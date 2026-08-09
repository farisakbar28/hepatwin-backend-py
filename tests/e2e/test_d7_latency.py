"""F8 -- Test suite latensi & konkurensi (D7). Lewat `client` fixture
(tests/conftest.py) -- proses test sudah "warm" (pytest sudah menjalankan
banyak test lain sebelumnya di sesi yang sama), sehingga TIDAK mengukur cold
start (lihat scripts/benchmark_cold_start.py utk itu) -- test ini murni
menjaga DoD p95 warm end-to-end < 5 detik sbg regression guard di CI.
"""
import asyncio
import time

import numpy as np

# 15 senyawa dari fixture conftest.py (ID kurasi Supabase asli -- cukup utk
# regression guard CI yang cepat; benchmark menyeluruh 50 senyawa asli ada di
# scripts/benchmark_simulation.py).
SAMPLE_IDS = [
    "HT0012", "HT0611", "HT0066", "HT0647", "HT0695",
    "HT1291", "HT0977", "HT0190", "HT0112", "HT0664",
    "HT1072", "HT0868", "HT0393", "HT0775", "HT0444",
]


def test_p95_latency_under_5_seconds(client):
    """Test #11 (F8): p95 end-to-end (HTTP penuh) < 5 detik (DoD D7)."""
    payload_template = {
        "dosis_mg": 500.0,
        "covariates": {"usia": 35, "jenis_kelamin": "L", "berat_badan_kg": 70.0, "tinggi_badan_cm": 170.0},
    }
    durations_ms = []
    for hid in SAMPLE_IDS:
        t0 = time.perf_counter()
        resp = client.post("/api/v1/simulate", json={**payload_template, "hepatwin_id": hid})
        durations_ms.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200

    p95 = float(np.percentile(durations_ms, 95))
    assert p95 < 5000.0, f"p95={p95:.0f}ms melebihi anggaran 5000ms PRD UC-02"


def test_concurrent_requests_are_thread_safe():
    """Test #12 (F8): 20 permintaan konkuren, senyawa & kovariat identik ->
    hasil identik (dili_score, cmax/auc, warna) -- verifikasi thread-safety
    model PyTorch dibagi antar-thread executor (F6). Dijalankan sinkron
    (asyncio.run) supaya tidak menambah dependensi plugin pytest-asyncio/anyio
    yang belum dipakai di test suite ini."""
    from app.core.database import SessionLocal
    from app.models.schemas import PatientCovariates, SimulationRequest
    from app.services.simulation_orchestrator import SimulationOrchestrator

    orchestrator = SimulationOrchestrator()

    async def one():
        db = SessionLocal()
        try:
            req = SimulationRequest(
                hepatwin_id="HT0012", dosis_mg=1000.0,
                covariates=PatientCovariates(usia=40, jenis_kelamin="L", berat_badan_kg=70.0, tinggi_badan_cm=170.0),
            )
            res = await orchestrator.handle_simulation(req, db)
            return (res.dili_score, round(res.cmax_hati, 6), round(res.auc_hati, 6), res.visual_color, res.risk_level)
        finally:
            db.close()

    async def run_all():
        return await asyncio.gather(*[one() for _ in range(20)])

    results = asyncio.run(run_all())
    unique_results = set(results)
    assert len(unique_results) == 1, f"Hasil konkuren TIDAK identik: {unique_results}"
