import pytest
from fastapi.testclient import TestClient

@pytest.mark.e2e
@pytest.mark.parametrize("query", [
    "Acetaminophen",
    "Ibuprofen",
    "Amoxicillin",
    "Isoniazid",
    "Levofloxacin",
    "Ciprofloxacin",
    "Valproic Acid",
    "Halothane",
    "Diclofenac",
    "Phenytoin",
    "Carbamazepine",
    "Azithromycin",
    "Amiodarone",
    "Ketoconazole",
    "Methotrexate",
    "Rifampin",
    "Erythromycin",
    "Tetracycline",
    "Nitrofurantoin",
    "Minocycline",
])
def test_autocomplete_positive_samples(client: TestClient, query: str):
    """(1) 20 Sampel Uji Positif - Verifikasi data yang valid secara ketat"""
    response = client.get(f"/api/v1/compounds/autocomplete?q={query}")
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert "results" in data
    
    results = data["results"]
    assert len(results) > 0, f"Pencarian autocomplete untuk '{query}' harus mengembalikan minimal 1 hasil!"
    
    for item in results:
        assert "hepatwin_id" in item
        assert "compound_name" in item
        assert item.get("is_simulatable") is True

@pytest.mark.e2e
@pytest.mark.parametrize("wild_query", [
    "ObatSakti123",
    "RandomCompound",
    "C1=CC=CC=C1", # Benzene SMILES
    "CC(=O)OC1=CC=CC=C1C(=O)O", # Aspirin SMILES mentah
    "TolakAngin",
    "SuperHealingPotion",
    "FakeDrug999",
    "UnregisteredCompound",
    "XYZ-12345",
    "TidakAdaObatIni"
])
def test_autocomplete_negative_wild_samples(client: TestClient, wild_query: str):
    """(2) 10 Sampel Negatif Liar (Anti-Halusinasi / Injeksi Bebas)"""
    response = client.get(f"/api/v1/compounds/autocomplete?q={wild_query}")
    if response.status_code == 400:
        return # SMILES rejection is 400
    assert response.status_code == 200 # Now returns 200 with empty list
    assert len(response.json()["results"]) == 0

@pytest.mark.e2e
@pytest.mark.parametrize("biologic", [
    "Infliximab",
    "Rituximab",
    "Adalimumab",
    "Epoetin alfa",
    "Insulin human",
    "Trastuzumab",
    "Bevacizumab",
    "Pembrolizumab",
    "Etanercept",
    "Daratumumab"
])
def test_autocomplete_biologic_isolation(client: TestClient, biologic: str):
    """(3) 10 Sampel Biologik - Pastikan 0% TAMPIL karena is_simulatable = FALSE"""
    response = client.get(f"/api/v1/compounds/autocomplete?q={biologic}")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0

@pytest.mark.e2e
@pytest.mark.parametrize("edge_case", [
    "Para  cetamol",  # Spasi ganda
    " ibuprofen ",    # Spasi awal akhir
    "%moxiflox%",     # SQL like wildcard
    "Ibu'profen",     # Quote
    'Cipro"floxacin', # Double quote
    "Cipro\\floxacin", # Slash (backslash)
    "a" * 200,        # Very long string
    "   ",            # Hanya spasi (fastapi strip() melempar 400 bad request)
    "_+-"             # Karakter aneh saja
])
def test_autocomplete_edge_cases(client: TestClient, edge_case: str):
    """(4) Edge Cases & Sanitasi Input"""
    response = client.get(f"/api/v1/compounds/autocomplete?q={edge_case}")
    if not edge_case.strip():
        assert response.status_code == 400
        assert "tidak boleh kosong" in response.json()["detail"].lower()
    else:
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)
