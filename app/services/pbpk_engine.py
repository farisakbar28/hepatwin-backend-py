import logging
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from app.services.allometric_service import AllometricService

logger = logging.getLogger(__name__)

NEGATIVE_TOLERANCE = 1e-10


def _pbpk_ode_python(
    _t: float, y: np.ndarray, v_p: float, v_l: float, v_k: float, v_r: float,
    q_l: float, q_k: float, q_r: float, cl_metab: float, cl_renal: float,
    kp_l: float, kp_k: float, kp_r: float,
) -> np.ndarray:
    c_p, c_l, c_k, c_r, _a_metab, _a_renal = y
    return np.array([
        (q_l * (c_l / kp_l) + q_k * (c_k / kp_k) + q_r * (c_r / kp_r) - (q_l + q_k + q_r) * c_p) / v_p,
        (q_l * (c_p - c_l / kp_l) - cl_metab * (c_l / kp_l)) / v_l,
        (q_k * (c_p - c_k / kp_k) - cl_renal * (c_k / kp_k)) / v_k,
        q_r * (c_p - c_r / kp_r) / v_r,
        cl_metab * (c_l / kp_l),
        cl_renal * (c_k / kp_k),
    ], dtype=np.float64)


try:
    from numba import njit

    _pbpk_ode = njit(cache=True)(_pbpk_ode_python)
    _pbpk_ode(0.0, np.zeros(6), *([1.0] * 12))
except Exception:  # pragma: no cover - optional acceleration must never block PBPK
    # P3: numba TIDAK dipin di runtime produksi (RAM diet Hobby 512 MB --
    # lihat requirements.txt); jalur default di cloud adalah fallback ini.
    _pbpk_ode = _pbpk_ode_python


@dataclass(frozen=True)
class PBPKSimulationResult:
    time_series: List[Dict[str, float]]
    cmax_hati: float
    auc_hati: float
    parameters: Dict[str, float]


class PBPKEngine:
    """PRD v2.3 four-compartment, linear, single-bolus PBPK solver."""

    def __init__(self) -> None:
        logger.info("PBPKEngine initialized.")

    @staticmethod
    def _validate_simulation_inputs(dosis_mg: float, duration_hours: float, step_hours: float) -> None:
        for name, value in {
            "dosis_mg": dosis_mg,
            "duration_hours": duration_hours,
            "step_hours": step_hours,
        }.items():
            if not math.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"{name} harus bernilai finite dan lebih besar dari 0.")
        if step_hours > duration_hours:
            raise ValueError("step_hours tidak boleh melebihi duration_hours.")

    @staticmethod
    def _time_grid(duration_hours: float, step_hours: float) -> np.ndarray:
        grid = np.arange(0.0, duration_hours + (step_hours * 0.5), step_hours, dtype=float)
        grid = grid[grid <= duration_hours]
        if not math.isclose(float(grid[-1]), duration_hours, rel_tol=0.0, abs_tol=1e-12):
            grid = np.append(grid, duration_hours)
        return grid

    @staticmethod
    def _verify_mass_balance(sol_y: np.ndarray, params: Dict[str, float], dosis_mg: float) -> None:
        m_total = (
            sol_y[0] * params["V_P"]
            + sol_y[1] * params["V_L"]
            + sol_y[2] * params["V_K"]
            + sol_y[3] * params["V_R"]
            + sol_y[4]
            + sol_y[5]
        )
        max_error = float(np.max(np.abs(m_total - dosis_mg)) / dosis_mg)
        if max_error > 1e-4:
            raise ValueError(f"Mass balance violated during simulation: {max_error:.2e}.")

    @lru_cache(maxsize=1024)
    def _simulate_base(
        self,
        usia: int,
        jenis_kelamin: str,
        berat_badan_kg: float,
        tinggi_badan_cm: float,
        xlogp: float | None,
        duration_hours: float,
        step_hours: float,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
        params = AllometricService.calculate_physiological_parameters(
            usia,
            jenis_kelamin,
            berat_badan_kg,
            tinggi_badan_cm,
            xlogp=xlogp,
        )
        y0 = np.array([1.0 / params["V_P"], 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
        t_eval = self._time_grid(duration_hours, step_hours)
        args = (
            params["V_P"], params["V_L"], params["V_K"], params["V_R"],
            params["Q_L"], params["Q_K"], params["Q_R"],
            params["Cl_metabolism"], params["Cl_renal"],
            params["K_P_L"], params["K_P_K"], params["K_P_R"],
        )
        solution = solve_ivp(
            fun=_pbpk_ode,
            t_span=(0.0, duration_hours),
            y0=y0,
            t_eval=t_eval,
            method="RK45",
            rtol=1e-6,
            atol=1e-8,
            args=args,
        )
        if not solution.success:
            raise ValueError(f"PBPK solver gagal: {solution.message}")
        if not np.all(np.isfinite(solution.y)):
            raise ValueError("PBPK solver menghasilkan nilai non-finite.")
        if np.any(solution.y < -NEGATIVE_TOLERANCE):
            raise ValueError("PBPK solver menghasilkan konsentrasi/amount negatif di luar toleransi.")
        sol_y = np.where(solution.y < 0.0, 0.0, solution.y)
        self._verify_mass_balance(sol_y, params, 1.0)
        return solution.t, sol_y, params

    def simulate_with_diagnostics(
        self,
        dosis_mg: float,
        usia: int,
        jenis_kelamin: str,
        berat_badan_kg: float,
        tinggi_badan_cm: float,
        xlogp: float | None = None,
        duration_hours: float = 24.0,
        step_hours: float = 0.1,
    ) -> PBPKSimulationResult:
        self._validate_simulation_inputs(dosis_mg, duration_hours, step_hours)
        t_arr, base_y, params = self._simulate_base(
            usia,
            jenis_kelamin,
            float(berat_badan_kg),
            float(tinggi_badan_cm),
            xlogp,
            float(duration_hours),
            float(step_hours),
        )
        sol_y = base_y * float(dosis_mg)
        if not np.all(np.isfinite(sol_y)):
            raise ValueError("PBPK scaling menghasilkan nilai non-finite.")
        if np.any(sol_y < -NEGATIVE_TOLERANCE):
            raise ValueError("PBPK scaling menghasilkan nilai negatif di luar toleransi.")
        sol_y = np.where(sol_y < 0.0, 0.0, sol_y)
        self._verify_mass_balance(sol_y, params, float(dosis_mg))

        c_l_arr = sol_y[1]
        time_series = [
            {"time": float(t), "c_plasma": float(c_p), "c_hati": float(c_l)}
            for t, c_p, c_l in zip(t_arr, sol_y[0], c_l_arr)
        ]
        return PBPKSimulationResult(
            time_series=time_series,
            cmax_hati=float(np.max(c_l_arr)),
            auc_hati=float(np.trapezoid(c_l_arr, t_arr)),
            parameters=params,
        )

    def simulate(
        self,
        dosis_mg: float,
        usia: int,
        jenis_kelamin: str,
        berat_badan_kg: float,
        tinggi_badan_cm: float,
        xlogp: float | None = None,
        duration_hours: float = 24.0,
        step_hours: float = 0.1,
    ) -> Tuple[List[Dict[str, float]], float, float]:
        result = self.simulate_with_diagnostics(
            dosis_mg,
            usia,
            jenis_kelamin,
            berat_badan_kg,
            tinggi_badan_cm,
            xlogp,
            duration_hours,
            step_hours,
        )
        return result.time_series, result.cmax_hati, result.auc_hati
