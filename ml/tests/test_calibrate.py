import numpy as np

from hepatwin_ml.calibrate import fit_calibrator


def test_fit_calibrator_uses_platt_below_threshold():
    rng = np.random.default_rng(0)
    n = 100
    labels = rng.integers(0, 2, size=n)
    probs = np.clip(labels * 0.6 + rng.normal(0, 0.2, size=n) + 0.2, 0.01, 0.99)
    calibrator = fit_calibrator(probs, labels, min_isotonic_n=200)
    assert calibrator.method == "platt"


def test_fit_calibrator_uses_isotonic_at_or_above_threshold():
    rng = np.random.default_rng(0)
    n = 250
    labels = rng.integers(0, 2, size=n)
    probs = np.clip(labels * 0.6 + rng.normal(0, 0.2, size=n) + 0.2, 0.01, 0.99)
    calibrator = fit_calibrator(probs, labels, min_isotonic_n=200)
    assert calibrator.method == "isotonic"


def test_calibrator_output_stays_in_unit_interval():
    rng = np.random.default_rng(1)
    n = 300
    labels = rng.integers(0, 2, size=n)
    probs = np.clip(labels * 0.5 + rng.normal(0, 0.3, size=n) + 0.25, 0.0, 1.0)
    calibrator = fit_calibrator(probs, labels)
    out = calibrator.predict(probs)
    assert (out >= 0).all() and (out <= 1).all()
