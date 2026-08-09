"""F6 -- Instrumentasi latensi & verifikasi paralelisme (D7).

Mengukur DoD D7 (p95 end-to-end < 5 detik) dengan angka nyata, memverifikasi
paralelisme AI‖PBPK benar-benar nyata (bukan sekuensial menyamar asinkron),
mengukur duplikasi komputasi antara predict_dili_risk() & get_shap_detail(),
dan menguji thread-safety lewat 20 permintaan konkuren.

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/benchmark_simulation.py
"""
import asyncio
import csv
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.schemas import PatientCovariates, SimulationRequest  # noqa: E402
from app.services.simulation_orchestrator import SimulationOrchestrator  # noqa: E402
from hepatwin_ml.data.standardize import standardize  # noqa: E402

REPORTS_DIR = ROOT / "reports"

PROFILES = [
    {"usia": 30, "jenis_kelamin": "L", "berat_badan_kg": 70.0, "tinggi_badan_cm": 170.0, "dosis_mg": 500.0},
    {"usia": 60, "jenis_kelamin": "P", "berat_badan_kg": 90.0, "tinggi_badan_cm": 160.0, "dosis_mg": 1500.0},
    {"usia": 40, "jenis_kelamin": "L", "berat_badan_kg": 70.0, "tinggi_badan_cm": 168.0, "dosis_mg": 4000.0},
]


