"""C11 -- Unit test endpoint inferensi AI (POST /api/v1/simulate), tabel edge
case wajib EXECUTION_PLAN_FIX_MODEL.md C11, uji reproduktibilitas, dan uji
konsistensi training<->inferensi.

Memakai `client` fixture (tests/conftest.py, SQLite in-memory seed) --
DB di-mock, tapi HybridAIEngine (model GATNN-DNN terlatih C6/C9) TIDAK
di-mock -- setiap assert di sini adalah inferensi model NYATA.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _valid_payload(hepatwin_id: str) -> dict:
    return {
        "hepatwin_id": hepatwin_id,
        "dosis_mg": 500.0,
        "covariates": {"usia": 35, "jenis_kelamin": "L", "berat_badan_kg": 70.0, "tinggi_badan_cm": 170.0},
    }


@pytest.mark.e2e
class TestKnownCompoundRelativeRisk:
    """C11: senyawa berlabel diketahui -- uji ARAH RELATIF, bukan nilai
    absolut (model boleh dilatih ulang secara sah tanpa membuat test rapuh)."""

    def test_paracetamol_scores_higher_than_ibuprofen(self, client):
        # Q11: Use real IDs from export
        resp_para = client.post("/api/v1/simulate", json=_valid_payload("HT0012"))  # Acetaminophen
        resp_ibu = client.post("/api/v1/simulate", json=_valid_payload("HT0611"))   # Ibuprofen
        assert resp_para.status_code == 200
        assert resp_ibu.status_code == 200

        score_para = resp_para.json()["dili_score"]
        score_ibu = resp_ibu.json()["dili_score"]
        assert score_para > score_ibu, (
            f"Ekspektasi parasetamol (vMost-DILI-concern) > ibuprofen (risiko lebih rendah): "
            f"para={score_para}, ibu={score_ibu} -- dicatat sebagai temuan model bila terbalik."
        )


@pytest.mark.e2e
class TestEdgeCasesWajib:
    """C11 tabel edge case wajib."""

    def test_hepatwin_id_tidak_ada_returns_404(self, client):
        resp = client.post("/api/v1/simulate", json=_valid_payload("HT-FIKTIF-TIDAK-ADA-999"))
        assert resp.status_code == 404

    def test_senyawa_is_simulatable_false_ditolak(self, client):
        """Senyawa biologik (is_simulatable=FALSE) -- ditolak, tidak masuk pipeline AI."""
        # Q11: Use real biologic ID
        resp = client.post("/api/v1/simulate", json=_valid_payload("HT0003")) # Abatacept
        assert resp.status_code == 422
        assert "biologik" in resp.json()["detail"].lower()

    def test_smiles_multi_fragmen_garam_berhasil(self, client):
        """SMILES garam (mengandung '.') -- berhasil, fragmen terbesar diambil
        (perbaikan standardize.py C2), bukan ditolak."""
        resp = client.post("/api/v1/simulate", json=_valid_payload("HT-C11-SALT"))
        assert resp.status_code == 200
        assert 0.0 <= resp.json()["dili_score"] <= 1.0

    def test_smiles_tidak_valid_di_database_ditangani_rapi_bukan_500(self, client):
        """Data DB korup/SMILES tidak valid -- endpoint tetap menjawab rapi
        (422 dari ai_engine, diteruskan lewat handler HTTPException bawaan
        FastAPI), BUKAN 500 dengan traceback mentah."""
        resp = client.post("/api/v1/simulate", json=_valid_payload("HT-C11-INVALID-SMILES"))
        assert resp.status_code != 500
        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data
        # Tidak ada traceback/exception mentah bocor ke body (C10 langkah 5).
        assert "Traceback" not in json.dumps(data)

    def test_molekul_tanpa_ikatan_tidak_crash(self):
        """Ion tunggal (mis. [Na+]) tidak boleh crash -- diuji langsung di
        level ai_engine (C3/C8 AC), bukan lewat endpoint (tidak ada senyawa
        ion tunggal is_simulatable=TRUE di database nyata)."""
        sys.path.insert(0, str(REPO_ROOT))
        from app.core.config import settings
        from app.services.ai_engine import HybridAIEngine

        if not (REPO_ROOT / settings.AI_MODEL_PATH).exists():
            pytest.skip("Artefak model tidak ditemukan")
        engine = HybridAIEngine(model_path=settings.AI_MODEL_PATH)
        score = engine.predict_dili_risk("[Na+]")
        assert 0.0 <= score <= 1.0

    def test_artefak_model_tidak_ada_503_bukan_skor_palsu(self):
        sys.path.insert(0, str(REPO_ROOT))
        from app.services.ai_engine import HybridAIEngine
        from fastapi import HTTPException

        broken_engine = HybridAIEngine(model_path="app/models/__c11_nonexistent__.pt")
        with pytest.raises(HTTPException) as exc_info:
            broken_engine.predict_dili_risk("CC(=O)Nc1ccc(O)cc1")
        assert exc_info.value.status_code == 503

    def test_molekul_tanpa_match_smarts_shap_list_kosong_bukan_crash(self):
        sys.path.insert(0, str(REPO_ROOT))
        from app.core.config import settings
        from app.services.ai_engine import HybridAIEngine

        if not (REPO_ROOT / settings.AI_MODEL_PATH).exists():
            pytest.skip("Artefak model tidak ditemukan")
        engine = HybridAIEngine(model_path=settings.AI_MODEL_PATH)
        names = engine.get_explainability("CC")  # etana -- tidak match satu pun dari 9 pola SMARTS
        assert names == []


@pytest.mark.e2e
class TestReproducibility:
    """PRD: keluaran 100% konsisten -- dua panggilan input identik -> identik."""

    def test_repeated_calls_same_input_identical_score_and_shap(self, client):
        payload = _valid_payload("HT0012")
        resp1 = client.post("/api/v1/simulate", json=payload)
        resp2 = client.post("/api/v1/simulate", json=payload)

        assert resp1.status_code == resp2.status_code == 200
        data1, data2 = resp1.json(), resp2.json()

        assert data1["dili_score"] == data2["dili_score"]
        assert data1["explainability_shap"] == data2["explainability_shap"]
        assert data1["shap_detail"] == data2["shap_detail"]


@pytest.mark.e2e
class TestTrainingInferenceConsistency:
    """C11: skor lewat app/services/ai_engine.py (jalur inferensi) vs skor
    dihitung ULANG dari nol lewat pemanggilan langsung fungsi ml/ (jalur
    training) pada senyawa test set C5 -- harus sama persis (toleransi
    floating point). Kedua jalur SECARA DESAIN memanggil fungsi identik
    (hepatwin_ml.features.graph.smiles_to_graph, .fingerprints.dnn_feature_vector,
    C10 langkah 2: "jangan duplikasi") -- test ini adalah regression guard:
    kalau suatu saat ai_engine.py atau ml/ diubah sampai keduanya menyimpang,
    test ini yang pertama merah, sebelum ketidakcocokan itu sampai ke user."""

    def test_ai_engine_score_matches_raw_ml_pipeline_on_c5_test_compounds(self):
        sys.path.insert(0, str(REPO_ROOT / "ml" / "src"))
        import pandas as pd
        import torch
        from torch_geometric.data import Batch

        from app.core.config import settings
        from app.services.ai_engine import HybridAIEngine
        from hepatwin_ml.features.fingerprints import dnn_feature_vector
        from hepatwin_ml.features.graph import smiles_to_graph
        from rdkit import Chem

        test_parquet = REPO_ROOT / "ml" / "data" / "processed" / "test.parquet"
        if not test_parquet.exists() or not (REPO_ROOT / settings.AI_MODEL_PATH).exists():
            pytest.skip("Butuh ml/data/processed/test.parquet (C5) dan model terlatih (C6/C9)")

        test_df = pd.read_parquet(test_parquet)
        sample = test_df.sample(n=min(5, len(test_df)), random_state=42)

        engine = HybridAIEngine(model_path=settings.AI_MODEL_PATH)

        for row in sample.itertuples(index=False):
            # Jalur A: app/services/ai_engine.py (dipakai endpoint /simulate nyata)
            engine_score = engine.predict_dili_risk(row.canonical_smiles)

            # Jalur B: dibangun ulang dari nol langsung dari ml/ (dipakai training)
            mol = Chem.MolFromSmiles(row.canonical_smiles)
            graph_data = smiles_to_graph(row.canonical_smiles)
            fingerprint = torch.tensor(dnn_feature_vector(mol), dtype=torch.float).unsqueeze(0)
            batch = Batch.from_data_list([graph_data])
            batch.fingerprint = fingerprint
            with torch.no_grad():
                raw_prob = torch.sigmoid(engine.model(batch)).item()
            ml_score = float(engine.calibrator.predict([raw_prob])[0]) if engine.calibrator else raw_prob

            assert engine_score == pytest.approx(ml_score, abs=1e-6), (
                f"Skor ai_engine vs pipeline ml/ menyimpang untuk {row.hepatwin_id}: "
                f"{engine_score} vs {ml_score} -- indikasi drift featurization training<->inferensi."
            )
