"""P3 -- Cache in-memory respons penuh /simulate.

Unit: builder kunci (dosis, kovariat, dan fingerprint data senyawa masuk ke
kunci) + perilaku bounded/clear. E2E (fixture `client`, model AI asli): dua
request identik -> komputasi hanya SEKALI (predict_dili_risk di-count) &
respons identik; request dengan dosis berbeda -> kunci berbeda -> hitung
ulang (cache tidak pernah melayani respons untuk input yang berbeda).
"""
import pytest

from app.models.domain import HepatwinCompound
from app.models.schemas import PatientCovariates, SimulationRequest
from app.services import simulation_cache as sc


def _req(hepatwin_id="HT0012", dosis=500.0, usia=35, jk="L", berat=70.0, tinggi=170.0):
    return SimulationRequest(
        hepatwin_id=hepatwin_id,
        dosis_mg=dosis,
        covariates=PatientCovariates(
            usia=usia, jenis_kelamin=jk, berat_badan_kg=berat, tinggi_badan_cm=tinggi
        ),
    )


def _compound(**overrides):
    base = dict(
        hepatwin_id="HT0012",
        compound_name="Acetaminophen",
        canonical_smiles="CC(=O)NC1=CC=C(C=C1)O",
        is_simulatable=True,
        xlogp=0.5,
        injury_pattern="Hepatoseluler",
        segment_list="V;VI;VII;VIII",
        hotspot_base_intensity="high",
        hotspot_display_mode="focal",
    )
    base.update(overrides)
    return HepatwinCompound(**base)


def test_key_termasuk_dosis_dan_kovariat():
    c = _compound()
    k1 = sc.build_simulation_cache_key(_req(dosis=500.0, usia=35, jk="L", berat=70.0, tinggi=170.0), c)
    k2 = sc.build_simulation_cache_key(_req(dosis=5000.0, usia=35, jk="L", berat=70.0, tinggi=170.0), c)
    k3 = sc.build_simulation_cache_key(_req(dosis=500.0, usia=60, jk="P", berat=90.0, tinggi=160.0), c)
    assert k1 != k2, "dosis berbeda harus menghasilkan kunci berbeda (PBPK diskalakan dosis)"
    assert k1 != k3, "kovariat berbeda harus menghasilkan kunci berbeda (penskalaan alometrik)"
    assert k2 != k3


def test_key_termasuk_fingerprint_data_senyawa():
    c1 = _compound(canonical_smiles="CC(=O)NC1=CC=C(C=C1)O", injury_pattern="Hepatoseluler")
    c2 = _compound(canonical_smiles="CC(=O)NC1=CC=C(C=C1)O", injury_pattern="Tidak Terklasifikasi")
    c3 = _compound(canonical_smiles="CCO", segment_list=None, hotspot_base_intensity=None)
    assert sc.build_simulation_cache_key(_req(), c1) != sc.build_simulation_cache_key(_req(), c2)
    assert sc.build_simulation_cache_key(_req(), c1) != sc.build_simulation_cache_key(_req(), c3)
    # Senyawa sama + input sama -> kunci stabil (deterministik)
    assert sc.build_simulation_cache_key(_req(), c1) == sc.build_simulation_cache_key(_req(), c1)


def test_get_put_clear():
    sc.clear_simulation_cache()
    key = sc.build_simulation_cache_key(_req(), _compound())
    assert sc.get_simulation_cached(key) is None
    sc.put_simulation_cached(key, {"dummy": "response"})
    assert sc.get_simulation_cached(key) == {"dummy": "response"}
    sc.clear_simulation_cache()
    assert sc.get_simulation_cached(key) is None


def test_clear_caches_hook_membuang_entri_cache():
    """Wiring invalidation: `CompoundRepository.clear_caches()` (hook seed
    ulang DB, dipanggil conftest) WAJIB membuang cache /simulate -- satu-satunya
    jalur pembuangan cache di produksi bila data senyawa berubah."""
    from app.repositories.compound_repository import clear_caches

    sc.clear_simulation_cache()
    key = sc.build_simulation_cache_key(_req(), _compound())
    sc.put_simulation_cached(key, {"dummy": "response"})
    assert sc.get_simulation_cached(key) == {"dummy": "response"}
    clear_caches()
    assert sc.get_simulation_cached(key) is None


def test_cache_bounded_evicts_oldest():
    sc.clear_simulation_cache()
    n = sc._SIMULATION_CACHE_MAXSIZE
    assert n > 0
    for i in range(n + 1):
        sc.put_simulation_cached(f"key-{i}", i)
    assert sc.simulation_cache_size() == n
    assert sc.get_simulation_cached("key-0") is None  # entri terlama ter-evict
    assert sc.get_simulation_cached(f"key-{n}") == n   # entri terbaru tetap ada
    sc.clear_simulation_cache()


@pytest.mark.e2e
def test_identical_requests_compute_once_and_cache_hit(client, monkeypatch):
    """Dua request identik -> predict_dili_risk hanya dipanggil SEKALI
    (bukti cache hit sungguhan, bukan sekadar output identik deterministik)."""
    sc.clear_simulation_cache()
    from app.services import ai_engine as ai_mod

    calls = {"n": 0}
    original = ai_mod.HybridAIEngine.predict_dili_risk

    def counting(self, smiles):
        calls["n"] += 1
        return original(self, smiles)

    monkeypatch.setattr(ai_mod.HybridAIEngine, "predict_dili_risk", counting)

    payload = {
        "hepatwin_id": "HT0012",
        "dosis_mg": 501.0,
        "covariates": {"usia": 33, "jenis_kelamin": "L", "berat_badan_kg": 71.0, "tinggi_badan_cm": 172.0},
    }
    r1 = client.post("/api/v1/simulate", json=payload)
    r2 = client.post("/api/v1/simulate", json=payload)
    assert r1.status_code == 200 and r2.status_code == 200
    assert calls["n"] == 1, f"predict_dili_risk dipanggil {calls['n']}x -- cache tidak hit!"

    d1, d2 = r1.json(), r2.json()
    for key in ("shap_detail", "timing_ms"):
        d1.pop(key, None)
        d2.pop(key, None)
    assert d1 == d2


@pytest.mark.e2e
def test_different_dose_bypasses_cache(client, monkeypatch):
    """Dosis berbeda -> kunci berbeda -> komputasi diulang & luaran PBPK
    berbeda (cache tidak pernah melayani respons utk input yang berbeda)."""
    sc.clear_simulation_cache()
    from app.services import ai_engine as ai_mod

    calls = {"n": 0}
    original = ai_mod.HybridAIEngine.predict_dili_risk

    def counting(self, smiles):
        calls["n"] += 1
        return original(self, smiles)

    monkeypatch.setattr(ai_mod.HybridAIEngine, "predict_dili_risk", counting)

    base = {
        "hepatwin_id": "HT0012",
        "covariates": {"usia": 33, "jenis_kelamin": "L", "berat_badan_kg": 71.0, "tinggi_badan_cm": 172.0},
    }
    r1 = client.post("/api/v1/simulate", json={**base, "dosis_mg": 501.0})
    r2 = client.post("/api/v1/simulate", json={**base, "dosis_mg": 2500.0})
    assert r1.status_code == 200 and r2.status_code == 200
    assert calls["n"] == 2
    assert r1.json()["cmax_liver_mg_l"] != r2.json()["cmax_liver_mg_l"]
