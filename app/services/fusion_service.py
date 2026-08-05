from typing import Tuple
from app.services.exposure_evaluator import ExposureRiskLevel

class FusionService:
    """
    Lapisan Fusi Rule-Based (Backend Fusi AI + PBPK).
    Menentukan warna WebGL dan kecepatan kedip hotspot berdasarkan fusi 
    Probabilitas AI (GATNN-DNN) dan Metrik Paparan Relatif (Cmax/AUC).
    Referensi: PRD v2.0 Bab 6.3 dan Bab 8.3
    """
    @staticmethod
    def determine_visual_status(
        dili_score: float,
        exposure_category: str
    ) -> Tuple[str, str, str]:
        """
        Mengembalikan tuple (risk_level, visual_color, blinking_speed)
        Berdasarkan matriks keputusan SOT Bab 8.3:
        - HIJAU (STABLE) -> P_DILI < 30% dan LOW_EXPOSURE
        - KUNING (SLOW) -> 30% <= P_DILI <= 70% atau MODERATE_EXPOSURE
        - MERAH (FAST) -> P_DILI > 70% atau HIGH_EXPOSURE
        """
        # Default
        risk_level = "low"
        visual_color = "green"
        blinking_speed = "none"

        # Aturan berjenjang (dari keparahan tertinggi ke terendah)
        if dili_score > 0.70 or exposure_category == ExposureRiskLevel.HIGH.value:
            risk_level = "high"
            visual_color = "red"
            blinking_speed = "fast"
        elif dili_score >= 0.30 or exposure_category == ExposureRiskLevel.MODERATE.value:
            risk_level = "medium"
            visual_color = "yellow"
            blinking_speed = "slow"
            
        return risk_level, visual_color, blinking_speed
