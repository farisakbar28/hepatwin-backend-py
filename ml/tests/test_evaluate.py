import numpy as np
import pytest

from hepatwin_ml.evaluate import compute_metrics, expected_calibration_error, summarize_across_seeds


def test_compute_metrics_perfect_predictions():
    y_true = np.array([1, 1, 0, 0])
    y_prob = np.array([0.9, 0.8, 0.1, 0.2])
    m = compute_metrics(y_true, y_prob)
    assert m["auc_roc"] == 1.0
    assert m["accuracy"] == 1.0
    assert m["sensitivity"] == 1.0
    assert m["specificity"] == 1.0
    assert m["mcc"] == 1.0


def test_expected_calibration_error_zero_for_perfectly_calibrated():
    y_true = np.array([1, 0, 1, 0])
    y_prob = np.array([1.0, 0.0, 1.0, 0.0])
    ece = expected_calibration_error(y_true, y_prob, n_bins=10)
    assert ece == 0.0


def test_summarize_across_seeds_computes_mean_std():
    metrics_list = [
        {"auc_roc": 0.7, "mcc": 0.3},
        {"auc_roc": 0.8, "mcc": 0.4},
    ]
    summary = summarize_across_seeds(metrics_list)
    assert summary["auc_roc"][0] == 0.75
    assert summary["mcc"][0] == pytest.approx(0.35)
