import pytest
import time
import numpy as np
import math
from app.services.pbpk_engine import PBPKEngine

def test_ode_mass_balance_and_convergence():
    engine = PBPKEngine()
    
    doses = [10.0, 500.0, 10000.0]
    for dosis in doses:
        start_time = time.perf_counter()
        time_series, cmax, auc = engine.simulate(
            dosis_mg=dosis,
            usia=45,
            jenis_kelamin="Laki-Laki",
            berat_badan_kg=75.0,
            tinggi_badan_cm=175.0
        )
        end_time = time.perf_counter()
        
        exec_time_ms = (end_time - start_time) * 1000.0
        
        # Test 2: Convergence (if it didn't raise ValueError, mass balance passed)
        assert len(time_series) > 0, "Simulation failed to converge or return data."
        
        # Test 6: Speed <= 100ms (Solved via ODE Linear Scaling & Cache)
        assert exec_time_ms <= 100.0, f"Execution time {exec_time_ms:.2f}ms exceeds 100ms limit."
        
        # Test 6: No Negative or NaN values
        for pt in time_series:
            assert not math.isnan(pt["c_plasma"])
            assert not math.isnan(pt["c_hati"])
            assert pt["c_plasma"] >= 0.0
            assert pt["c_hati"] >= 0.0

def test_allometric_scaling_age_and_bmi():
    engine = PBPKEngine()
    
    # Baseline: Age 30, BMI 22.8 (70kg, 175cm)
    base_params = engine.calculate_allometric_parameters(30, "Laki-Laki", 70.0, 175.0)
    
    # Age >= 40: Age 50, BMI 22.8
    age_params = engine.calculate_allometric_parameters(50, "Laki-Laki", 70.0, 175.0)
    
    # BMI >= 30: Age 30, BMI 31.0 (95kg, 175cm)
    obese_params = engine.calculate_allometric_parameters(30, "Laki-Laki", 95.0, 175.0)
    
    # 1. Q_L baseline is 90.0 for age < 40
    assert base_params["q_l"] == 90.0
    
    # 2. Q_L age 50 = 90.0 * (1 - 0.008 * (50-40)) = 90.0 * 0.92 = 82.8
    assert math.isclose(age_params["q_l"], 82.8, rel_tol=1e-5), f"Expected 82.8, got {age_params['q_l']}"
    
    # 3. Cl_metab baseline = 20.0
    assert base_params["cl_metab"] == 20.0
    
    # 4. Cl_metab obese = 20.0 * 0.8 = 16.0
    assert obese_params["cl_metab"] == 16.0
    
def test_allometric_bf_percent():
    engine = PBPKEngine()
    
    params = engine.calculate_allometric_parameters(45, "Laki-Laki", 75.0, 175.0)
    assert "bf_percent" in params
    assert params["bf_percent"] > 0.0
    
    # Manually check: BMI = 75 / (1.75^2) = 24.4898
    # %BF = 1.20 * 24.4898 + 0.23 * 45 - 10.8 * 1.0 - 5.4 = 29.38776 + 10.35 - 10.8 - 5.4 = 23.53776
    assert math.isclose(params["bf_percent"], 23.54, rel_tol=1e-2), f"Expected ~23.54, got {params['bf_percent']}"