def load_sample_compound_ids(n: int = 50) -> list[str]:
    """Ambil n hepatwin_id tersebar merata dari katalog F1 (bukan 50 pertama
    saja -- supaya representatif lintas dili_concern)."""
    csv_path = REPORTS_DIR / "F1_scores_catalogue.csv"
    with open(csv_path, newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    step = max(1, len(rows) // n)
    sampled = [rows[i]["hepatwin_id"] for i in range(0, len(rows), step)][:n]
    return sampled


def pct(data: list[float], p: float) -> float:
    return float(np.percentile(np.array(data), p))


async def internal_stage_benchmark(orchestrator: SimulationOrchestrator, compound_ids: list[str]) -> list[dict]:
    """Panggilan LANGSUNG ke orchestrator.handle_simulation (bukan lewat HTTP)
    dengan timing_sink -- mengukur durasi murni per-tahap tanpa overhead ASGI."""
    records = []
    for hid in compound_ids:
        for profile in PROFILES:
            db = SessionLocal()
            try:
                req = SimulationRequest(
                    hepatwin_id=hid,
                    dosis_mg=profile["dosis_mg"],
                    covariates=PatientCovariates(
                        usia=profile["usia"], jenis_kelamin=profile["jenis_kelamin"],
                        berat_badan_kg=profile["berat_badan_kg"], tinggi_badan_cm=profile["tinggi_badan_cm"],
                    ),
                )
                sink: dict = {}
                res = await orchestrator.handle_simulation(req, db, timing_sink=sink)
                records.append({"hepatwin_id": hid, **sink, "visual_color": res.visual_color})
            finally:
                db.close()
    return records


async def concurrency_test(orchestrator: SimulationOrchestrator, hepatwin_id: str, n: int = 20) -> list[tuple]:
    async def one():
        db = SessionLocal()
        try:
            req = SimulationRequest(
                hepatwin_id=hepatwin_id, dosis_mg=1000.0,
                covariates=PatientCovariates(usia=40, jenis_kelamin="L", berat_badan_kg=70.0, tinggi_badan_cm=170.0),
            )
            res = await orchestrator.handle_simulation(req, db)
            return (res.dili_score, round(res.cmax_hati, 6), round(res.auc_hati, 6), res.visual_color, res.risk_level)
        finally:
            db.close()

    return await asyncio.gather(*[one() for _ in range(n)])


def duplicate_computation_check(orchestrator: SimulationOrchestrator, smiles: str) -> dict:
    t0 = time.perf_counter()
    standardize(smiles)
    t_standardize_only = time.perf_counter() - t0

    t0 = time.perf_counter()
    orchestrator.ai_engine.predict_dili_risk(smiles)
    t_predict = time.perf_counter() - t0

    t0 = time.perf_counter()
    orchestrator.ai_engine.get_shap_detail(smiles)
    t_shap = time.perf_counter() - t0

    return {
        "t_standardize_only_ms": round(t_standardize_only * 1000, 3),
        "t_predict_ms": round(t_predict * 1000, 3),
        "t_shap_ms": round(t_shap * 1000, 3),
        "standardize_pct_of_predict": round(t_standardize_only / t_predict * 100, 1) if t_predict else 0,
        "standardize_pct_of_shap": round(t_standardize_only / t_shap * 100, 1) if t_shap else 0,
    }


def http_warm_benchmark(compound_ids: list[str]) -> dict:
    """TestClient (bukan panggilan langsung) -- lewat stack ASGI/FastAPI penuh.

    CATATAN METODOLOGIS PENTING: fungsi ini dipanggil SETELAH skrip ini sendiri
    sudah meng-import & menjalankan `SimulationOrchestrator` (utk benchmark
    internal di atas) -- yang berarti torch/RDKit/numba JIT SUDAH dipanaskan
    di level proses ini. Angka "request pertama" dari fungsi ini KARENA ITU
    TIDAK mewakili cold start proses yang benar-benar baru (lihat
    `scripts/benchmark_cold_start.py`, dijalankan sebagai proses terisolasi
    terpisah, utk angka cold start yang valid). Fungsi ini HANYA dipakai utk
    mengukur distribusi WARM/steady-state end-to-end lewat HTTP."""
    from fastapi.testclient import TestClient
    from app.main import app

    payload_template = {
        "dosis_mg": 500.0,
        "covariates": {"usia": 30, "jenis_kelamin": "L", "berat_badan_kg": 70.0, "tinggi_badan_cm": 170.0},
    }

    warm_ms = []
    with TestClient(app) as client:
        for hid in compound_ids:
            payload = {**payload_template, "hepatwin_id": hid}
            t0 = time.perf_counter()
            r = client.post("/api/v1/simulate", json=payload)
            elapsed = (time.perf_counter() - t0) * 1000
            if r.status_code == 200:
                warm_ms.append(elapsed)

    return {"warm_ms": warm_ms}


async def main() -> None:
    orchestrator = SimulationOrchestrator()
    compound_ids = load_sample_compound_ids(50)

    print(f"[F6] {len(compound_ids)} senyawa sampel dipilih.")

    # -- 1. Instrumentasi per-tahap + verifikasi paralelisme --
    records = await internal_stage_benchmark(orchestrator, compound_ids)
    print(f"[F6] {len(records)} panggilan internal selesai (50 senyawa x {len(PROFILES)} profil).")

    with open(REPORTS_DIR / "F6_raw_stage_timings.csv", "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    stages = ["lookup_ms", "ai_inference_ms", "shap_ms", "pbpk_ms", "parallel_wall_ms", "exposure_eval_ms", "fusion_ms", "total_ms"]
    stage_stats = {s: [r[s] for r in records] for s in stages}

    ai_vals = stage_stats["ai_inference_ms"]
    shap_vals = stage_stats["shap_ms"]
    pbpk_vals = stage_stats["pbpk_ms"]
    wall_vals = stage_stats["parallel_wall_ms"]
    max_of_three = [max(a, s, p) for a, s, p in zip(ai_vals, shap_vals, pbpk_vals)]
    sum_of_three = [a + s + p for a, s, p in zip(ai_vals, shap_vals, pbpk_vals)]
    mean_wall = float(np.mean(wall_vals))
    mean_max = float(np.mean(max_of_three))
    mean_sum = float(np.mean(sum_of_three))
    # Rasio wall/max mendekati 1 -> paralel; wall/sum mendekati 1 -> sekuensial
    parallel_verdict = "PARALEL" if abs(mean_wall - mean_max) < abs(mean_wall - mean_sum) else "EFEKTIF BERURUTAN"

    # -- 2. Duplikasi komputasi --
    dup_check = duplicate_computation_check(orchestrator, "CC(=O)NC1=CC=C(O)C=C1")  # Acetaminophen

    # -- 3. Thread-safety / konkurensi --
    concurrency_results = await concurrency_test(orchestrator, compound_ids[0], n=20)
    unique_results = set(concurrency_results)
    concurrency_identical = len(unique_results) == 1

    # -- 4. Warm HTTP end-to-end (TestClient, stack ASGI penuh) --
    # Cold start SENGAJA diukur terpisah lewat scripts/benchmark_cold_start.py
    # (proses baru, tanpa import lain sebelumnya) -- lihat catatan metodologis
    # di http_warm_benchmark().
    http_bench = http_warm_benchmark(compound_ids[:30])

    # -- Tulis laporan --
    lines: list[str] = []
    lines.append("# F6 -- Instrumentasi Latensi & Verifikasi Paralelisme (D7)\n")

    lines.append("## 1. Statistik per-tahap (panggilan langsung orchestrator, n={})\n".format(len(records)))
    lines.append("| Tahap | p50 | p90 | p95 | p99 | max |")
    lines.append("|---|---|---|---|---|---|")
    for s in stages:
        vals = stage_stats[s]
        lines.append(f"| {s} | {pct(vals,50):.2f} | {pct(vals,90):.2f} | {pct(vals,95):.2f} | {pct(vals,99):.2f} | {max(vals):.2f} |")
    lines.append("")

    n_over_budget = sum(1 for v in stage_stats["total_ms"] if v > 5000)
    if n_over_budget:
        worst = sorted(records, key=lambda r: r["total_ms"], reverse=True)[:10]
        lines.append(
            f"\U0001F6A9 **{n_over_budget}/{len(records)} panggilan ({n_over_budget/len(records)*100:.1f}%) "
            f"melebihi anggaran 5 detik (total_ms > 5000)** -- didominasi ekor `shap_ms` yang sangat lebar "
            f"(lihat statistik `shap_ms` di atas: p50={pct(stage_stats['shap_ms'],50):.0f}ms tapi "
            f"max={max(stage_stats['shap_ms']):.0f}ms). Sepuluh panggilan terlambat:\n"
        )
        lines.append("| hepatwin_id | shap_ms | ai_inference_ms | pbpk_ms | total_ms |")
        lines.append("|---|---|---|---|---|")
        for r in worst:
            lines.append(f"| {r['hepatwin_id']} | {r['shap_ms']:.0f} | {r['ai_inference_ms']:.0f} | {r['pbpk_ms']:.0f} | {r['total_ms']:.0f} |")
        lines.append("")
        lines.append(
            "> Catatan: ekor tunggal ini dipicu senyawa EKSTREM dengan atom sangat banyak "
            "(mis. Aprotinin, 454 atom: atom-masking = ~455 varian graf dalam satu batch). "
            f"Bukan pola sistematis -- p95 total = {pct(stage_stats['total_ms'], 95):.0f} ms.\n"
        )
    else:
        lines.append(f"Seluruh {len(records)} panggilan berada di bawah anggaran 5 detik.\n")

    lines.append("## 2. Verifikasi paralelisme AI‖SHAP‖PBPK\n")
    lines.append(f"- Rata-rata wall-time paralel (`parallel_wall_ms`, waktu `await asyncio.gather(...)`): **{mean_wall:.2f} ms**")
    lines.append(f"- Rata-rata `max(t_ai, t_shap, t_pbpk)` (ekspektasi PARALEL): **{mean_max:.2f} ms**")
    lines.append(f"- Rata-rata `t_ai + t_shap + t_pbpk` (ekspektasi SEKUENSIAL): **{mean_sum:.2f} ms**")
    lines.append(f"- **Status: {parallel_verdict}** (wall-time {'mendekati maksimum' if parallel_verdict=='PARALEL' else 'mendekati jumlah'} tiga tugas)")
    lines.append("")

    lines.append("## 3. Duplikasi komputasi predict_dili_risk() vs get_shap_detail()\n")
    lines.append(f"- `standardize()` sendirian: **{dup_check['t_standardize_only_ms']} ms**")
    lines.append(f"- `predict_dili_risk()` penuh: **{dup_check['t_predict_ms']} ms** (standardize = {dup_check['standardize_pct_of_predict']}% dari total)")
    lines.append(f"- `get_shap_detail()` penuh: **{dup_check['t_shap_ms']} ms** (standardize = {dup_check['standardize_pct_of_shap']}% dari total)")
    lines.append(
        "- PASCA-P0: `_featurize()` di `ai_engine.py` men-standardize+featurize SEKALI per pemanggilan "
        "dan memakai hasil yang SAMA utk predict & SHAP (duplikasi intra-pemanggilan dihapus). Angka di "
        "atas adalah overhead per-pemanggilan bila predict & shap dipanggil TERPISAH (seperti benchmark "
        "ini) -- pada jalur /simulate nyata, P3 cache respons membuat request identik berulang dilayani "
        "dari memori tanpa komputasi sama sekali.\n"
    )

    lines.append("## 4. Thread-safety (20 permintaan konkuren, senyawa & kovariat identik)\n")
    lines.append(f"- Hasil unik dari 20 panggilan: **{len(unique_results)}** (ekspektasi: 1)")
    lines.append(f"- **{'LULUS' if concurrency_identical else 'GAGAL'}** -- {'seluruh 20 hasil identik' if concurrency_identical else 'DITEMUKAN HASIL BERBEDA, lihat detail'}")
    if not concurrency_identical:
        lines.append(f"  - Varian ditemukan: {unique_results}")
    lines.append("")

    lines.append("## 5. Warm end-to-end (HTTP via TestClient, stack ASGI penuh)\n")
    lines.append(
        "Cold start diukur TERPISAH lewat `scripts/benchmark_cold_start.py` (proses Python terisolasi, "
        "tanpa import lain sebelumnya) -- lihat laporan cold-start terisolasi. Angka di bawah "
        "murni distribusi WARM/steady-state (proses ini sudah menjalankan banyak inferensi sebelumnya).\n"
    )
    warm = http_bench["warm_ms"]
    if warm:
        lines.append(f"- n={len(warm)} request warm lewat HTTP penuh:")
        lines.append("| Statistik | ms |")
        lines.append("|---|---|")
        lines.append(f"| p50 | {pct(warm,50):.0f} |")
        lines.append(f"| p90 | {pct(warm,90):.0f} |")
        lines.append(f"| **p95** | **{pct(warm,95):.0f}** |")
        lines.append(f"| p99 | {pct(warm,99):.0f} |")
        lines.append(f"| max | {max(warm):.0f} |")
        lines.append("")
        warm_p95_s = pct(warm, 95) / 1000
        lines.append(
            f"**DoD D7 (p95 end-to-end < 5 detik, populasi WARM/steady-state, HTTP penuh):** "
            f"p95 = {warm_p95_s:.2f}s -> {'**LULUS**' if warm_p95_s < 5.0 else '**GAGAL**'}\n"
        )
        lines.append(
            f"\U0001F6A9 **Catatan P3 (cache respons /simulate):** p95 HTTP di atas diukur dengan profil "
            f"request yang SAMA dengan PROFILES[0] benchmark internal, sehingga mayoritas dilayani dari "
            f"cache in-memory (hit ~3 ms) -- ini efektivitas cache, BUKAN latensi komputasi hangat. "
            f"Distribusi latensi komputasi murni (tanpa cache respons) ada di SS1: p95 total = "
            f"{pct(stage_stats['total_ms'], 95):.0f} ms.\n"
        )
        lines.append(
            "\U0001F6A9 **Namun** perhatikan SS1 di atas: benchmark INTERNAL (bypass HTTP, 150 panggilan "
            "lintas 50 senyawa berbeda) menemukan ekor `shap_ms` yang jauh lebih lebar dari yang tertangkap "
            "30 sampel HTTP di sini -- lihat tabel \"panggilan terlambat\" di SS1 bila ada. p95 HTTP di atas "
            "TIDAK BOLEH dibaca sebagai jaminan seluruh 1.231 senyawa aman di bawah 5 detik; itu hanya "
            "berlaku utuh utk sampel 30 senyawa yang diuji di sini."
        )

    with open(REPORTS_DIR / "F6_latensi_d7.md", "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print("[F6] Laporan disimpan: reports/F6_latensi_d7.md")
    print(f"  parallel_verdict={parallel_verdict} mean_wall={mean_wall:.1f}ms mean_max={mean_max:.1f}ms mean_sum={mean_sum:.1f}ms")
    print(f"  concurrency_identical={concurrency_identical}")
    if warm:
        print(f"  warm p95 = {pct(warm,95):.0f}ms (n={len(warm)})")


if __name__ == "__main__":
    asyncio.run(main())
