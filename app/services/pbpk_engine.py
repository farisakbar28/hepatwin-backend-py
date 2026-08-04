import logging
import math
from typing import List, Dict, Tuple
from scipy.integrate import solve_ivp
import numpy as np

logger = logging.getLogger(__name__)

class PBPKEngine:
    """
    Mesin Farmakokinetika Mekanistik (PBPK 4-Kompartemen & Penskalaan Alometrik).
    Referensi: PRD v2.0 Bab 8.2 (Brown et al., Deurenberg et al., Soejima et al.).
    """
    
    def __init__(self):
        logger.info("PBPKEngine initialized.")

    def calculate_allometric_parameters(
        self, 
        usia: int, 
        jenis_kelamin: str, 
        berat_badan_kg: float, 
        tinggi_badan_cm: float
    ) -> Dict[str, float]:
        """
        Kovariat Pasien -> Penskalaan Alometrik Deterministik:
        1. BMI = Berat / (Tinggi/100)^2
        2. V_L = 0.025 * Berat (Volume Hati)
        3. %BF = 1.20 * BMI + 0.23 * Usia - 10.8 * Sex - 5.4 (Deurenberg et al.)
        4. Q_L = Baseline * [1 - 0.008 * (Usia - 40)] jika Usia >= 40 (Soejima et al.)
        5. Reduksi Klirens ~20% jika BMI >= 30 (MASLD/Obesitas)
        """
        tinggi_m = tinggi_badan_cm / 100.0
        bmi = berat_badan_kg / (tinggi_m ** 2)
        
        # Volume Anatomi (L)
        v_l = 0.025 * berat_badan_kg # 2.5% dari berat badan
        v_p = 0.05 * berat_badan_kg  # Plasma ~5%
        v_k = 0.004 * berat_badan_kg # Ginjal ~0.4%
        v_r = 0.60 * berat_badan_kg  # Jaringan sisa ~60%
        
        # Laju Aliran Darah Hepatik Q_L (L/jam)
        q_l_baseline = 90.0 # L/jam baseline dewasa
        if usia >= 40:
            q_l = q_l_baseline * (1.0 - 0.008 * (usia - 40))
        else:
            q_l = q_l_baseline
            
        q_k = 70.0 # L/jam aliran darah ginjal
        q_r = 150.0 # L/jam sisa jaringan
        
        # Klirens Metabolisme Hepatik (L/jam)
        cl_metab = 20.0
        if bmi >= 30.0:
            cl_metab *= 0.8 # Reduksi 20% pada obesitas (BMI >= 30)
            
        cl_renal = 5.0 # L/jam
        
        # Koefisien Partisi Jaringan-Plasma (K_p)
        kp_l = 1.5
        kp_k = 1.2
        kp_r = 1.0
        
        return {
            "bmi": round(bmi, 2),
            "v_p": v_p,
            "v_l": v_l,
            "v_k": v_k,
            "v_r": v_r,
            "q_l": q_l,
            "q_k": q_k,
            "q_r": q_r,
            "cl_metab": cl_metab,
            "cl_renal": cl_renal,
            "kp_l": kp_l,
            "kp_k": kp_k,
            "kp_r": kp_r,
        }

    def _pbpk_ode(self, t: float, y: List[float], params: Dict[str, float]) -> List[float]:
        """
        Sistem ODE PBPK 4-Kompartemen:
        y = [C_P, C_L, C_K, C_R]
        """
        C_P, C_L, C_K, C_R = y
        
        V_P = params["v_p"]
        V_L = params["v_l"]
        V_K = params["v_k"]
        V_R = params["v_r"]
        
        Q_L = params["q_l"]
        Q_K = params["q_k"]
        Q_R = params["q_r"]
        
        Cl_metab = params["cl_metab"]
        Cl_renal = params["cl_renal"]
        
        K_PL = params["kp_l"]
        K_PK = params["kp_k"]
        K_PR = params["kp_r"]
        
        # dC_P/dt
        dCP_dt = (1.0 / V_P) * (
            Q_L * (C_L / K_PL) + Q_K * (C_K / K_PK) + Q_R * (C_R / K_PR) - (Q_L + Q_K + Q_R) * C_P
        )
        
        # dC_L/dt (Hati)
        dCL_dt = (1.0 / V_L) * (
            Q_L * (C_P - C_L / K_PL) - Cl_metab * (C_L / K_PL)
        )
        
        # dC_K/dt (Ginjal)
        dCK_dt = (1.0 / V_K) * (
            Q_K * (C_P - C_K / K_PK) - Cl_renal * (C_K / K_PK)
        )
        
        # dC_R/dt (Perifer)
        dCR_dt = (1.0 / V_R) * (
            Q_R * (C_P - C_R / K_PR)
        )
        
        return [dCP_dt, dCL_dt, dCK_dt, dCR_dt]

    def simulate(
        self, 
        dosis_mg: float, 
        usia: int, 
        jenis_kelamin: str, 
        berat_badan_kg: float, 
        tinggi_badan_cm: float,
        duration_hours: float = 24.0,
        step_hours: float = 0.5
    ) -> Tuple[List[Dict[str, float]], float, float]:
        """
        Menjalankan solver solve_ivp RK45 untuk menyimulasikan konsentrasi C_hati(t) & C_plasma(t).
        Mengembalikan: (time_series, cmax_hati, auc_hati)
        """
        params = self.calculate_allometric_parameters(usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm)
        
        # Dosis bolus masuk ke plasma C_P(0) = Dosis / V_P
        c_p0 = dosis_mg / params["v_p"]
        y0 = [c_p0, 0.0, 0.0, 0.0]
        
        t_eval = np.arange(0, duration_hours + step_hours, step_hours)
        
        sol = solve_ivp(
            fun=self._pbpk_ode,
            t_span=(0, duration_hours),
            y0=y0,
            t_eval=t_eval,
            method='RK45',
            args=(params,)
        )
        
        time_series = []
        cmax_hati = 0.0
        auc_hati = 0.0
        
        if sol.success:
            c_p_arr = sol.y[0]
            c_l_arr = sol.y[1]
            
            cmax_hati = float(np.max(c_l_arr))
            auc_hati = float(np.trapezoid(c_l_arr, sol.t))
            
            for t, cp, cl in zip(sol.t, c_p_arr, c_l_arr):
                time_series.append({
                    "time": round(float(t), 2),
                    "c_plasma": max(0.0, round(float(cp), 4)),
                    "c_hati": max(0.0, round(float(cl), 4))
                })
                
        return time_series, round(cmax_hati, 4), round(auc_hati, 4)
