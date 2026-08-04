import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

@pytest.fixture(scope="module")
def api_url():
    assert SUPABASE_URL, "SUPABASE_URL tidak ditemukan di .env"
    return f"{SUPABASE_URL}/rest/v1/hepatwin_compounds"

def get_headers(api_key):
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

class TestRLSAnon:
    """Pengujian RLS untuk role anon (Publik / Frontend)"""
    
    def test_anon_can_select(self, api_url):
        headers = get_headers(SUPABASE_ANON_KEY)
        response = requests.get(f"{api_url}?select=*", headers=headers, params={"limit": 1})
        assert response.status_code == 200, f"Anon seharusnya bisa SELECT, tapi mendapat {response.status_code}"
    
    def test_anon_cannot_insert(self, api_url):
        headers = get_headers(SUPABASE_ANON_KEY)
        payload = {"hepatwin_id": "test_insert_anon", "compound_name": "Test"}
        response = requests.post(api_url, headers=headers, json=payload)
        # RLS biasanya menolak dengan 401, 403, atau 404
        assert response.status_code in [401, 403, 404], f"Anon seharusnya DITOLAK saat INSERT, status {response.status_code}"

    def test_anon_cannot_update(self, api_url):
        headers = get_headers(SUPABASE_ANON_KEY)
        headers["Prefer"] = "return=representation"
        payload = {"compound_name": "Test Update"}
        response = requests.patch(f"{api_url}?hepatwin_id=eq.unauthorized_test_id", headers=headers, json=payload)
        # Pada PostgREST, RLS yang menolak UPDATE untuk anon akan menghasilkan status 401/403/404 ATAU 200/204 dengan 0 baris terpengaruh ([])
        if response.status_code in [200, 204]:
            data = response.json() if response.content else []
            assert len(data) == 0, f"Anon seharusnya TIDAK BISA memodifikasi data, tapi memodifikasi {len(data)} baris"
        else:
            assert response.status_code in [401, 403, 404], f"Status tidak diharapkan: {response.status_code}"

    def test_anon_cannot_delete(self, api_url):
        headers = get_headers(SUPABASE_ANON_KEY)
        headers["Prefer"] = "return=representation"
        response = requests.delete(f"{api_url}?hepatwin_id=eq.unauthorized_test_id", headers=headers)
        # Pada PostgREST, RLS yang menolak DELETE untuk anon akan menghasilkan status 401/403/404 ATAU 200/204 dengan 0 baris terpengaruh ([])
        if response.status_code in [200, 204]:
            data = response.json() if response.content else []
            assert len(data) == 0, f"Anon seharusnya TIDAK BISA menghapus data, tapi menghapus {len(data)} baris"
        else:
            assert response.status_code in [401, 403, 404], f"Status tidak diharapkan: {response.status_code}"

class TestRLSServiceRole:
    """Pengujian RLS untuk role service_role (Backend Internal)"""
    
    def test_service_role_can_select(self, api_url):
        headers = get_headers(SUPABASE_SERVICE_ROLE_KEY)
        response = requests.get(f"{api_url}?select=*", headers=headers, params={"limit": 1})
        assert response.status_code == 200, f"Service Role seharusnya bisa SELECT, status {response.status_code}"
        
    def test_service_role_can_crud_flow(self, api_url):
        headers = get_headers(SUPABASE_SERVICE_ROLE_KEY)
        test_id = "test_sr_crud_flow"
        
        # INSERT
        payload = {"hepatwin_id": test_id, "compound_name": "sr_test"}
        response = requests.post(api_url, headers=headers, json=payload)
        assert response.status_code in [200, 201, 204], f"Service Role gagal INSERT, status {response.status_code}"
        
        # UPDATE
        update_payload = {"compound_name": "sr_test_updated"}
        response = requests.patch(f"{api_url}?hepatwin_id=eq.{test_id}", headers=headers, json=update_payload)
        assert response.status_code in [200, 204], f"Service Role gagal UPDATE, status {response.status_code}"
        
        # DELETE
        response = requests.delete(f"{api_url}?hepatwin_id=eq.{test_id}", headers=headers)
        assert response.status_code in [200, 204], f"Service Role gagal DELETE, status {response.status_code}"
