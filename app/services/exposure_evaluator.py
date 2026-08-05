from enum import Enum
from typing import Dict, Any

class ExposureRiskLevel(str, Enum):
    LOW = "LOW_EXPOSURE"
    MODERATE = "MODERATE_EXPOSURE"
    HIGH = "HIGH_EXPOSURE"

class ExposureEvaluatorService:
    """
    Modul evaluasi profil paparan relatif seragam tanpa garis ambang absolut.
    Berlaku konsisten untuk seluruh 1.231 senyawa is_simulatable = TRUE.
    Rujukan klinis modifikator demografis:
      - Soejima et al. (2022) [21]: Kerentanan eliminasi pada Usia >= 60 tahun.
      - Ghabril et al. (2025) [17]: MASLD/perlemakan hati pada BMI >= 30 kg/m2.
    """
    @staticmethod
    def evaluate_relative_exposure(
        cmax: float,
        auc: float,
        age: int,
        bmi: float,
        dose_mg: float,
        weight_kg: float
    ) -> Dict[str, Any]:
        if weight_kg <= 0.0 or auc < 0.0 or dose_mg < 0.0 or cmax < 0.0:
            raise ValueError("Parameter fisik/farmakokinetik tidak valid (<= 0 atau negatif).")
            
        # 1. Hitung rasio paparan relatif cmax / auc
        cmax_auc_ratio = (cmax / auc) if auc > 0 else 0.0

        # 2. Hitung dosis relatif per berat badan (mg/kg) sebagai metrik beban bolus
        dose_per_kg = dose_mg / weight_kg

        # 3. Faktor Modifikator Demografis (Usia lanjut atau Obesitas MASLD)
        has_vulnerability_modifier = (age >= 60) or (bmi >= 30.0)
        
        # Penyesuaian ambang dinamis
        high_threshold = 0.35 if has_vulnerability_modifier else 0.40
        moderate_threshold = 0.20 if has_vulnerability_modifier else 0.30

        # 4. Logika Evaluasi Seragam (Tanpa perbandingan terhadap ambang mg/L literatur)
        # Kriteria relatif empiris yang seragam untuk seluruh senyawa simulatable:
        if dose_per_kg >= 30.0 or cmax_auc_ratio > high_threshold:
            risk_level = ExposureRiskLevel.HIGH
            risk_score = 0.85
        elif dose_per_kg >= 10.0 or cmax_auc_ratio > moderate_threshold:
            risk_level = ExposureRiskLevel.MODERATE
            risk_score = 0.50
        else:
            risk_level = ExposureRiskLevel.LOW
            risk_score = 0.15

        return {
            "risk_level": risk_level.value,
            "relative_risk_score": risk_score,
            "cmax_auc_ratio": round(cmax_auc_ratio, 4),
            "dose_per_kg": round(dose_per_kg, 2),
            "has_vulnerability_modifier": has_vulnerability_modifier,
            "threshold_line_used": False  # Penegasan eksplisit bahwa ambang absolut TIDAK digunakan
        }
