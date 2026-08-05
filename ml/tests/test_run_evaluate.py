"""C7 -- test hasil evaluasi (butuh ml/reports/C7_evaluasi.json dari
ml/scripts/run_evaluate.py, di-skip otomatis bila belum pernah dijalankan)."""
import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_PATH = _REPO_ROOT / "ml" / "reports" / "C7_evaluasi.json"
CALIBRATOR_PATH = _REPO_ROOT / "ml" / "models" / "calibrator_gatnn_dnn.pkl"

pytestmark = pytest.mark.skipif(
    not RESULTS_PATH.exists(),
    reason="Jalankan ml/scripts/run_evaluate.py dulu",
)

REQUIRED_MODELS = {"gatnn_dnn", "random_forest", "lightgbm", "xgboost", "logistic_regression"}
REQUIRED_METRIC_KEYS = {
    "auc_roc", "auc_pr", "accuracy", "sensitivity", "specificity",
    "precision", "f1", "mcc", "brier", "ece",
}


@pytest.fixture(scope="module")
def results() -> dict:
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


def test_all_required_models_present(results):
    assert REQUIRED_MODELS <= set(results["metrics"].keys())


def test_all_metric_keys_present_and_numeric(results):
    for model_name, metrics in results["metrics"].items():
        missing = REQUIRED_METRIC_KEYS - set(metrics.keys())
        assert not missing, f"{model_name} kehilangan metrik: {missing}"
        for key in REQUIRED_METRIC_KEYS:
            assert isinstance(metrics[key], (int, float)), f"{model_name}.{key} bukan angka"


def test_no_suspiciously_high_auc(results):
    """🚩 AC C7: AUC > 0.90 wajib diaudit, tidak boleh lolos diam-diam."""
    for model_name, metrics in results["metrics"].items():
        assert metrics["auc_roc"] <= 0.90, f"{model_name} AUC={metrics['auc_roc']} > 0.90 -- audit kebocoran"


def test_ece_improves_after_calibration(results):
    cal = results["gatnn_dnn_calibration"]
    assert cal["ece_after"] < cal["ece_before"]


def test_calibrator_artifact_saved(results):
    assert CALIBRATOR_PATH.exists()


def test_confusion_matrix_shape(results):
    cm = results["confusion_matrix_gatnn_dnn"]
    assert len(cm) == 2 and all(len(row) == 2 for row in cm)
    total = sum(sum(row) for row in cm)
    assert total == results["n_test"]
