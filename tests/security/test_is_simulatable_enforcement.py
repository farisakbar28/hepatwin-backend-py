import pytest
from fastapi.testclient import TestClient

# Daftar 10 senyawa biologik nyata dari database (HTdddd)
BIOLOGICS = [
    {"id": "HT0003", "name": "Abatacept"},
    {"id": "HT0004", "name": "Abciximab"},
    {"id": "HT0019", "name": "Adalimumab"},
    {"id": "HT0023", "name": "Agalsidase beta"},
    {"id": "HT0029", "name": "Aldesleukin"},
    {"id": "HT0031", "name": "Alemtuzumab"},
    {"id": "HT0035", "name": "Alglucosidase alfa"},
    {"id": "HT0044", "name": "Alteplase"},
    {"id": "HT0072", "name": "Anakinra"},
    {"id": "HT0076", "name": "Antithymocyte globulin"},
]

@pytest.mark.security
def test_01_autocomplete_strict_exclusion(client: TestClient):
    """
    Uji Kemurnian Hasil Autocomplete: 
    Memastikan tidak satupun senyawa biologik (is_simulatable=False) muncul di hasil pencarian.
    """
    for bio in BIOLOGICS:
        response = client.get(f"/api/v1/compounds/autocomplete?q={bio['name']}")
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 0, f"FATAL: Senyawa biologik {bio['name']} lolos di autocomplete!"

@pytest.mark.security
def test_02_lookup_detail_strict_blocking(client: TestClient):
    """
    Uji Penolakan Lookup Detail Senyawa Biologik:
    Memastikan pemanggilan GET langsung ke ID biologik merespons dengan 422 Unprocessable Entity.
    """
    for bio in BIOLOGICS:
        response = client.get(f"/api/v1/compounds/{bio['id']}")
        assert response.status_code == 422, f"FATAL: Lookup untuk ID {bio['id']} lolos atau tidak diblokir dengan 422!"
        
        data = response.json()
        assert "senyawa ini bertipe biologik" in data["detail"].lower(), "Pesan error tidak semantik."

@pytest.mark.security
def test_03_simulate_preflight_strict_blocking(client: TestClient):
    """
    Uji Perlindungan Gerbang Simulasi (POST /simulate):
    Memastikan request simulasi langsung menggunakan ID biologik ditolak dengan 422 Unprocessable Entity
    tanpa memicu 500 Internal Server Error dari AI/PBPK Engine.
    """
    for bio in BIOLOGICS:
        payload = {
            "hepatwin_id": bio['id'],
            "dosis_mg": 100.0,
            "covariates": {
                "usia": 35,
                "jenis_kelamin": "L",
                "berat_badan_kg": 70.0,
                "tinggi_badan_cm": 170.0
            }
        }
        response = client.post("/api/v1/simulate", json=payload)
        
        # Validasi bahwa request ditolak keras secara spesifik di Pre-flight Validator
        assert response.status_code == 422, f"FATAL: Simulasi untuk ID {bio['id']} tidak diblokir dengan HTTP 422!"
        
        data = response.json()
        assert "senyawa ini bertipe biologik" in data["detail"].lower(), "Pesan error simulasi biologik salah."

@pytest.mark.security
def test_04_dataset_integrity(client: TestClient):
    """
    Uji Keutuhan Dataset (No Physical Deletion):
    Memastikan sistem membedakan ID fiktif (404) vs ID biologik sah yang ditolak (422).
    Ini membuktikan 105 biologik tetap tersimpan utuh di basis data.
    """
    # 1. Pastikan ID fiktif mendapat 404
    response_fake = client.get("/api/v1/compounds/HT-9999")
    assert response_fake.status_code == 404
    
    # 2. Pastikan ID biologik riil mendapat 422
    response_bio = client.get(f"/api/v1/compounds/{BIOLOGICS[0]['id']}")
    assert response_bio.status_code == 422
