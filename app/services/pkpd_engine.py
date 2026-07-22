import logging
import math
from dataclasses import dataclass
from typing import List, Dict, Optional
from scipy.integrate import odeint
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PDConstant:
    """Konstanta ilmiah bergerbang validasi Farmasi. Lihat PRD §13 item #1."""

    value: Optional[float]
    unit: str
    citation: Optional[str] = None
    validated_by_pharmacy: bool = False


class AcetaminophenPKPDEngine:
    """
    Model Matematika PK/PD Paracetamol.
    Referensi absorpsi oral: Morse et al., 2022 (PRD §8.1 langkah 1).
    """
    # Parameter absorpsi oral — sudah bersumber dari Morse et al. (2022),
    # PRD §8.1. TIDAK termasuk gerbang validasi Farmasi (audit TA.1).
    F_ORAL = 0.86
    CL_SYSTEMIC = 24.0 # L/hr
    V1 = 43.5 # L
    KA = 3.47 # hr^-1
    KE = 0.55 # hr^-1

    # Konstanta kinetika hati/NAPQI/GSH + parameter nomogram — WAJIB
    # divalidasi anggota Farmasi sebelum dipakai (PRD §13 item #1,
    # AGENTS.md §3.1). JANGAN isi `value` dengan angka apa pun di sini.
    PD_CONSTANTS: Dict[str, PDConstant] = {
        # TODO(farmasi): lihat PRD §13 #1, menunggu balasan permintaan validasi
        "k_in": PDConstant(None, "1/hr"),
        # TODO(farmasi): lihat PRD §13 #1, menunggu balasan permintaan validasi
        "k_elim": PDConstant(None, "1/hr"),
        # TODO(farmasi): lihat PRD §13 #1, menunggu balasan permintaan validasi
        "k_meta": PDConstant(None, "1/hr"),
        # TODO(farmasi): lihat PRD §13 #1, menunggu balasan permintaan validasi
        "k_gsh": PDConstant(None, "L/(mmol*hr)"),
        # TODO(farmasi): lihat PRD §13 #1, menunggu balasan permintaan validasi
        "gsh_initial": PDConstant(None, "mmol"),
        # TODO(farmasi): lihat PRD §13 #1, menunggu balasan permintaan validasi
        "theta_thr": PDConstant(None, "ratio"),
        # TODO(farmasi): parameter kalibrasi garis nomogram 150/200 wajib
        # diverifikasi ke sumber primer (PRD §13 #1, EXECUTION_PLAN.md T2.4)
        "nomogram_decay_constant": PDConstant(None, "unitless"),
    }

    def __init__(self):
        logger.info("AcetaminophenPKPDEngine initialized.")

    def assert_ready(self) -> None:
        """Gerbang wajib sebelum komputasi PD/nomogram apa pun. Lihat PRD §13 item #1."""
        missing = [
            name for name, c in self.PD_CONSTANTS.items()
            if c.value is None or not c.validated_by_pharmacy or not c.citation
        ]
        if missing:
            raise RuntimeError(
                f"Konstanta PD belum tervalidasi Farmasi: {missing}. "
                "Lihat PRD §13 item #1."
            )

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

        k_in = self.PD_CONSTANTS["k_in"].value
        k_elim = self.PD_CONSTANTS["k_elim"].value
        k_meta = self.PD_CONSTANTS["k_meta"].value
        k_gsh = self.PD_CONSTANTS["k_gsh"].value

        dC_liver_dt = k_in * C_plasma - k_elim * C_liver

        # d[NAPQI]/dt = k_meta * C_liver - k_GSH * [GSH] * [NAPQI]
        dNAPQI_dt = k_meta * C_liver - k_gsh * GSH * NAPQI

        # d[GSH]/dt = -k_GSH * [GSH] * [NAPQI] (Asumsi sintesis GSH de novo diabaikan selama krisis)
        dGSH_dt = -k_gsh * GSH * NAPQI

        return [dC_liver_dt, dNAPQI_dt, dGSH_dt]

    def simulate_napqi_gsh_dynamics(self, dose_mg_kg: float, max_time_hours: int = 24, step_dt: float = 0.5) -> List[Dict[str, float]]:
        """
        Integrasi numerik ODE dC_liver/dt, d[NAPQI]/dt, d[GSH]/dt.
        BLOCKED sampai konstanta PD tervalidasi Farmasi (PRD §13 #1).
        """
        self.assert_ready()

        time_series = []
        if step_dt <= 0 or max_time_hours <= 0:
            return time_series

        gsh_initial = self.PD_CONSTANTS["gsh_initial"].value
        theta_thr = self.PD_CONSTANTS["theta_thr"].value

        t_points = np.arange(0, max_time_hours + step_dt, step_dt)
        y0 = [0.0, 0.0, gsh_initial] # Initial: C_liver=0, NAPQI=0, GSH=gsh_initial

        solution = odeint(self._pkpd_derivatives, y0, t_points, args=(dose_mg_kg,))

        for idx, t in enumerate(t_points):
            c_plasma = self.calculate_oral_absorption(dose_mg_kg, t)
            c_liver = solution[idx, 0]
            napqi = solution[idx, 1]
            gsh = solution[idx, 2]

            ratio = napqi / gsh_initial
            threshold_exceeded = bool(ratio > theta_thr)

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
        """
        Garis referensi nomogram Rumack-Matthew (PRD §8.1 validasi silang).
        BLOCKED: parameter kalibrasi garis 150/200 wajib diverifikasi Farmasi
        ke sumber primer (PRD §13 item #1; lihat juga EXECUTION_PLAN.md T2.4).
        """
        self.assert_ready()
        # Konstanta siap (assert_ready lulus) tetapi bentuk formula peluruhan
        # garis 150/200 belum ditetapkan — itu bagian dari verifikasi Farmasi
        # yang sama, bukan sesuatu yang boleh diasumsikan di sini.
        raise NotImplementedError(
            "Formula nomogram menunggu verifikasi Farmasi (PRD §13 #1, EXECUTION_PLAN.md T2.4)"
        )
