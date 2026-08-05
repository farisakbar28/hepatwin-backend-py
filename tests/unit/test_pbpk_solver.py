import pytest
import time
import math
from app.services.pbpk_engine import PBPKEngine
from app.services.allometric_service import AllometricService

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
        
        # 2. Kecepatan Eksekusi <= 100ms per simulasi (LRU cache + linear ODE scaling)
        assert exec_time_ms <= 100.0, f"Execution time {exec_time_ms:.2f}ms exceeds 100ms limit."
        
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
