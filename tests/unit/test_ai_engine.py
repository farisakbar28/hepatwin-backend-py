"""C10 -- test HybridAIEngine (versi GATNN-DNN, menggantikan GCNConv lama).

Butuh artefak model nyata (app/models/model_gatnn_dnn.pt dari C6/C9) --
di-skip otomatis bila belum ada (mis. clone baru belum menjalankan pipeline ml/)."""
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.services.ai_engine import HybridAIEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
_MODEL_EXISTS = (REPO_ROOT / settings.AI_MODEL_PATH).exists()

pytestmark = pytest.mark.skipif(
    not _MODEL_EXISTS,
    reason=f"Artefak model tidak ditemukan di {settings.AI_MODEL_PATH} -- jalankan pipeline ml/ dulu (C6/C9)",
)

PARACETAMOL_SMILES = "CC(=O)Nc1ccc(O)cc1"
IBUPROFEN_SMILES = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"


@pytest.fixture(scope="module")
def engine() -> HybridAIEngine:
    return HybridAIEngine(model_path=settings.AI_MODEL_PATH)


def test_engine_ready_and_metadata_populated(engine):
    assert engine.ready is True
    assert engine.model_status == "trained"
    assert engine.model_version
    assert isinstance(engine.score_is_calibrated, bool)


def test_predict_dili_risk_returns_probability_in_range(engine):
    score = engine.predict_dili_risk(PARACETAMOL_SMILES)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_predict_dili_risk_deterministic_for_same_input(engine):
    """PRD: keluaran 100% konsisten -- dua panggilan input identik -> skor identik."""
    s1 = engine.predict_dili_risk(PARACETAMOL_SMILES)
    s2 = engine.predict_dili_risk(PARACETAMOL_SMILES)
    assert s1 == s2


def test_predict_dili_risk_rejects_invalid_smiles_with_422(engine):
    with pytest.raises(HTTPException) as exc_info:
        engine.predict_dili_risk("XYZ123")
    assert exc_info.value.status_code == 422


def test_predict_dili_risk_handles_molecule_without_bonds(engine):
    """C3/C8 AC: molekul tanpa ikatan (ion tunggal) tidak boleh crash."""
    score = engine.predict_dili_risk("[Na+]")
    assert 0.0 <= score <= 1.0


def test_get_shap_detail_schema_and_honesty(engine):
    detail = engine.get_shap_detail(PARACETAMOL_SMILES)
    assert set(detail.keys()) == {"method", "groups", "atoms", "smiles_used"}
    assert detail["method"] == "masking_attribution"  # bukan "SHAP" -- aturan kejujuran C8


def test_get_shap_detail_no_smarts_match_returns_empty_groups_not_crash(engine):
    detail = engine.get_shap_detail("CC")  # etana -- tidak match satu pun dari 9 pola
    assert detail["groups"] == []


def test_get_explainability_backward_compatible_list_str(engine):
    names = engine.get_explainability(PARACETAMOL_SMILES)
    assert isinstance(names, list)
    assert all(isinstance(n, str) for n in names)


def test_model_unavailable_raises_503_not_silent_fallback():
    """Cacat #4 (C10): TIDAK ADA return 0.5 diam-diam."""
    broken_engine = HybridAIEngine(model_path="app/models/__nonexistent_for_test__.pt")
    assert broken_engine.ready is False
    assert broken_engine.model_status == "unavailable"
    with pytest.raises(HTTPException) as exc_info:
        broken_engine.predict_dili_risk(PARACETAMOL_SMILES)
    assert exc_info.value.status_code == 503


def test_paracetamol_scores_higher_than_ibuprofen(engine):
    """C11 pola uji eksplisit: arah relatif (parasetamol vMost-DILI-concern >
    ibuprofen risiko lebih rendah), bukan nilai absolut -- supaya test tidak
    rapuh terhadap retraining yang sah."""
    score_paracetamol = engine.predict_dili_risk(PARACETAMOL_SMILES)
    score_ibuprofen = engine.predict_dili_risk(IBUPROFEN_SMILES)
    assert score_paracetamol > score_ibuprofen, (
        f"Ekspektasi parasetamol > ibuprofen tidak terpenuhi "
        f"(parasetamol={score_paracetamol:.4f}, ibuprofen={score_ibuprofen:.4f}) -- "
        "dicatat sebagai temuan model, bukan bug test."
    )
