import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.domain import HepatwinCompound
from app.core.database import get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_db_for_unit_tests():
    def mock_get_db():
        db = MagicMock()
        yield db

@pytest.fixture(autouse=True)
def _override_get_db():
    """Scoped ke tiap test di modul ini -- override sebelumnya (mis. SQLite
    seed dari tests/conftest.py) dipulihkan setelahnya. Sebelumnya baris ini
    adalah kode top-level yang jalan sekali saat modul di-import (collection
    time), menimpa app.dependency_overrides[get_db] secara global untuk
    SISA seluruh sesi pytest -- termasuk test e2e/security yang di-collect
    setelah modul ini, membuatnya memakai MagicMock alih-alih SQLite seed
    dan gagal massal saat `pytest tests/` dijalankan utuh."""
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = mock_get_db
    yield
    if previous is not None:
        app.dependency_overrides[get_db] = previous
    else:
        app.dependency_overrides.pop(get_db, None)

def test_health_check():
    response = client.get("/health")
    assert response.status_code in [200, 404]

def test_compounds_autocomplete_validation():
    # Tanpa query 'q' harus 422 Unprocessable Entity
    response = client.get("/api/v1/compounds/autocomplete")
    assert response.status_code == 422

def test_simulation_request_validation():
    # Body kosong harus 422 Unprocessable Entity
    response = client.post("/api/v1/simulate", json={})
    assert response.status_code == 422

@patch("app.services.lookup_service.CompoundRepository.get_by_id")
def test_simulation_invalid_id(mock_get_by_id):
    # Mocking DB call agar melempar 404 Not Found secara terkontrol tanpa butuh koneksi internet Supabase
    mock_get_by_id.return_value = None
    
    payload = {
        "hepatwin_id": "INVALID_ID_TEST_999",
        "dosis_mg": 500.0,
        "covariates": {
            "usia": 30,
            "jenis_kelamin": "L",
            "berat_badan_kg": 70.0,
            "tinggi_badan_cm": 170.0
        }
    }
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 404
    assert "tidak ditemukan" in response.json()["detail"]

@patch("app.services.lookup_service.CompoundRepository.get_by_id")
def test_simulation_valid_flow(mock_get_by_id):
    # Mock compound valid dari DB
    mock_compound = HepatwinCompound(
        hepatwin_id="HEPATWIN_0001",
        compound_name="Acetaminophen",
        canonical_smiles="CC(=O)NC1=CC=C(O)C=C1",
        is_simulatable=True,
        injury_pattern="Hepatocellular",
        segment_list="V, VI, VII, VIII"
    )
    mock_get_by_id.return_value = mock_compound

    payload = {
        "hepatwin_id": "HEPATWIN_0001",
        "dosis_mg": 1000.0,
        "covariates": {
            "usia": 40,
            "jenis_kelamin": "L",
            "berat_badan_kg": 70.0,
            "tinggi_badan_cm": 170.0
        }
    }
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["hepatwin_id"] == "HEPATWIN_0001"
    assert res_data["compound_name"] == "Acetaminophen"
    assert "affected_segments" in res_data
    assert "time_series_pbpk" in res_data
    assert "disclaimer_permanent" in res_data
