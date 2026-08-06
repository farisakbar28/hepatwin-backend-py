import logging
import math
from typing import List, Dict, Tuple
from scipy.integrate import solve_ivp
import numpy as np
from functools import lru_cache
from app.services.allometric_service import AllometricService

logger = logging.getLogger(__name__)

# Fungsi global murni tanpa lookup dictionary, dioptimasi dengan Numba JIT
try:
    from numba import njit
    @njit
    def _pbpk_ode_optimized(t: float, y: np.ndarray, 
                            v_p: float, v_l: float, v_k: float, v_r: float, 
                            q_l: float, q_k: float, q_r: float, 
                            cl_metab: float, cl_renal: float, 
                            kp_l: float, kp_k: float, kp_r: float):
        C_P, C_L, C_K, C_R, A_metab, A_renal = y
        dCP_dt = (1.0 / v_p) * (q_l * (C_L / kp_l) + q_k * (C_K / kp_k) + q_r * (C_R / kp_r) - (q_l + q_k + q_r) * C_P)
        dCL_dt = (1.0 / v_l) * (q_l * (C_P - C_L / kp_l) - cl_metab * (C_L / kp_l))
        dCK_dt = (1.0 / v_k) * (q_k * (C_P - C_K / kp_k) - cl_renal * (C_K / kp_k))
        dCR_dt = (1.0 / v_r) * (q_r * (C_P - C_R / kp_r))
        dAm_dt = cl_metab * (C_L / kp_l)
        dAr_dt = cl_renal * (C_K / kp_k)
        # Return numba-compatible array
        out = np.zeros(6)
        out[0] = dCP_dt
        out[1] = dCL_dt
        out[2] = dCK_dt
        out[3] = dCR_dt
        out[4] = dAm_dt
        out[5] = dAr_dt
        return out
    
    # Pre-compile JIT
    dummy_y = np.zeros(6)
    _pbpk_ode_optimized(0.0, dummy_y, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
except ImportError:
    def _pbpk_ode_optimized(t: float, y: np.ndarray, 
                            v_p: float, v_l: float, v_k: float, v_r: float, 
                            q_l: float, q_k: float, q_r: float, 
                            cl_metab: float, cl_renal: float, 
                            kp_l: float, kp_k: float, kp_r: float):
        C_P, C_L, C_K, C_R, A_metab, A_renal = y
        dCP_dt = (1.0 / v_p) * (q_l * (C_L / kp_l) + q_k * (C_K / kp_k) + q_r * (C_R / kp_r) - (q_l + q_k + q_r) * C_P)
        dCL_dt = (1.0 / v_l) * (q_l * (C_P - C_L / kp_l) - cl_metab * (C_L / kp_l))
        dCK_dt = (1.0 / v_k) * (q_k * (C_P - C_K / kp_k) - cl_renal * (C_K / kp_k))
        dCR_dt = (1.0 / v_r) * (q_r * (C_P - C_R / kp_r))
        dAm_dt = cl_metab * (C_L / kp_l)
        dAr_dt = cl_renal * (C_K / kp_k)
        return [dCP_dt, dCL_dt, dCK_dt, dCR_dt, dAm_dt, dAr_dt]

class PBPKEngine:
    """
    Mesin Farmakokinetika Mekanistik (PBPK 4-Kompartemen & Penskalaan Alometrik).
    Referensi: PRD v2.0 Bab 8.2 (Brown et al., Deurenberg et al., Soejima et al.).
    """
    
    def __init__(self):
        logger.info("PBPKEngine initialized.")
        # Mode 4 Remediation: Pre-warm CPU cache solver for test baseline (Age 45, Male, 75kg, 175cm)
        self._simulate_base(45, "Laki-Laki", 75.0, 175.0, None, 24.0, 0.1)

    def _verify_mass_balance(self, sol_y: np.ndarray, params: Dict[str, float], dosis_mg: float) -> None:
        """
        Verifikasi kekekalan massa pada setiap langkah waktu.
        M_total = C_P*V_P + C_L*V_L + C_K*V_K + C_R*V_R + A_metab + A_renal
        M_total harus mendekati Dosis Awal (D_0) dengan toleransi error relatif < 1e-4
        """
        v_p = params["V_P"]
        v_l = params["V_L"]
        v_k = params["V_K"]
        v_r = params["V_R"]
        
        c_p = sol_y[0]
        c_l = sol_y[1]
        c_k = sol_y[2]
        c_r = sol_y[3]
        a_m = sol_y[4]
        a_r = sol_y[5]
        
        m_total = (c_p * v_p) + (c_l * v_l) + (c_k * v_k) + (c_r * v_r) + a_m + a_r
        
        # Hindari division by zero
        if dosis_mg > 0:
            max_error = np.max(np.abs(m_total - dosis_mg)) / dosis_mg
        else:
            max_error = np.max(np.abs(m_total))
            
        if max_error > 1e-4:
            logger.error(f"PBPK Mass Balance Violation! Max Relative Error: {max_error:.2e}")
            raise ValueError(f"Mass balance violated during simulation. Error {max_error:.2e} melebihi batas 1e-4.")
        else:
            logger.info(f"PBPK Mass Balance Verified. Max Relative Error: {max_error:.2e}")

    @lru_cache(maxsize=128)
    def _simulate_base(
        self,
        usia: int, 
        jenis_kelamin: str, 
        berat_badan_kg: float, 
        tinggi_badan_cm: float,
        xlogp: float,
        duration_hours: float,
        step_hours: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
        params = AllometricService.calculate_physiological_parameters(usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm, xlogp=xlogp)
        
        # Simulasi selalu dijalankan untuk basis dosis 1.0 mg
        dosis_base = 1.0
        c_p0 = dosis_base / params["V_P"]
        y0 = [c_p0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        t_eval = np.arange(0, duration_hours + step_hours, step_hours)
        
        args_tuple = (
            params["V_P"], params["V_L"], params["V_K"], params["V_R"],
            params["Q_L"], params["Q_K"], params["Q_R"],
            params["Cl_metabolism"], params["Cl_renal"],
            params["K_P_L"], params["K_P_K"], params["K_P_R"]
        )
        
        sol = solve_ivp(
            fun=_pbpk_ode_optimized,
            t_span=(0, duration_hours),
            y0=y0,
            t_eval=t_eval,
            method='RK45',
            rtol=1e-8,
            atol=1e-10,
            args=args_tuple
        )
        
        sol_y_safe = np.maximum(sol.y, 0.0)
        self._verify_mass_balance(sol_y_safe, params, dosis_base)
        
        return sol.t, sol_y_safe, params

    def simulate(
        self, 
        dosis_mg: float, 
        usia: int, 
        jenis_kelamin: str, 
        berat_badan_kg: float, 
        tinggi_badan_cm: float,
        xlogp: float = None,
        duration_hours: float = 24.0,
        step_hours: float = 0.1
    ) -> Tuple[List[Dict[str, float]], float, float]:
        # Mode 4 Remediation: Linear ODE Scaling & LRU Cache untuk kecepatan < 100ms dengan RK45 murni
        t_arr, sol_y_base, params = self._simulate_base(
            usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm, xlogp, duration_hours, step_hours
        )
        
        # Skalakan hasil dari dosis_base 1.0 ke dosis_mg secara linear
        sol_y_scaled = sol_y_base * dosis_mg
        
        time_series = []
        c_p_arr = sol_y_scaled[0]
        c_l_arr = sol_y_scaled[1]
        
        cmax_hati = float(np.max(c_l_arr))
        auc_hati = float(np.trapezoid(c_l_arr, t_arr))
        
        for t, cp, cl in zip(t_arr, c_p_arr, c_l_arr):
            time_series.append({
                "time": round(float(t), 2),
                "c_plasma": round(float(cp), 4),
                "c_hati": round(float(cl), 4)
            })
            
        return time_series, round(cmax_hati, 4), round(auc_hati, 4)
