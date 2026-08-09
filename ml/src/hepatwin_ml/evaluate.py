"""Metrik evaluasi bersama (dipakai TU.8/TU.9/TU.10/TU.13).

UPSCALE.md SS4.2: AUC-ROC, AUC-PR, Accuracy, Sensitivity, Specificity,
Precision, F1, MCC, Brier score, ECE.
"""
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    matthews_corrcoef,
    precision_score,
    roc_auc_score,
)


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """ECE standar: rata-rata |akurasi_bin - confidence_bin| berbobot jumlah sampel per bin."""
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (y_prob > lo) & (y_prob <= hi) if lo > 0 else (y_prob >= lo) & (y_prob <= hi)
        if mask.sum() == 0:
            continue
        bin_acc = y_true[mask].mean()
        bin_conf = y_prob[mask].mean()
        ece += (mask.sum() / n) * abs(bin_acc - bin_conf)
    return float(ece)


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    y_pred = (y_prob >= threshold).astype(int)

    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) > 0 else float("nan")

    metrics = {
        "auc_roc": roc_auc_score(y_true, y_prob) if len(set(y_true)) > 1 else float("nan"),
        "auc_pr": average_precision_score(y_true, y_prob) if len(set(y_true)) > 1 else float("nan"),
        "accuracy": accuracy_score(y_true, y_pred),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "mcc": matthews_corrcoef(y_true, y_pred) if len(set(y_pred)) > 1 else 0.0,
        "brier": brier_score_loss(y_true, y_prob),
        "ece": expected_calibration_error(y_true, y_prob),
    }
    return metrics


def summarize_across_seeds(metrics_list: list[dict]) -> dict:
    """List hasil compute_metrics (lintas seed/fold) -> {metrik: (mean, std)}."""
    keys = metrics_list[0].keys()
    out = {}
    for k in keys:
        values = np.array([m[k] for m in metrics_list], dtype=np.float64)
        out[k] = (float(np.nanmean(values)), float(np.nanstd(values)))
    return out
