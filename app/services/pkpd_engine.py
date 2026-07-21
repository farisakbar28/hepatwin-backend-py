import logging
import math
from typing import List, Dict
from scipy.integrate import odeint
import numpy as np

logger = logging.getLogger(__name__)

class AcetaminophenPKPDEngine:
    """
    Model Matematika PK/PD Paracetamol.
    Referensi: Bab E.4.0 Proposal (Morse et al., 2022).
    """
    F_ORAL = 0.86
    CL_SYSTEMIC = 24.0 # L/hr
    V1 = 43.5 # L
    KA = 3.47 # hr^-1
    KE = 0.55 # hr^-1
    
    # Kinetika Liver & Metabolit (Nilai pendekatan literatur)
    K_IN = 1.0 # hr^-1 (Asumsi difusi cepat)
    K_ELIM = 0.4 # hr^-1
    K_META = 0.1 # hr^-1 (Metabolisme CYP2E1 ke NAPQI)
    K_GSH = 2.0 # L/(mol*hr) (Reaksi detoksifikasi)
    GSH_INITIAL = 100.0 # mmol (Asumsi stok GSH awal)
    
    THETA_THRESHOLD = 0.3 # Rasio NAPQI/GSH pemicu nekrosis

    def __init__(self):
        logger.info("AcetaminophenPKPDEngine initialized.")

    def calculate_oral_absorption(self, dose_mg_kg: float, time_hours: float) -> float:
        """
        Hitung C_plasma(t) (closed-form dua eksponensial).
        """
        dose_total = dose_mg_kg * 70  # Asumsi bb 70kg
        ka, ke = self.KA, self.KE
        lag_time_hr = 5.3 / 60.0

        if time_hours <= lag_time_hr or (ka - ke) == 0:
            return 0.0
        
        t_eff = time_hours - lag_time_hr
        c_plasma = (self.F_ORAL * dose_total * ka / (self.V1 * (ka - ke))) * (math.exp(-ke * t_eff) - math.exp(-ka * t_eff))
        return max(0.0, c_plasma)
        
    def _pkpd_derivatives(self, y: List[float], t: float, dose_mg_kg: float) -> List[float]:
        """
        Sistem Persamaan Diferensial (ODE) untuk HepaTwin.
        y = [C_liver, NAPQI, GSH]
        """
        C_liver, NAPQI, GSH = y
        C_plasma = self.calculate_oral_absorption(dose_mg_kg, t)
        
        dC_liver_dt = self.K_IN * C_plasma - self.K_ELIM * C_liver
        
        # d[NAPQI]/dt = k_meta * C_liver - k_GSH * [GSH] * [NAPQI]
        dNAPQI_dt = self.K_META * C_liver - self.K_GSH * GSH * NAPQI
        
        # d[GSH]/dt = -k_GSH * [GSH] * [NAPQI] (Asumsi sintesis GSH de novo diabaikan selama krisis)
        dGSH_dt = -self.K_GSH * GSH * NAPQI
        
        return [dC_liver_dt, dNAPQI_dt, dGSH_dt]

    def simulate_napqi_gsh_dynamics(self, dose_mg_kg: float, max_time_hours: int = 24, step_dt: float = 0.5) -> List[Dict[str, float]]:
        """
        Integrasi numerik ODE dC_liver/dt, d[NAPQI]/dt, d[GSH]/dt.
        """
        time_series = []
        if step_dt <= 0 or max_time_hours <= 0:
            return time_series
            
        t_points = np.arange(0, max_time_hours + step_dt, step_dt)
        y0 = [0.0, 0.0, self.GSH_INITIAL] # Initial: C_liver=0, NAPQI=0, GSH=100
        
        solution = odeint(self._pkpd_derivatives, y0, t_points, args=(dose_mg_kg,))
        
        for idx, t in enumerate(t_points):
            c_plasma = self.calculate_oral_absorption(dose_mg_kg, t)
            c_liver = solution[idx, 0]
            napqi = solution[idx, 1]
            gsh = solution[idx, 2]
            
            ratio = napqi / self.GSH_INITIAL
            threshold_exceeded = bool(ratio > self.THETA_THRESHOLD)
            
            time_series.append({
                "time": round(float(t), 2),
                "concentration": round(float(c_plasma), 2), # Plasma concentration for nomogram reference
                "c_liver": round(float(c_liver), 4),
                "napqi": round(float(napqi), 4),
                "gsh": round(float(gsh), 4),
                "napqi_gsh_ratio": round(float(ratio), 4),
                "threshold_exceeded": threshold_exceeded
            })
        return time_series

    def get_nomogram_data(self, dose_mg_kg: float) -> List[Dict[str, float]]:
        data = []
        for t in [4, 8, 12, 16, 20, 24]:
            c_plasma = self.calculate_oral_absorption(dose_mg_kg, t)
            data.append({"time": t, "plasma_concentration": round(c_plasma, 2)})
        return data