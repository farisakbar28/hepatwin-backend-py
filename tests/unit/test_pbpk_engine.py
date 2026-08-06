import json
from pathlib import Path

import pytest
from app.services.pbpk_engine import PBPKEngine
from app.services.exposure_evaluator import ExposureEvaluatorService

def test_pbpk_engine_simulation_mass_balance():
    engine = PBPKEngine()
    
    dosis_mg = 500.0
    usia = 45
    jenis_kelamin = "Laki-Laki"
    berat_badan_kg = 75.0
    tinggi_badan_cm = 175.0
    
    # Simulate will automatically verify mass balance (raising error if fails)
    time_series, cmax, auc = engine.simulate(
        dosis_mg=dosis_mg,
        usia=usia,
        jenis_kelamin=jenis_kelamin,
        berat_badan_kg=berat_badan_kg,
        tinggi_badan_cm=tinggi_badan_cm
    )
    
    assert len(time_series) > 0
    assert cmax > 0.0
    assert auc > 0.0
    
    # Check that %BF is correctly calculated in params
    from app.services.allometric_service import AllometricService
    params = AllometricService.calculate_physiological_parameters(usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm)
    assert "body_fat_pct" in params
    assert params["body_fat_pct"] > 0


def test_prd_regression_apap_10500mg_has_higher_exposure_index_than_ibuprofen_400mg():
    fixture_path = Path(__file__).parents[1] / "fixtures" / "pbpk_regression_v2_3.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    patient = fixture["patient"]
    engine = PBPKEngine()

    apap = fixture["acetaminophen"]
    ibu = fixture["ibuprofen"]
    apap_result = engine.simulate_with_diagnostics(**patient, dosis_mg=apap["dosis_mg"], xlogp=apap["xlogp"])
    ibu_result = engine.simulate_with_diagnostics(**patient, dosis_mg=ibu["dosis_mg"], xlogp=ibu["xlogp"])
    apap_exposure = ExposureEvaluatorService.evaluate_relative_exposure(apap_result.cmax_hati, apap_result.auc_hati)
    ibu_exposure = ExposureEvaluatorService.evaluate_relative_exposure(ibu_result.cmax_hati, ibu_result.auc_hati)

    assert apap_exposure["exposure_index"] > ibu_exposure["exposure_index"]
    assert apap_exposure["shape_ratio_h_inv"] == pytest.approx(apap_result.cmax_hati / apap_result.auc_hati)
