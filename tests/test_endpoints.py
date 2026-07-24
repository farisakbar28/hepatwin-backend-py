"""Test integrasi endpoint via FastAPI TestClient.

Menutup gap fondasi: sebelum ini hanya ada unit test chem + test kontrak triase,
tidak ada test yang benar-benar memanggil endpoint HTTP. Test ini memverifikasi
seluruh siklus request/response yang akan dipakai frontend.

Dasar: PRD §7.1 · Arsitektur §E.1 · EXECUTION_PLAN.md T6.5 (subset e2e).
"""
import warnings

import pytest

warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

# SMILES ≥ 5 atom berat (lolos kelayakan). Paracetamol = 11 atom berat.
PARACETAMOL = "CC(=O)NC1=CC=C(O)C=C1"


# ---------------------------------------------------------------- /health
def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # Harus membedakan "server nyala" vs "bobot terlatih dimuat" (audit F1, §3.10)
    assert "ai_engine_ready" in body
    assert "ai_weights_loaded" in body
    assert "pkpd_engine_ready" in body


# ------------------------------------------------------------- /compounds
def test_compounds_returns_two_flagship():
    r = client.get("/api/v1/compounds")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    ids = {c["id"] for c in data}
    assert ids == {"paracetamol", "amox_clav"}
    for c in data:
        assert "display_name" in c and "mechanism_type" in c


# ------------------------------------------------------------ /model-info
def test_model_info_metrics_null_after_reseal():
    """Setelah re-seal, metrics HARUS null (PRD §8.3 / §3.3: jangan sajikan
    angka target/karangan sebagai hasil; null bila belum divalidasi resmi)."""
    r = client.get("/api/v1/model-info")
    assert r.status_code == 200
    body = r.json()
    assert body["metrics"] is None
    assert "model_version" in body and "backend" in body


# -------------------------------------------------------- /validate-smiles
def test_validate_smiles_valid():
    r = client.post("/api/v1/validate-smiles", json={"smiles": PARACETAMOL})
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["canonical_smiles"] is not None
    assert body["error_code"] is None


def test_validate_smiles_invalid():
    r = client.post("/api/v1/validate-smiles", json={"smiles": "bukan$$$smiles"})
    assert r.status_code == 200
    assert r.json()["valid"] is False
    assert r.json()["error_code"] == "E_SMILES_INVALID"


def test_validate_smiles_inorganic():
    # Tetraethyllead: mengandung Pb (di luar himpunan organik)
    r = client.post("/api/v1/validate-smiles", json={"smiles": "CC[Pb](CC)(CC)CC"})
    assert r.status_code == 200
    assert r.json()["valid"] is False
    assert r.json()["error_code"] == "E_INORGANIC"


def test_validate_smiles_too_small():
    # Etanol: 3 atom berat (< 5) → di luar cakupan model
    r = client.post("/api/v1/validate-smiles", json={"smiles": "CCO"})
    assert r.status_code == 200
    assert r.json()["valid"] is False
    assert r.json()["error_code"] == "E_MOL_TOO_LARGE"


# ------------------------------------------------------------- /simulate
def test_simulate_triase_valid():
    r = client.post(
        "/api/v1/simulate",
        json={"mode": "triase_umum", "smiles_string": PARACETAMOL},
    )
    assert r.status_code == 200
    body = r.json()
    # Kontrak scope PRD §4.2: triase SELALU heatmap_generik
    assert body["visual_pattern"] == "heatmap_generik"
    assert 0.0 <= body["DILI_score"] <= 1.0
    assert body["model_status"] in ("trained", "untrained_random_weights", "mock")
    assert body["disclaimer_hideable"] is False  # disclaimer triase tak bisa disembunyikan
    assert isinstance(body["model_limitations"], list)


def test_simulate_triase_invalid_smiles_returns_422():
    r = client.post(
        "/api/v1/simulate",
        json={"mode": "triase_umum", "smiles_string": "zzz$$$"},
    )
    assert r.status_code == 422
    assert r.json()["code"] == "E_SMILES_INVALID"


def test_simulate_triase_missing_smiles_returns_422():
    r = client.post("/api/v1/simulate", json={"mode": "triase_umum"})
    assert r.status_code == 422
    assert r.json()["code"] == "E_REQUEST_INCOMPLETE"


def test_simulate_edukasi_amox_clav_works():
    """Amox-clav digerakkan skor AI (Mesin B), tidak butuh Mesin A → berfungsi."""
    r = client.post(
        "/api/v1/simulate",
        json={"mode": "edukasi_mendalam", "compound_id": "amox_clav", "dose_mg_kg": 15},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["compound_class"] == "idiosyncratic"
    assert body["visual_pattern"] == "portal_inflammation"
    assert 0.0 <= body["DILI_score"] <= 1.0


def test_simulate_edukasi_paracetamol_gated_returns_503():
    """Mesin A parasetamol digembok (konstanta PD belum divalidasi Farmasi).
    Harus gagal RAPI dengan E_MODEL_UNAVAILABLE (503), BUKAN 500 generik."""
    r = client.post(
        "/api/v1/simulate",
        json={"mode": "edukasi_mendalam", "compound_id": "paracetamol", "dose_mg_kg": 15},
    )
    assert r.status_code == 503
    assert r.json()["code"] == "E_MODEL_UNAVAILABLE"


def test_simulate_edukasi_invalid_compound_returns_422():
    r = client.post(
        "/api/v1/simulate",
        json={"mode": "edukasi_mendalam", "compound_id": "aspirin"},
    )
    # compound_id di luar Literal → validasi Pydantic (422)
    assert r.status_code == 422


@pytest.mark.parametrize(
    "smiles",
    ["CC(=O)Nc1ccc(O)cc1", "c1ccccc1", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "O=C(O)c1ccccc1"],
)
def test_simulate_triase_always_heatmap_generik(smiles):
    """Penjaga scope tambahan lewat jalur HTTP (bukan hanya orchestrator langsung)."""
    r = client.post(
        "/api/v1/simulate", json={"mode": "triase_umum", "smiles_string": smiles}
    )
    assert r.status_code == 200
    assert r.json()["visual_pattern"] == "heatmap_generik"
