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

