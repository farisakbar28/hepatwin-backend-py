from typing import Tuple
from app.services.exposure_evaluator import ExposureRiskLevel

# [KEPUTUSAN AI -- PENDING K2]: Threshold distribusional pasca-kalibrasi
FUSION_AI_T_LOW = 0.30
FUSION_AI_T_HIGH = 0.70

class FusionService:
    """
    Lapisan Fusi Rule-Based (Backend Fusi AI + PBPK).
    Menentukan warna WebGL dan kecepatan kedip hotspot berdasarkan fusi 
    Probabilitas AI (GATNN-DNN) dan Metrik Paparan Relatif (Cmax/AUC).
    Referensi: PRD v2.3 Bab 8.3 (Threshold provisional 0.30/0.70)
    """
    @staticmethod
    def determine_visual_status(
        dili_score: float,
        exposure_category: str
    ) -> Tuple[str, str, str]:
        """
        Mengembalikan tuple (risk_level, visual_color, blinking_speed)
        Berdasarkan matriks keputusan SOT Bab 8.3:
        - HIJAU (STABLE) -> P_DILI < T_LOW dan LOW_EXPOSURE
        - KUNING (SLOW) -> T_LOW <= P_DILI <= T_HIGH atau MODERATE_EXPOSURE
        - MERAH (FAST) -> P_DILI > T_HIGH atau HIGH_EXPOSURE
        """
        # Default
        risk_level = "low"
        visual_color = "green"
        blinking_speed = "none"

        # Aturan berjenjang (dari keparahan tertinggi ke terendah)
        if dili_score > FUSION_AI_T_HIGH or exposure_category == ExposureRiskLevel.HIGH.value:
            risk_level = "high"
            visual_color = "red"
            blinking_speed = "fast"
        elif dili_score >= FUSION_AI_T_LOW or exposure_category == ExposureRiskLevel.MODERATE.value:
            risk_level = "medium"
            visual_color = "yellow"
            blinking_speed = "slow"
            
        return risk_level, visual_color, blinking_speed
