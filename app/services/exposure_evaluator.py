import math
from enum import Enum
from typing import Any, Dict

from app.services import pbpk_calibration


class ExposureRiskLevel(str, Enum):
    LOW = "LOW_EXPOSURE"
    MODERATE = "MODERATE_EXPOSURE"
    HIGH = "HIGH_EXPOSURE"


class ExposureEvaluatorService:
    """Evaluate PRD v2.3 PBPK magnitude exposure from frozen quantiles only."""

    @staticmethod
    def evaluate_relative_exposure(cmax: float, auc: float, **_: Any) -> Dict[str, Any]:
        if not all(math.isfinite(float(value)) and float(value) >= 0.0 for value in (cmax, auc)):
            raise ValueError("Cmax dan AUC harus bernilai finite dan tidak negatif.")
        pbpk_calibration.ensure_runtime_config_matches_calibration()
        if pbpk_calibration.P33_EXPOSURE_INDEX is None or pbpk_calibration.P66_EXPOSURE_INDEX is None:
            raise RuntimeError("PBPK exposure calibration v2.3 belum dibekukan.")

        cmax = float(cmax)
        auc = float(auc)
        shape_ratio_h_inv = cmax / auc if auc > 0.0 else 0.0
        exposure_index = math.log1p(cmax) + math.log1p(auc)
        p33 = float(pbpk_calibration.P33_EXPOSURE_INDEX)
        p66 = float(pbpk_calibration.P66_EXPOSURE_INDEX)
        if not math.isfinite(p33) or not math.isfinite(p66) or p33 > p66:
            raise RuntimeError("PBPK exposure calibration v2.3 tidak valid.")

        if exposure_index < p33:
            risk_level = ExposureRiskLevel.LOW
        elif exposure_index <= p66:
            risk_level = ExposureRiskLevel.MODERATE
        else:
            risk_level = ExposureRiskLevel.HIGH

        return {
            "risk_level": risk_level.value,
            "cmax_auc_ratio": shape_ratio_h_inv,
            "shape_ratio_h_inv": shape_ratio_h_inv,
            "exposure_index": exposure_index,
            "p33_calibration": p33,
            "p66_calibration": p66,
            "exposure_category_source": pbpk_calibration.CALIBRATION_SOURCE,
            "calibration_version": pbpk_calibration.CALIBRATION_VERSION,
        }
