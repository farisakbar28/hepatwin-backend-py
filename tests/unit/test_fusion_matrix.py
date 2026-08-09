"""F8 -- Test suite matriks fusi 3x3 (D9). Murni unit test, tidak butuh DB/model
AI/PBPK -- FusionService.determine_visual_status() hanya butuh (dili_score,
exposure_category), bebas dari sisi lain sistem.
"""
import ast
from pathlib import Path

import pytest

from app.services.exposure_evaluator import ExposureRiskLevel
from app.services.fusion_service import AiRiskBand, FusionService

T_LOW = 0.5458
T_HIGH = 0.6866

# Sembilan sel matriks (PRD Bab 8.3 / PROJECT_FUSION.md SS4.1) -- setiap sel
# hasil (risk_level, visual_color, blinking_speed) diverifikasi eksplisit,
# tidak ada yang boleh tak-teruji.
MATRIX_CASES = [
    (T_LOW - 0.01, ExposureRiskLevel.LOW.value, ("low", "green", "none"), "AI_LOW x LOW_EXPOSURE"),
    (T_LOW - 0.01, ExposureRiskLevel.MODERATE.value, ("medium", "yellow", "slow"), "AI_LOW x MODERATE_EXPOSURE"),
    (T_LOW - 0.01, ExposureRiskLevel.HIGH.value, ("high", "red", "fast"), "AI_LOW x HIGH_EXPOSURE"),
    ((T_LOW + T_HIGH) / 2, ExposureRiskLevel.LOW.value, ("medium", "yellow", "slow"), "AI_MID x LOW_EXPOSURE"),
    ((T_LOW + T_HIGH) / 2, ExposureRiskLevel.MODERATE.value, ("medium", "yellow", "slow"), "AI_MID x MODERATE_EXPOSURE"),
    ((T_LOW + T_HIGH) / 2, ExposureRiskLevel.HIGH.value, ("high", "red", "fast"), "AI_MID x HIGH_EXPOSURE"),
    (T_HIGH + 0.01, ExposureRiskLevel.LOW.value, ("high", "red", "fast"), "AI_HIGH x LOW_EXPOSURE"),
    (T_HIGH + 0.01, ExposureRiskLevel.MODERATE.value, ("high", "red", "fast"), "AI_HIGH x MODERATE_EXPOSURE"),
    (T_HIGH + 0.01, ExposureRiskLevel.HIGH.value, ("high", "red", "fast"), "AI_HIGH x HIGH_EXPOSURE"),
]


@pytest.mark.parametrize("dili_score,exposure_category,expected,fusion_reason", MATRIX_CASES, ids=[c[3] for c in MATRIX_CASES])
def test_matrix_cell_explicit(dili_score, exposure_category, expected, fusion_reason):
    """Test #1 (F8): seluruh 9 sel matriks tercakup, tidak ada yang tak tercapai."""
    result = FusionService.determine_visual_status(dili_score, exposure_category)
    assert (result.risk_level, result.visual_color, result.blinking_speed) == expected
    assert result.fusion_reason == fusion_reason


def test_matrix_covers_exactly_nine_cells():
    assert len(MATRIX_CASES) == 9
    assert len({c[3] for c in MATRIX_CASES}) == 9


def test_ai_low_x_low_exposure_is_green():
    """Test #2 (F8): memperbaiki SS3.1 -- hijau kini tercapai secara struktural."""
    result = FusionService.determine_visual_status(T_LOW - 0.01, ExposureRiskLevel.LOW.value)
    assert result.visual_color == "green"
    assert result.risk_level == "low"
    assert result.blinking_speed == "none"


def test_ai_low_x_moderate_differs_from_ai_low_x_low():
    """Test #3 (F8): memperbaiki SS3.2 -- MODERATE_EXPOSURE kini bermakna,
    berbeda dari LOW_EXPOSURE pada AI band yang sama."""
    green = FusionService.determine_visual_status(T_LOW - 0.01, ExposureRiskLevel.LOW.value)
    yellow = FusionService.determine_visual_status(T_LOW - 0.01, ExposureRiskLevel.MODERATE.value)
    assert green.visual_color != yellow.visual_color
    assert (green.risk_level, green.visual_color, green.blinking_speed) != (
        yellow.risk_level, yellow.visual_color, yellow.blinking_speed
    )


def test_classify_ai_band_boundaries():
    assert FusionService.classify_ai_band(T_LOW - 0.0001) == AiRiskBand.AI_LOW
    assert FusionService.classify_ai_band(T_LOW) == AiRiskBand.AI_MID  # < strict, T_low sendiri masuk AI_MID
    assert FusionService.classify_ai_band(T_HIGH) == AiRiskBand.AI_MID  # > strict, T_high sendiri masuk AI_MID
    assert FusionService.classify_ai_band(T_HIGH + 0.0001) == AiRiskBand.AI_HIGH


def test_fusion_service_has_no_ml_imports():
    """Test #13 (F8): D9 mensyaratkan fusi 100% rule-based -- tidak ada impor
    pustaka ML apa pun di fusion_service.py (diverifikasi lewat parsing AST,
    bukan sekadar substring, supaya tidak salah tangkap komentar/docstring)."""
    source_path = Path(__file__).resolve().parent.parent.parent / "app" / "services" / "fusion_service.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    banned_prefixes = ("torch", "sklearn", "tensorflow", "keras", "xgboost", "lightgbm")
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)
    offending = [m for m in imported_modules if m.startswith(banned_prefixes)]
    assert not offending, f"fusion_service.py mengimpor pustaka ML: {offending}"
