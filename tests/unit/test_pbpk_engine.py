import pytest
from app.services.pbpk_engine import PBPKEngine

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
