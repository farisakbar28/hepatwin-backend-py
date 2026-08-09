from enum import Enum
from typing import Dict, NamedTuple, Tuple

from app.core.config import settings
from app.services.exposure_evaluator import ExposureRiskLevel


class AiRiskBand(str, Enum):
    """Band dili_score terkalibrasi, ambang dari `settings.FUSION_AI_T_LOW`/
    `FUSION_AI_T_HIGH` (F2, gerbang K2) -- BUKAN 0.30/0.70 tetap seperti versi
    lama, karena rentang keluaran kalibrator terkunci di [~0.4337, ~0.7747]
    (PROJECT_FUSION.md SS3.1)."""

    AI_LOW = "AI_LOW"
    AI_MID = "AI_MID"
    AI_HIGH = "AI_HIGH"


class FusionResult(NamedTuple):
    risk_level: str
    visual_color: str
    blinking_speed: str
    fusion_reason: str


# Matriks 3x3 eksplisit (PROJECT_FUSION.md SS4.1, PRD Bab 8.3) -- menggantikan
# rantai `if/elif ... or ...` lama yang membuat cabang hijau & MODERATE_EXPOSURE
# jadi kode mati (SS3.1, SS3.2). Seluruh 9 sel terlihat, tidak ada yang bisa
# tersembunyi tak-terjangkau secara struktural.
_MATRIX: Dict[Tuple[AiRiskBand, str], Tuple[str, str, str]] = {
    (AiRiskBand.AI_LOW, ExposureRiskLevel.LOW.value): ("low", "green", "none"),
    (AiRiskBand.AI_LOW, ExposureRiskLevel.MODERATE.value): ("medium", "yellow", "slow"),
    (AiRiskBand.AI_LOW, ExposureRiskLevel.HIGH.value): ("high", "red", "fast"),
    (AiRiskBand.AI_MID, ExposureRiskLevel.LOW.value): ("medium", "yellow", "slow"),
    (AiRiskBand.AI_MID, ExposureRiskLevel.MODERATE.value): ("medium", "yellow", "slow"),
    (AiRiskBand.AI_MID, ExposureRiskLevel.HIGH.value): ("high", "red", "fast"),
    (AiRiskBand.AI_HIGH, ExposureRiskLevel.LOW.value): ("high", "red", "fast"),
    (AiRiskBand.AI_HIGH, ExposureRiskLevel.MODERATE.value): ("high", "red", "fast"),
    (AiRiskBand.AI_HIGH, ExposureRiskLevel.HIGH.value): ("high", "red", "fast"),
}


class FusionService:
    """
    Lapisan Fusi Rule-Based (Backend Fusi AI + PBPK).
    Menentukan warna WebGL dan kecepatan kedip hotspot berdasarkan fusi
    Probabilitas AI (GATNN-DNN, band AI_LOW/AI_MID/AI_HIGH) dan Metrik Paparan
    Relatif PBPK (LOW/MODERATE/HIGH_EXPOSURE), murni rule-based (TIDAK ADA
    machine learning atau pembobotan yang dipelajari -- syarat eksplisit D9).
    Referensi: PRD v2.0 Bab 6.3 dan Bab 8.3; PROJECT_FUSION.md SS4.1 (F3).
    """

    @staticmethod
    def classify_ai_band(dili_score: float) -> AiRiskBand:
        if dili_score < settings.FUSION_AI_T_LOW:
            return AiRiskBand.AI_LOW
        if dili_score > settings.FUSION_AI_T_HIGH:
            return AiRiskBand.AI_HIGH
        return AiRiskBand.AI_MID

    @staticmethod
    def determine_visual_status(dili_score: float, exposure_category: str) -> FusionResult:
        """
        Mengembalikan `FusionResult(risk_level, visual_color, blinking_speed, fusion_reason)`
        lewat lookup matriks 3x3 eksplisit -- setiap sel bisa diaudit langsung,
        tidak ada kondisi `or` yang membuat satu sisi selalu menang.
        """
        ai_band = FusionService.classify_ai_band(dili_score)
        risk_level, visual_color, blinking_speed = _MATRIX[(ai_band, exposure_category)]
        fusion_reason = f"{ai_band.value} x {exposure_category}"
        return FusionResult(risk_level, visual_color, blinking_speed, fusion_reason)
