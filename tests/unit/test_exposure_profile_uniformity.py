import pytest
from app.services.exposure_evaluator import ExposureEvaluatorService, ExposureRiskLevel

def test_zero_absolute_threshold_dependence():
    """
    Membuktikan bahwa fungsi evaluasi tidak pernah membutuhkan atau mengecek
    kolom threshold_available, serta mengembalikan threshold_line_used = False.
    """
    result = ExposureEvaluatorService.evaluate_relative_exposure(
        cmax=10.0,
        auc=50.0,
        age=30,
        bmi=22.0,
        dose_mg=500.0,
        weight_kg=70.0
    )
    
    assert "threshold_line_used" in result
    assert result["threshold_line_used"] is False
    assert result["risk_level"] in [e.value for e in ExposureRiskLevel]

def test_uniform_evaluation_across_compounds():
    """
    Membuktikan bahwa evaluasi seragam untuk senyawa apapun (Acetaminophen, Ibuprofen, dll).
    Karena ExposureEvaluatorService.evaluate_relative_exposure() TIDAK menerima nama senyawa
    atau ID senyawa, maka secara matematis tidak mungkin ada aturan hardcode untuk
    Acetaminophen (Nomogram Rumack-Matthew).
    Keduanya dievaluasi murni dari angka PBPK dan demografi.
    """
    # Acetaminophen simulation
    result_acetaminophen = ExposureEvaluatorService.evaluate_relative_exposure(
        cmax=100.0,
        auc=400.0,
        age=25,
        bmi=24.0,
        dose_mg=4000.0, # Overdosis
        weight_kg=60.0
    )
    
    # Ibuprofen simulation (with identical parameters to Acetaminophen for test sake)
    result_ibuprofen = ExposureEvaluatorService.evaluate_relative_exposure(
        cmax=100.0,
        auc=400.0,
        age=25,
        bmi=24.0,
        dose_mg=4000.0,
        weight_kg=60.0
    )
    
    assert result_acetaminophen["risk_level"] == result_ibuprofen["risk_level"]
    assert result_acetaminophen["relative_risk_score"] == result_ibuprofen["relative_risk_score"]
    assert result_acetaminophen["dose_per_kg"] == 66.67
    assert result_acetaminophen["risk_level"] == ExposureRiskLevel.HIGH.value

def test_vulnerability_modifiers_age_and_bmi():
    """
    Membuktikan bahwa pada dosis/rasio yang sama, pasien berusia lanjut (>= 60)
    atau ber-BMI obesitas (>= 30) mendapatkan tingkat risiko yang lebih tinggi.
    """
    # Baseline dewasa muda sehat (cmax_auc = 0.28, dose = 7.14) -> MODERATE threshold is 0.30 -> LOW
    result_healthy = ExposureEvaluatorService.evaluate_relative_exposure(
        cmax=14.0,
        auc=50.0, 
        age=30,
        bmi=24.0,
        dose_mg=500.0, 
        weight_kg=70.0
    )
    assert result_healthy["has_vulnerability_modifier"] is False
    assert result_healthy["risk_level"] == ExposureRiskLevel.LOW.value

    # Lansia (Usia >= 60) -> vulnerable, MODERATE threshold drops to 0.20 -> MODERATE
    result_elderly = ExposureEvaluatorService.evaluate_relative_exposure(
        cmax=14.0,
        auc=50.0,
        age=65,
        bmi=24.0,
        dose_mg=500.0,
        weight_kg=70.0
    )
    assert result_elderly["has_vulnerability_modifier"] is True
    assert result_elderly["risk_level"] == ExposureRiskLevel.MODERATE.value

    # Obesitas / MASLD (BMI >= 30) -> vulnerable, MODERATE threshold drops to 0.20 -> MODERATE
    result_obese = ExposureEvaluatorService.evaluate_relative_exposure(
        cmax=14.0,
        auc=50.0,
        age=30,
        bmi=32.0,
        dose_mg=500.0,
        weight_kg=70.0
    )
    assert result_obese["has_vulnerability_modifier"] is True
    assert result_obese["risk_level"] == ExposureRiskLevel.MODERATE.value

def test_zero_dose_elderly_is_low_exposure():
    """
    Memastikan lansia dengan dosis 0 (cmax=0, auc=0) tidak secara konyol dicap Moderate.
    """
    result = ExposureEvaluatorService.evaluate_relative_exposure(
        cmax=0.0,
        auc=0.0,
        age=65,
        bmi=24.0,
        dose_mg=0.0,
        weight_kg=70.0
    )
    assert result["has_vulnerability_modifier"] is True
    assert result["cmax_auc_ratio"] == 0.0
    assert result["dose_per_kg"] == 0.0
    assert result["risk_level"] == ExposureRiskLevel.LOW.value

def test_invalid_inputs_raise_value_error():
    """
    Memastikan weight_kg = 0 memicu ValueError, begitu juga nilai negatif.
    """
    with pytest.raises(ValueError, match="Parameter fisik/farmakokinetik tidak valid"):
        ExposureEvaluatorService.evaluate_relative_exposure(
            cmax=10.0,
            auc=50.0,
            age=30,
            bmi=24.0,
            dose_mg=500.0,
            weight_kg=0.0 # Error!
        )
    with pytest.raises(ValueError, match="Parameter fisik/farmakokinetik tidak valid"):
        ExposureEvaluatorService.evaluate_relative_exposure(
            cmax=-10.0,
            auc=50.0,
            age=30,
            bmi=24.0,
            dose_mg=500.0,
            weight_kg=70.0 # Error!
        )
