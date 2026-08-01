import numpy as np

from hepatwin_ml.significance import bootstrap_auc_ci, delong_test, wilcoxon_vs_gatnn


def test_wilcoxon_identical_arrays_gives_p_one():
    aucs = [0.7, 0.72, 0.68, 0.75, 0.71]
    result = wilcoxon_vs_gatnn(aucs, aucs)
    assert result["p_value"] == 1.0
    assert result["mean_diff"] == 0.0


def test_wilcoxon_clearly_different_arrays_gives_small_p():
    gatnn = [0.80, 0.82, 0.78, 0.85, 0.81, 0.79, 0.83, 0.80, 0.84, 0.82]
    weaker = [0.60, 0.62, 0.58, 0.65, 0.61, 0.59, 0.63, 0.60, 0.64, 0.62]
    result = wilcoxon_vs_gatnn(gatnn, weaker)
    assert result["p_value"] < 0.01
    assert result["mean_diff"] > 0


def test_delong_identical_predictions_gives_zero_diff():
    rng = np.random.default_rng(0)
    y_true = rng.integers(0, 2, size=100)
    proba = rng.uniform(0, 1, size=100)
    result = delong_test(y_true, proba, proba.copy())
    assert abs(result["diff"]) < 1e-9
    assert result["p_value"] > 0.99


def test_delong_perfect_vs_random_shows_significant_difference():
    rng = np.random.default_rng(0)
    n = 200
    y_true = np.array([1] * (n // 2) + [0] * (n // 2))
    # Model A: pemisahan sempurna (AUC=1.0)
    proba_a = np.array([0.9 + 0.01 * i for i in range(n // 2)] + [0.1 - 0.001 * i for i in range(n // 2)])
    proba_a = np.clip(proba_a, 0, 1)
    # Model B: acak (AUC ~0.5)
    proba_b = rng.uniform(0, 1, size=n)

    result = delong_test(y_true, proba_a, proba_b)
    assert result["auc_a"] > 0.95
    assert 0.3 < result["auc_b"] < 0.7
    assert result["p_value"] < 0.05


def test_bootstrap_ci_contains_point_estimate():
    rng = np.random.default_rng(1)
    y_true = rng.integers(0, 2, size=150)
    y_prob = np.clip(y_true * 0.4 + rng.normal(0, 0.25, size=150) + 0.3, 0, 1)
    result = bootstrap_auc_ci(y_true, y_prob, n_resample=500, seed=1)
    assert result["ci_lower"] <= result["point_estimate"] <= result["ci_upper"]
    assert result["n_resample_used"] > 400


def test_bootstrap_ci_narrow_for_perfect_classifier():
    y_true = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0] * 10)
    y_prob = np.array([0.9, 0.85, 0.95, 0.88, 0.92, 0.1, 0.15, 0.05, 0.12, 0.08] * 10)
    result = bootstrap_auc_ci(y_true, y_prob, n_resample=500, seed=1)
    assert result["point_estimate"] == 1.0
    assert result["ci_lower"] > 0.9
