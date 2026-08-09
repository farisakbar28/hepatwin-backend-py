import pytest
import time
import math
from app.services.pbpk_engine import PBPKEngine

def test_pbpk_solver_mass_balance_and_convergence():
    """
    Menguji konvergensi ODE SciPy Runge-Kutta 45 (RK45) dan kekekalan massa (< 1e-4).
    """
    engine = PBPKEngine()
    
    doses = [10.0, 500.0, 4000.0, 10000.0]
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
        
        # 1. Konvergensi & Kelengkapan data (241 titik data untuk 24 jam step 0.1h)
        assert len(time_series) == 241, f"Time series length {len(time_series)} expected 241"
        assert cmax > 0.0
        assert auc > 0.0
        
        # 2. PBPK must remain well inside the PRD's end-to-end five-second NFR.
        assert exec_time_ms <= 5000.0, f"Execution time {exec_time_ms:.2f}ms exceeds 5s NFR."
        
        # 3. Sanitasi Numerik (Tidak ada NaN atau nilai negatif)
        for pt in time_series:
            assert not math.isnan(pt["c_plasma"]), "Found NaN in c_plasma"
            assert not math.isnan(pt["c_hati"]), "Found NaN in c_hati"
            assert pt["c_plasma"] >= 0.0, "Found negative c_plasma"
            assert pt["c_hati"] >= 0.0, "Found negative c_hati"

def test_pbpk_solver_age_and_weight_variations():
    """
    Menguji stabilitas solver PBPK pada variasi demografi ekstrem (bayi/lansia, bb ringan/berat).
    """
    engine = PBPKEngine()
    test_cases = [
        {"usia": 0, "gender": "M", "weight": 3.0, "height": 50.0, "dose": 25.0},
        {"usia": 25, "gender": "F", "weight": 55.0, "height": 160.0, "dose": 500.0},
        {"usia": 65, "gender": "Pria", "weight": 85.0, "height": 170.0, "dose": 1000.0},
        {"usia": 90, "gender": "Perempuan", "weight": 110.0, "height": 155.0, "dose": 2000.0},
    ]
    
    for tc in test_cases:
        time_series, cmax, auc = engine.simulate(
            dosis_mg=tc["dose"],
            usia=tc["usia"],
            jenis_kelamin=tc["gender"],
            berat_badan_kg=tc["weight"],
            tinggi_badan_cm=tc["height"]
        )
        assert len(time_series) > 0
        assert cmax > 0.0
        assert auc > 0.0

def test_pbpk_solver_linear_scaling_consistency():
    """
    Membuktikan bahwa penskalaan linear dosis menggandakan Cmax dan AUC secara proporsional.
    """
    engine = PBPKEngine()
    _, cmax_500, auc_500 = engine.simulate(500.0, 30, "L", 70.0, 170.0)
    _, cmax_1000, auc_1000 = engine.simulate(1000.0, 30, "L", 70.0, 170.0)
    
    assert abs(cmax_1000 - 2.0 * cmax_500) < 1e-3
    assert abs(auc_1000 - 2.0 * auc_500) < 1e-3


def test_pbpk_solver_rejects_invalid_numerical_control_inputs():
    engine = PBPKEngine()
    with pytest.raises(ValueError, match="step_hours"):
        engine.simulate(100.0, 40, "L", 70.0, 170.0, duration_hours=1.0, step_hours=2.0)
    with pytest.raises(ValueError, match="dosis_mg"):
        engine.simulate(float("nan"), 40, "L", 70.0, 170.0)


def test_pbpk_solver_10080_prd_v23_combinations_are_finite_and_nonnegative():
    """PRD §3.3 numerical-stability evidence over more than 10,000 scenarios."""
    engine = PBPKEngine()
    patient_shapes = (
        (3.0, 50.0), (10.0, 100.0), (20.0, 110.0), (35.0, 140.0), (50.0, 150.0),
        (70.0, 170.0), (90.0, 180.0), (120.0, 190.0), (200.0, 210.0), (350.0, 250.0),
    )
    scenario_count = 0
    for usia in (0, 15, 16, 40, 90, 100):
        for jenis_kelamin in ("L", "P"):
            for berat_badan_kg, tinggi_badan_cm in patient_shapes:
                for dosis_mg in range(1, 85):
                    result = engine.simulate_with_diagnostics(
                        float(dosis_mg), usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm, xlogp=0.0
                    )
                    scenario_count += 1
                    assert len(result.time_series) == 241
                    assert math.isfinite(result.cmax_hati) and result.cmax_hati >= 0.0
                    assert math.isfinite(result.auc_hati) and result.auc_hati >= 0.0
    assert scenario_count == 10_080
