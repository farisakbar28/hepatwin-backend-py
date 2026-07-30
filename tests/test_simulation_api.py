"""TU.14 -- Test integrasi endpoint /simulate & /health.

Acceptance criteria UPSCALE.md TU.14:
- endpoint balas 503 (bukan 200 skor 0.5) saat artefak model tidak ada
- tidak ada string exception mentah di response body
- response berisi field model_version/model_status/score_is_calibrated/internal_cv_auc
"""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

MODEL_PATH = Path("app/models/model_arm_a.pt")
BACKUP_PATH = Path("app/models/model_arm_a.pt.testbak")


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint_reports_ai_ready(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["ai_engine_ready"] is True


def test_simulate_triase_umum_returns_new_fields(client):
    resp = client.post(
        "/api/v1/simulate",
        json={"mode": "triase_umum", "smiles_string": "CC(=O)Nc1ccc(O)cc1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["DILI_score"] <= 1.0
    assert body["model_status"] == "ready"
    assert body["score_is_calibrated"] is True
    assert body["model_version"] == "gatnn-dnn-arm-a-v1"
    assert body["internal_cv_auc"] == pytest.approx(0.7385)


def test_simulate_invalid_smiles_returns_400(client):
    resp = client.post("/api/v1/simulate", json={"mode": "triase_umum", "smiles_string": "not_a_smiles!!!"})
    assert resp.status_code == 400


def test_simulate_returns_503_not_default_score_when_model_artifact_missing():
    """Kriteria akseptansi eksplisit UPSCALE.md TU.14: hapus file model ->
    503, BUKAN 200 dengan skor 0.5 (larangan silent fallback)."""
    MODEL_PATH.rename(BACKUP_PATH)
    try:
        # import ulang app supaya orchestrator singleton dibuat ulang tanpa model
        import importlib

        import app.api.dependencies as deps_module
        import app.main as main_module

        importlib.reload(deps_module)
        importlib.reload(main_module)
        fresh_client = TestClient(main_module.app)

        resp = fresh_client.post(
            "/api/v1/simulate",
            json={"mode": "triase_umum", "smiles_string": "CC(=O)Nc1ccc(O)cc1"},
        )
        assert resp.status_code == 503
        body = resp.json()
        assert body != {"DILI_score": 0.5}
    finally:
        BACKUP_PATH.rename(MODEL_PATH)
        import importlib

        import app.api.dependencies as deps_module
        import app.main as main_module

        importlib.reload(deps_module)
        importlib.reload(main_module)


def test_global_exception_handler_does_not_leak_raw_error(monkeypatch):
    """UPSCALE.md TU.14: 'Tidak ada string exception mentah di response body'.

    raise_server_exceptions=False supaya TestClient meniru perilaku server
    sungguhan (lewat global_exception_handler), bukan langsung re-raise ke
    proses test seperti default TestClient."""
    from app.services import simulation_orchestrator

    def _boom(self, req):
        raise RuntimeError("SECRET_INTERNAL_PATH_C:/Users/vedoputra/private/leak")

    monkeypatch.setattr(simulation_orchestrator.SimulationOrchestrator, "handle_request", _boom)

    no_raise_client = TestClient(app, raise_server_exceptions=False)
    resp = no_raise_client.post("/api/v1/simulate", json={"mode": "triase_umum", "smiles_string": "CCO"})
    assert resp.status_code == 500
    assert "SECRET_INTERNAL_PATH" not in resp.text
    assert resp.json() == {"detail": "Internal Server Error"}
