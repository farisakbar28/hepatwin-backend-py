"""TU.21 -- Uji signifikansi statistik (UPSCALE.md SS13.4).

wilcoxon_vs_gatnn(): dijalankan sekarang, atas AUC 10-fold outer TU.20.
delong_test() dan bootstrap_auc_ci(): DISIAPKAN di sini, dieksekusi TU.22
pada holdout_set (belum boleh disentuh sebelum TU.22).
"""
import logging

import numpy as np
from scipy.stats import norm, wilcoxon

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def wilcoxon_vs_gatnn(gatnn_aucs: list[float], baseline_aucs: list[float]) -> dict:
    """Wilcoxon signed-rank berpasangan per-fold-outer. Fold HARUS identik
    (dari outer_fold_indices.json, TU.20) -- ini yang membuat uji berpasangan valid."""
    gatnn_aucs = np.asarray(gatnn_aucs)
    baseline_aucs = np.asarray(baseline_aucs)
    diffs = gatnn_aucs - baseline_aucs
    if np.allclose(diffs, 0):
        return {"statistic": 0.0, "p_value": 1.0, "mean_diff": 0.0, "note": "semua selisih nol"}
    stat, p = wilcoxon(gatnn_aucs, baseline_aucs)
    return {"statistic": float(stat), "p_value": float(p), "mean_diff": float(diffs.mean())}


def _delong_placements(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Structural components (V10, V01) untuk estimator DeLong -- lihat
    DeLong et al. (1988), implementasi via metode placements (Sun & Xu 2014)."""
    pos = y_prob[y_true == 1]
    neg = y_prob[y_true == 0]
    n_pos, n_neg = len(pos), len(neg)

    tx = np.empty(n_pos)
    for i, p in enumerate(pos):
        tx[i] = ((neg < p).sum() + 0.5 * (neg == p).sum()) / n_neg
    ty = np.empty(n_neg)
    for j, n in enumerate(neg):
        ty[j] = ((pos > n).sum() + 0.5 * (pos == n).sum()) / n_pos
    return tx, ty


def delong_test(y_true: np.ndarray, proba_a: np.ndarray, proba_b: np.ndarray) -> dict:
    """DeLong's test membandingkan 2 AUC pada SAMPEL/TEST SET YANG SAMA
    (model A vs model B, prediksi berpasangan). Valid dipakai di TU.22 pada
    holdout_set (semua model dievaluasi pada hold-out yang identik) -- BUKAN
    valid untuk Arm A vs Arm B (sampel senyawa berbeda, lihat 07_comparison.md
    yang memakai Mann-Whitney U untuk kasus itu)."""
    y_true = np.asarray(y_true)
    auc_a = float(((proba_a[y_true == 1][:, None] > proba_a[y_true == 0][None, :]).mean()
                    + 0.5 * (proba_a[y_true == 1][:, None] == proba_a[y_true == 0][None, :]).mean()))
    auc_b = float(((proba_b[y_true == 1][:, None] > proba_b[y_true == 0][None, :]).mean()
                    + 0.5 * (proba_b[y_true == 1][:, None] == proba_b[y_true == 0][None, :]).mean()))

    tx_a, ty_a = _delong_placements(y_true, proba_a)
    tx_b, ty_b = _delong_placements(y_true, proba_b)

    n_pos, n_neg = len(tx_a), len(ty_a)
    v_a = np.concatenate([tx_a, ty_a])
    v_b = np.concatenate([tx_b, ty_b])
    v = np.vstack([v_a, v_b])
    cov = np.cov(v) / (n_pos + n_neg)  # aproksimasi kovarians gabungan (pooled), cukup untuk 2 grup independen di sini

    var_diff = cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]
    if var_diff <= 0:
        var_diff = 1e-10
    z = (auc_a - auc_b) / np.sqrt(var_diff)
    p_value = 2 * (1 - norm.cdf(abs(z)))

    return {"auc_a": auc_a, "auc_b": auc_b, "diff": auc_a - auc_b, "z": float(z), "p_value": float(p_value)}


def bootstrap_auc_ci(y_true: np.ndarray, y_prob: np.ndarray, n_resample: int = 1000, seed: int = 42) -> dict:
    """Bootstrap CI 95% untuk AUC-ROC (resample dgn penggantian pada indeks sampel)."""
    from sklearn.metrics import roc_auc_score

    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    rng = np.random.default_rng(seed)
    n = len(y_true)
    aucs = []
    for _ in range(n_resample):
        idx = rng.integers(0, n, size=n)
        if len(set(y_true[idx])) < 2:
            continue
        aucs.append(roc_auc_score(y_true[idx], y_prob[idx]))
    aucs = np.array(aucs)
    return {
        "point_estimate": float(roc_auc_score(y_true, y_prob)),
        "ci_lower": float(np.percentile(aucs, 2.5)),
        "ci_upper": float(np.percentile(aucs, 97.5)),
        "n_resample_used": len(aucs),
    }
