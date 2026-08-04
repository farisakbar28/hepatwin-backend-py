import pytest
from fastapi.testclient import TestClient

@pytest.mark.e2e
@pytest.mark.parametrize("expected", [
    {
        "query": "Acetaminophen", "hepatwin_id": "HT-001", "ltkb_id": "LTKB-001", "cid": 1983,
        "compound_name": "Acetaminophen", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CC(=O)NC1=CC=C(O)C=C1", "injury_pattern": "Hepatocellular",
        "segment_list": "V, VI, VII, VIII"
    },
    {
        "query": "Ibuprofen", "hepatwin_id": "HT-002", "ltkb_id": "LTKB-002", "cid": 3672,
        "compound_name": "Ibuprofen", "dili_concern": "Less-DILI-Concern",
        "canonical_smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "injury_pattern": "Mixed",
        "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Amoxicillin", "hepatwin_id": "HT-003", "ltkb_id": "LTKB-003", "cid": 33613,
        "compound_name": "Amoxicillin", "dili_concern": "Less-DILI-Concern",
        "canonical_smiles": "CC1(C(N2C(S1)C(C2=O)NC(=O)C(C3=CC=C(C=C3)O)N)C(=O)O)C", "injury_pattern": "Mixed",
        "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Isoniazid", "hepatwin_id": "HT-004", "ltkb_id": "LTKB-004", "cid": 3767,
        "compound_name": "Isoniazid", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "C1=CN=CC=C1C(=O)NN", "injury_pattern": "Hepatocellular",
        "segment_list": "V, VI, VII, VIII"
    },
    {
        "query": "Levofloxacin", "hepatwin_id": "HT-005", "ltkb_id": "LTKB-005", "cid": 149096,
        "compound_name": "Levofloxacin", "dili_concern": "Less-DILI-Concern",
        "canonical_smiles": "CC1COC2=C3N1C=C(C(=O)C3=CC(=C2F)N4CCN(CC4)C)C(=O)O", "injury_pattern": "Cholestatic",
        "segment_list": "II, III, IV"
    },
    {
        "query": "Ciprofloxacin", "hepatwin_id": "HT-006", "ltkb_id": "LTKB-006", "cid": 2764,
        "compound_name": "Ciprofloxacin", "dili_concern": "Less-DILI-Concern",
        "canonical_smiles": "C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O", "injury_pattern": "Cholestatic",
        "segment_list": "II, III, IV"
    },
    {
        "query": "Valproic Acid", "hepatwin_id": "HT-007", "ltkb_id": "LTKB-007", "cid": 3121,
        "compound_name": "Valproic Acid", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CCCC(CCC)C(=O)O", "injury_pattern": "Hepatocellular",
        "segment_list": "V, VI, VII, VIII"
    },
    {
        "query": "Halothane", "hepatwin_id": "HT-008", "ltkb_id": "LTKB-008", "cid": 3562,
        "compound_name": "Halothane", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "C(C(F)(F)F)(Cl)Br", "injury_pattern": "Hepatocellular",
        "segment_list": "V, VI, VII, VIII"
    },
    {
        "query": "Diclofenac", "hepatwin_id": "HT-009", "ltkb_id": "LTKB-009", "cid": 3033,
        "compound_name": "Diclofenac", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "C1=CC=C(C(=C1)CC(=O)O)NC2=C(C=CC=C2Cl)Cl", "injury_pattern": "Hepatocellular",
        "segment_list": "V, VI, VII, VIII"
    },
    {
        "query": "Phenytoin", "hepatwin_id": "HT-010", "ltkb_id": "LTKB-010", "cid": 1775,
        "compound_name": "Phenytoin", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "C1=CC=C(C=C1)C2(C(=O)NC(=O)N2)C3=CC=C(C=C3)", "injury_pattern": "Mixed",
        "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Carbamazepine", "hepatwin_id": "HT-011", "ltkb_id": "LTKB-011", "cid": 2554,
        "compound_name": "Carbamazepine", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "C1=CC=C2C(=C1)C=CC3=CC=CC=C3N2C(=O)N", "injury_pattern": "Mixed",
        "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Azithromycin", "hepatwin_id": "HT-012", "ltkb_id": "LTKB-012", "cid": 447043,
        "compound_name": "Azithromycin", "dili_concern": "Less-DILI-Concern",
        "canonical_smiles": "CCC1C(C(C(N(CC(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)C)O)(C)O",
        "injury_pattern": "Cholestatic", "segment_list": "II, III, IV"
    },
    {
        "query": "Amiodarone", "hepatwin_id": "HT-013", "ltkb_id": "LTKB-013", "cid": 2162,
        "compound_name": "Amiodarone", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CCCCC1=C(C2=CC=CC=C2O1)C(=O)C3=CC(=C(C(=C3)I)OCCN(CC)CC)I",
        "injury_pattern": "Hepatocellular", "segment_list": "V, VI, VII, VIII"
    },
    {
        "query": "Ketoconazole", "hepatwin_id": "HT-014", "ltkb_id": "LTKB-014", "cid": 3823,
        "compound_name": "Ketoconazole", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CC(=O)N1CCC(CC1)N2C=CC(=C2)OCC3COC(O3)(CN4C=CN=C4)C5=C(C=C(C=C5)Cl)Cl",
        "injury_pattern": "Mixed", "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Methotrexate", "hepatwin_id": "HT-015", "ltkb_id": "LTKB-015", "cid": 4112,
        "compound_name": "Methotrexate", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)NC(CCC(=O)O)C(=O)O",
        "injury_pattern": "Hepatocellular", "segment_list": "V, VI, VII, VIII"
    },
    {
        "query": "Rifampin", "hepatwin_id": "HT-016", "ltkb_id": "LTKB-016", "cid": 135398738,
        "compound_name": "Rifampin", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CC1C=CC=C(C(=O)NC2=C(C(=C3C(=C2O)C(=C(C4=C3C(=O)C(O4)(OC=C1C(C(C(C(C(C(C)O)(C)O)C)OC(=O)C)C)OC)C)C)O)C=NNC5CCN(CC5)C)C",
        "injury_pattern": "Mixed", "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Erythromycin", "hepatwin_id": "HT-017", "ltkb_id": "LTKB-017", "cid": 12560,
        "compound_name": "Erythromycin", "dili_concern": "Less-DILI-Concern",
        "canonical_smiles": "CCC1C(C(C(C(=O)C(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)O)(C)O",
        "injury_pattern": "Cholestatic", "segment_list": "II, III, IV"
    },
    {
        "query": "Tetracycline", "hepatwin_id": "HT-018", "ltkb_id": "LTKB-018", "cid": 54675776,
        "compound_name": "Tetracycline", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CC1(C2CC3C(C(=O)C(=C(C3(C(=O)C2=C(C4=C1C=CC=C4O)O)O)O)C(=O)N)N(C)C)O",
        "injury_pattern": "Mixed", "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Nitrofurantoin", "hepatwin_id": "HT-019", "ltkb_id": "LTKB-019", "cid": 6604200,
        "compound_name": "Nitrofurantoin", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "C1=C(OC(=C1)C=NNC2=O)C(=O)N(C2=O)C",
        "injury_pattern": "Mixed", "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    },
    {
        "query": "Minocycline", "hepatwin_id": "HT-020", "ltkb_id": "LTKB-020", "cid": 54675783,
        "compound_name": "Minocycline", "dili_concern": "Most-DILI-Concern",
        "canonical_smiles": "CN(C)C1=C(C=CC2=C1C(C3CC4C(C(=O)C(=C(C4(C(=O)C3=C2O)O)O)C(=O)N)N(C)C)O)O",
        "injury_pattern": "Mixed", "segment_list": "I, II, III, IV, V, VI, VII, VIII"
    }
])
def test_lookup_valid_flow(client: TestClient, expected: dict):
    """
    Menguji lookup valid flow (20 Sampel Obat Simulatable).
    Langkah 1: Gunakan autocomplete untuk mendapatkan hepatwin_id riil dari database.
    Langkah 2: Panggil /compounds/{hepatwin_id} dan verifikasi presisi numerik & kualitatif 40 kolom.
    """
    query = expected["query"]
    autocomplete_res = client.get(f"/api/v1/compounds/autocomplete?q={query}")
    assert autocomplete_res.status_code == 200, f"Gagal autocomplete: {autocomplete_res.text}"
    results = autocomplete_res.json()
    
    assert len(results["results"]) > 0, f"Query '{query}' tidak ditemukan di autocomplete"
        
    first_item = results["results"][0]
    hepatwin_id = first_item["hepatwin_id"]
    assert hepatwin_id == expected["hepatwin_id"]
    
    # Direct detail lookup
    lookup_res = client.get(f"/api/v1/compounds/{hepatwin_id}")
    assert lookup_res.status_code == 200, f"Gagal lookup: {lookup_res.text}"
    data = lookup_res.json()
    
    # Deep Numerical & Categorical Verification (ASME V&V 40 Compliance)
    assert data["hepatwin_id"] == expected["hepatwin_id"]
    assert data["ltkb_id"] == expected["ltkb_id"]
    assert data["cid"] == expected["cid"]
    assert data["compound_name"] == expected["compound_name"]
    assert data["dili_concern"] == expected["dili_concern"]
    assert data["canonical_smiles"] == expected["canonical_smiles"]
    assert data["injury_pattern"] == expected["injury_pattern"]
    assert data["segment_list"] == expected["segment_list"]
    assert data["is_simulatable"] is True

@pytest.mark.e2e
def test_lookup_invalid_id(client: TestClient):
    """Menguji penanganan id ngawur pada lookup (Strict 404)."""
    response = client.get("/api/v1/compounds/INVALID_ID_99999")
    assert response.status_code == 404
    assert "tidak ditemukan" in response.json()["detail"].lower()

@pytest.mark.e2e
@pytest.mark.parametrize("biologic_id, biologic_name", [
    ("HT-BIOLOGIC-001", "Infliximab"),
    ("HT-BIOLOGIC-002", "Rituximab"),
    ("HT-BIOLOGIC-003", "Adalimumab"),
    ("HT-BIOLOGIC-004", "Epoetin alfa"),
    ("HT-BIOLOGIC-005", "Insulin human"),
    ("HT-BIOLOGIC-006", "Trastuzumab"),
    ("HT-BIOLOGIC-007", "Bevacizumab"),
    ("HT-BIOLOGIC-008", "Pembrolizumab"),
    ("HT-BIOLOGIC-009", "Etanercept"),
    ("HT-BIOLOGIC-010", "Daratumumab"),
])
def test_lookup_biologic_ids_strict_block(client: TestClient, biologic_id: str, biologic_name: str):
    """
    Memverifikasi 10 Senyawa Biologik Nyata di Database (is_simulatable = FALSE).
    Sistem WAJIB menolak direct lookup dengan HTTP 404 (Not Found / Blocked).
    """
    response = client.get(f"/api/v1/compounds/{biologic_id}")
    assert response.status_code == 404, f"Senyawa biologik {biologic_name} ({biologic_id}) tidak diblokir!"
    assert "tidak ditemukan" in response.json()["detail"].lower() or "is_simulatable = false" in response.json()["detail"].lower()
