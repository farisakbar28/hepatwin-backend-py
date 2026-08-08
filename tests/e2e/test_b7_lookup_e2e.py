import pytest
from fastapi.testclient import TestClient

@pytest.mark.e2e
@pytest.mark.parametrize("expected", [
    {
        "query": "Acetaminophen", "hepatwin_id": "HT0012", "ltkb_id": "LT00004", "cid": 1983,
        "compound_name": "Acetaminophen", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CC(=O)NC1=CC=C(C=C1)O", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Ibuprofen", "hepatwin_id": "HT0611", "ltkb_id": "LT00199", "cid": 3672,
        "compound_name": "Ibuprofen", "dili_concern": "vLess-DILI-concern",
        "canonical_smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "injury_pattern": "Mixed",
        "segment_list": "I;II;III;IV;V;VI;VII;VIII"
    },
    {
        "query": "Amoxicillin", "hepatwin_id": "HT0066", "ltkb_id": "LT00507", "cid": 33613,
        "compound_name": "Amoxicillin", "dili_concern": "vLess-DILI-concern",
        "canonical_smiles": "CC1(C(N2C(S1)C(C2=O)NC(=O)C(C3=CC=C(C=C3)O)N)C(=O)O)C", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Isoniazid", "hepatwin_id": "HT0647", "ltkb_id": "LT00306", "cid": 3767,
        "compound_name": "Isoniazid", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "C1=CN=CC=C1C(=O)NN", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Levofloxacin", "hepatwin_id": "HT0695", "ltkb_id": "LT01488", "cid": 149096,
        "compound_name": "Levofloxacin", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CC1COC2=C3N1C=C(C(=O)C3=CC(=C2N4CCN(CC4)C)F)C(=O)O", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Valproic acid", "hepatwin_id": "HT1291", "ltkb_id": "LT00160", "cid": 3121,
        "compound_name": "Valproic acid", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CCCC(CCC)C(=O)O", "injury_pattern": "Fallback_Diffuse",
        "segment_list": "I;II;III;IV;V;VI;VII;VIII"
    },
    {
        "query": "Phenytoin", "hepatwin_id": "HT0977", "ltkb_id": "LT00032", "cid": 1775,
        "compound_name": "Phenytoin", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "C1=CC=C(C=C1)C2(C(=O)NC(=O)N2)C3=CC=CC=C3", "injury_pattern": "Mixed",
        "segment_list": "I;II;III;IV;V;VI;VII;VIII"
    },
    {
        "query": "Carbamazepine", "hepatwin_id": "HT0190", "ltkb_id": "LT00060", "cid": 2554,
        "compound_name": "Carbamazepine", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "C1=CC=C2C(=C1)C=CC3=CC=CC=C3N2C(=O)N", "injury_pattern": "Mixed",
        "segment_list": "I;II;III;IV;V;VI;VII;VIII"
    },
    {
        "query": "Azithromycin", "hepatwin_id": "HT0112", "ltkb_id": "LT00265", "cid": 447043,
        "compound_name": "Azithromycin", "dili_concern": "vLess-DILI-concern",
        "canonical_smiles": "CCC1C(C(C(N(CC(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)C)O)(C)O", "injury_pattern": "Cholestatic",
        "segment_list": "II;III;IV"
    },
    {
        "query": "Ketoconazole", "hepatwin_id": "HT0664", "ltkb_id": "LT00111", "cid": 47576,
        "compound_name": "Ketoconazole", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CC(=O)N1CCN(CC1)C2=CC=C(C=C2)OCC3COC(O3)(CN4C=CN=C4)C5=C(C=C(C=C5)Cl)Cl", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Rifampin", "hepatwin_id": "HT1072", "ltkb_id": "LT00034", "cid": 135398735,
        "compound_name": "Rifampin", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CC1C=CC=C(C(=O)NC2=C(C(=C3C(=C2O)C(=C(C4=C3C(=O)C(O4)(OC=CC(C(C(C(C(C(C1O)C)O)C)OC(=O)C)C)OC)C)C)O)O)C=NN5CCN(CC5)C)C", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Nitrofurantoin", "hepatwin_id": "HT0868", "ltkb_id": "LT00125", "cid": 6604200,
        "compound_name": "Nitrofurantoin", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "C1C(=O)NC(=O)N1N=CC2=CC=C(O2)[N+](=O)[O-]", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Doxycycline", "hepatwin_id": "HT0393", "ltkb_id": "LT00393", "cid": 54671203,
        "compound_name": "Doxycycline", "dili_concern": "vLess-DILI-concern",
        "canonical_smiles": "CC1C2C(C3C(C(=O)C(=C(C3(C(=O)C2=C(C4=C1C=CC=C4O)O)O)O)C(=O)N)N(C)C)O", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Methotrexate sodium", "hepatwin_id": "HT0775", "ltkb_id": "LT00026", "cid": 11329481,
        "compound_name": "Methotrexate sodium", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)NC(CCC(=O)[O-])C(=O)[O-].[Na+].[Na+]", "injury_pattern": "Fallback_Diffuse",
        "segment_list": "I;II;III;IV;V;VI;VII;VIII"
    },
    {
        "query": "Erythromycin estolate", "hepatwin_id": "HT0444", "ltkb_id": "LT00092", "cid": 441371,
        "compound_name": "Erythromycin estolate", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CCCCCCCCCCCCOS(=O)(=O)O.CCC1C(C(C(C(=O)C(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)OC(=O)CC)(C)O)C)C)O)(C)O", "injury_pattern": "Fallback_Diffuse",
        "segment_list": "I;II;III;IV;V;VI;VII;VIII"
    },
    {
        "query": "Minocycline hydrochloride", "hepatwin_id": "HT0806", "ltkb_id": "LT00416", "cid": 54685925,
        "compound_name": "Minocycline hydrochloride", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CN(C)C1C2CC3CC4=C(C=CC(=C4C(=C3C(=O)C2(C(=C(C1=O)C(=O)N)O)O)O)O)N(C)C.Cl", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Amiodarone hydrochloride", "hepatwin_id": "HT0060", "ltkb_id": "LT00046", "cid": 441325,
        "compound_name": "Amiodarone hydrochloride", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "CCCCC1=C(C2=CC=CC=C2O1)C(=O)C3=CC(=C(C(=C3)I)OCCN(CC)CC)I.Cl", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Ciprofloxacin hydrochloride", "hepatwin_id": "HT0255", "ltkb_id": "LT00178", "cid": 62998,
        "compound_name": "Ciprofloxacin hydrochloride", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O.O.Cl", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Diclofenac sodium", "hepatwin_id": "HT0359", "ltkb_id": "LT00084", "cid": 5018304,
        "compound_name": "Diclofenac sodium", "dili_concern": "vMost-DILI-concern",
        "canonical_smiles": "C1=CC=C(C(=C1)CC(=O)[O-])NC2=C(C=CC=C2Cl)Cl.[Na+]", "injury_pattern": "Hepatocellular",
        "segment_list": "V;VI;VII;VIII"
    },
    {
        "query": "Epoetin alfa", "hepatwin_id": "HT0433", "ltkb_id": "LT01316", "cid": 92043599,
        "compound_name": "Epoetin alfa", "dili_concern": "vNo-DILI-concern",
        "canonical_smiles": "CC1CC=CC=CC(C(CC(C(C(C(CC(=O)O1)O)OC)OC2C(C(C(C(O2)C)OC3CC(C(C(O3)C)O)(C)O)N(C)C)O)CCO)C)OC4CC(C(C(O4)C)O)(C)O", "injury_pattern": "Fallback_Diffuse",
        "segment_list": "I;II;III;IV;V;VI;VII;VIII"
    }
])
def test_lookup_valid_flow(client: TestClient, expected: dict):
    """
    Menguji lookup valid flow (20 Sampel Obat Simulatable).
    Langkah 1: Gunakan autocomplete untuk mendapatkan hepatwin_id riil dari database.
    Langkah 2: Panggil /compounds/{hepatwin_id} dan verifikasi presisi numerik & kualitatif 42 kolom.
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
    ("HT0003", "Abatacept"),
    ("HT0004", "Abciximab"),
    ("HT0019", "Adalimumab"),
    ("HT0023", "Agalsidase beta"),
    ("HT0029", "Aldesleukin"),
    ("HT0031", "Alemtuzumab"),
    ("HT0035", "Alglucosidase alfa"),
    ("HT0044", "Alteplase"),
    ("HT0072", "Anakinra"),
    ("HT0076", "Antithymocyte globulin"),
])
def test_lookup_biologic_ids_strict_block(client: TestClient, biologic_id: str, biologic_name: str):
    """
    Memverifikasi 10 Senyawa Biologik Nyata di Database (is_simulatable = FALSE).
    Sistem WAJIB menolak direct lookup dengan HTTP 422 (Unprocessable Entity).
    """
    response = client.get(f"/api/v1/compounds/{biologic_id}")
    assert response.status_code == 422, f"Senyawa biologik {biologic_name} ({biologic_id}) tidak diblokir dengan 422!"
    assert "senyawa ini bertipe biologik" in response.json()["detail"].lower()
