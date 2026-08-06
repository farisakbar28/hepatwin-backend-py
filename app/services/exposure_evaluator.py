from enum import Enum
from typing import Dict, Any

from app.core.config import settings

class ExposureRiskLevel(str, Enum):
    LOW = "LOW_EXPOSURE"
    MODERATE = "MODERATE_EXPOSURE"
    HIGH = "HIGH_EXPOSURE"

class ExposureEvaluatorService:
    """
    Modul evaluasi profil paparan relatif seragam tanpa garis ambang KONSENTRASI
    TOKSIK ABSOLUT per senyawa (mis. "hepatotoksik di atas 150 mg/L") -- nilai
    semacam itu hanya tervalidasi untuk sedikit obat, sehingga PRD Bab 8.3
    menolaknya (lihat `absolute_concentration_threshold_used` di bawah).
    Berlaku konsisten untuk seluruh 1.231 senyawa is_simulatable = TRUE.

    Rujukan klinis modifikator demografis (F5, PROJECT_FUSION.md SS3.5):
      - Soejima et al. (2022) [21]: mendukung KEBERADAAN kerentanan eliminasi
        pada Usia >= 60 tahun -- BUKAN dasar nilai ambang 0.35/0.20 di bawah.
      - Ghabril et al. (2025) [17]: mendukung KEBERADAAN MASLD/perlemakan hati
        pada BMI >= 30 kg/m2 -- BUKAN dasar nilai ambang 0.35/0.20 di bawah.

    [ASUMSI DESAIN -- PENDING REVIEW FARMASI, gerbang K3] Keenam angka ambang
    (`EXPOSURE_DOSE_HIGH_MG_PER_KG`=30.0, `EXPOSURE_DOSE_MODERATE_MG_PER_KG`=10.0,
    `EXPOSURE_RATIO_HIGH_THRESHOLD`=0.40/0.35, `EXPOSURE_RATIO_MODERATE_THRESHOLD`
    =0.30/0.20, `app/core/config.py`) TIDAK bersitasi -- asumsi desain tim,
    dipertahankan apa adanya per default gerbang K3 (PROJECT_FUSION.md SS6).
    Analisis sensitivitas & temuan keterjangkauan LOW_EXPOSURE ada di
    `reports/F5_audit_exposure.md` dan `reports/F2_exposure_reachability_finding.md`.
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

        # Penyesuaian ambang dinamis (nilai dari config, lihat [ASUMSI DESAIN] di atas)
        high_threshold = (
            settings.EXPOSURE_RATIO_HIGH_THRESHOLD_VULNERABLE
            if has_vulnerability_modifier else settings.EXPOSURE_RATIO_HIGH_THRESHOLD
        )
        moderate_threshold = (
            settings.EXPOSURE_RATIO_MODERATE_THRESHOLD_VULNERABLE
            if has_vulnerability_modifier else settings.EXPOSURE_RATIO_MODERATE_THRESHOLD
        )

        # 4. Logika Evaluasi Seragam (Tanpa perbandingan terhadap ambang mg/L literatur)
        # Kriteria relatif empiris yang seragam untuk seluruh senyawa simulatable:
        if dose_per_kg >= settings.EXPOSURE_DOSE_HIGH_MG_PER_KG or cmax_auc_ratio > high_threshold:
            risk_level = ExposureRiskLevel.HIGH
            risk_score = 0.85
        elif dose_per_kg >= settings.EXPOSURE_DOSE_MODERATE_MG_PER_KG or cmax_auc_ratio > moderate_threshold:
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
            # F5 (gerbang K5): nama akurat -- sistem tidak memakai ambang KONSENTRASI
            # TOKSIK ABSOLUT per senyawa (mis. mg/L); ambang RELATIF seragam
            # (mg/kg & rasio Cmax/AUC di atas) tetap dipakai, lihat docstring kelas.
            "absolute_concentration_threshold_used": False,
            # Alias mundur -- dipertahankan agar konsumen lama (frontend/test)
            # yang sudah membaca field ini tidak patah tanpa koordinasi kontrak.
            "threshold_line_used": False,
        }
