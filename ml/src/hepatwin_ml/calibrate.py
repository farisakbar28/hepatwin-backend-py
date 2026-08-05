"""TU.10 -- Kalibrasi probabilitas (UPSCALE.md SS6, wajib).

Isotonic regression secara default; fallback ke Platt scaling (logistic
regression 1D) bila ukuran set kalibrasi < 200 sampel -- ambang ini sesuai
UPSCALE.md SS6 persis.
"""
from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

MIN_ISOTONIC_N = 200


@dataclass
class Calibrator:
    method: Literal["isotonic", "platt"]
    model: object

    def predict(self, probs: np.ndarray) -> np.ndarray:
        probs = np.asarray(probs)
        if self.method == "isotonic":
            return self.model.predict(probs)
        return self.model.predict_proba(probs.reshape(-1, 1))[:, 1]


def fit_calibrator(cal_probs: np.ndarray, cal_labels: np.ndarray, min_isotonic_n: int = MIN_ISOTONIC_N) -> Calibrator:
    """Fit kalibrator pada set kalibrasi (HARUS terpisah dari set training model
    & test akhir -- lihat run_calibration.py untuk skema split)."""
    n = len(cal_labels)
    if n >= min_isotonic_n:
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(cal_probs, cal_labels)
        return Calibrator("isotonic", iso)

    lr = LogisticRegression()
    lr.fit(np.asarray(cal_probs).reshape(-1, 1), cal_labels)
    return Calibrator("platt", lr)
