import logging
import math
from typing import Any, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)


class AllometricService:
    """Convert patient covariates to PRD v2.3 PBPK Phase 1 parameters."""

    @staticmethod
    def calculate_physiological_parameters(
        age: int,
        gender: str,
        weight_kg: float,
        height_cm: float,
        base_cl_metabolism_l_hr: float | None = None,
        xlogp: float | None = None,
    ) -> Dict[str, Any]:
        if base_cl_metabolism_l_hr is None:
            base_cl_metabolism_l_hr = settings.PBPK_BASE_CL_METABOLISM_70_L_H
        AllometricService._validate_inputs(age, weight_kg, height_cm, base_cl_metabolism_l_hr)

        gender_upper = gender.strip().upper()
        if gender_upper in {"MALE", "M", "L", "LAKI-LAKI", "LAKI", "PRIA"}:
            sex_val = 1
        elif gender_upper in {"FEMALE", "F", "P", "PEREMPUAN", "WANITA"}:
            sex_val = 0
        else:
            raise ValueError("Format jenis kelamin tidak valid.")

        height_m = float(height_cm) / 100.0
        bmi = float(weight_kg) / (height_m**2)
        if age <= 15:
            body_fat_raw = 1.51 * bmi - 0.70 * age - 3.6 * sex_val + 1.4
        else:
            body_fat_raw = 1.20 * bmi + 0.23 * age - 10.8 * sex_val - 5.4
        body_fat_clamped = min(max(body_fat_raw, 3.0), 60.0)
        if not math.isclose(body_fat_raw, body_fat_clamped):
            logger.warning(
                "[PBPK BODY_FAT CLAMP] raw=%s clamped=%s age=%s",
                body_fat_raw,
                body_fat_clamped,
                age,
            )

        weight_kg = float(weight_kg)
        allometric_scale = (weight_kg / 70.0) ** 0.75
        v_plasma = settings.PBPK_PLASMA_VOLUME_FRACTION * weight_kg
        v_liver = settings.PBPK_LIVER_VOLUME_FRACTION * weight_kg
        v_kidney = settings.PBPK_KIDNEY_VOLUME_FRACTION * weight_kg
        v_remainder = max(weight_kg - v_plasma - v_liver - v_kidney, 1.0)

        q_cardiac = settings.PBPK_CARDIAC_FLOW_70_L_H * allometric_scale
        age_factor = 1.0 if age < 40 else max(0.60, 1.0 - 0.008 * (min(age, 90) - 40))
        q_liver = 0.25 * q_cardiac * age_factor
        q_kidney = 0.20 * q_cardiac
        q_remainder = max(q_cardiac - q_liver - q_kidney, 0.0)

        cl_metabolism = min(float(base_cl_metabolism_l_hr) * allometric_scale, 0.95 * q_liver)
        cl_renal = settings.PBPK_BASE_CL_RENAL_70_L_H * allometric_scale

        if xlogp is None:
            logger.warning("[FALLBACK XLogP NULL] xlogp_eff=0.0")
            xlogp_eff = 0.0
        else:
            if not math.isfinite(float(xlogp)):
                raise ValueError("XLogP harus bernilai finite atau null.")
            xlogp_eff = min(max(float(xlogp), -1.0), 7.0)
        bf_frac = min(max(body_fat_clamped / 100.0, 0.03), 0.60)
        kp_r = min(max(1.0 + bf_frac * (10 ** (0.25 * xlogp_eff)), 1.0), 10.0)

        return {
            "bmi": bmi,
            "metabolic_risk_flag": bmi >= 30.0,
            "clearance_multiplier_from_bmi": 1.0,
            "body_fat_percent_raw": body_fat_raw,
            "body_fat_percent_clamped": body_fat_clamped,
            "body_fat_pct": body_fat_clamped,
            "xlogp_eff": xlogp_eff,
            "V_P": v_plasma,
            "V_L": v_liver,
            "V_K": v_kidney,
            "V_R": v_remainder,
            "Q_C": q_cardiac,
            "Q_L": q_liver,
            "Q_K": q_kidney,
            "Q_R": q_remainder,
            "age_factor": age_factor,
            "Cl_metabolism": cl_metabolism,
            "Cl_renal": cl_renal,
            "Cl_metabolism_source": "FALLBACK_BASE_CL_MET_70",
            "Cl_renal_source": "DESIGN_FALLBACK_BASE_CL_RENAL_70",
            "K_P_L": 5.0,
            "K_P_K": 2.0,
            "K_P_R": kp_r,
        }

    @staticmethod
    def _validate_inputs(
        age: int,
        weight_kg: float,
        height_cm: float,
        base_cl_metabolism_l_hr: float,
    ) -> None:
        if isinstance(age, bool) or not isinstance(age, int) or not 0 <= age <= 100:
            raise ValueError("Usia harus berupa integer antara 0 dan 100 tahun.")
        for name, value in {
            "berat badan": weight_kg,
            "tinggi badan": height_cm,
            "base clearance metabolism": base_cl_metabolism_l_hr,
        }.items():
            if not math.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"Parameter {name} harus bernilai finite dan lebih besar dari 0.")
