from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import PBPKDebugResponse, SimulationRequest, SimulationResponse
from app.api.dependencies import get_orchestrator
from app.services.simulation_orchestrator import SimulationOrchestrator
from app.core.validators.compound_validator import verify_simulatable_compound

router = APIRouter()

@router.post("/simulate", response_model=SimulationResponse, dependencies=[Depends(verify_simulatable_compound)])
async def simulate_dili(
    request: SimulationRequest, 
    db: Session = Depends(get_db),
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    return await orchestrator.handle_simulation(request, db)

@router.get("/pbpk/debug", response_model=PBPKDebugResponse)
async def pbpk_debug(
    usia: int = Query(45, ge=0, le=100),
    jenis_kelamin: str = Query("L", pattern="^(L|P)$"),
    berat_badan_kg: float = Query(75.0, gt=0, allow_inf_nan=False),
    tinggi_badan_cm: float = Query(175.0, gt=0, allow_inf_nan=False),
    dosis_mg: float = Query(100.0, gt=0, allow_inf_nan=False),
    xlogp: float | None = Query(2.0, allow_inf_nan=False),
) -> PBPKDebugResponse:
    from app.services.pbpk_engine import PBPKEngine
    from app.services.exposure_evaluator import ExposureEvaluatorService

    engine = PBPKEngine()
    result = engine.simulate_with_diagnostics(
        dosis_mg, usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm, xlogp=xlogp
    )
    params = result.parameters
    exposure_result = ExposureEvaluatorService.evaluate_relative_exposure(result.cmax_hati, result.auc_hati)

    return PBPKDebugResponse(
        BMI=params["bmi"],
        metabolic_risk_flag=params["metabolic_risk_flag"],
        clearance_multiplier_from_bmi=params["clearance_multiplier_from_bmi"],
        V_P_L=params["V_P"], V_L_L=params["V_L"], V_K_L=params["V_K"], V_R_L=params["V_R"],
        Q_C_L_h=params["Q_C"], Q_L_L_h=params["Q_L"], Q_K_L_h=params["Q_K"], Q_R_L_h=params["Q_R"],
        body_fat_percent_raw=params["body_fat_percent_raw"],
        body_fat_percent_clamped=params["body_fat_percent_clamped"],
        xlogp_eff=params["xlogp_eff"], Kp_R=params["K_P_R"],
        Cl_met_L_h=params["Cl_metabolism"], Cl_renal_L_h=params["Cl_renal"],
        cmax_liver_mg_l=result.cmax_hati, auc_liver_mg_h_l=result.auc_hati,
        cmax_auc_ratio=exposure_result["cmax_auc_ratio"],
        shape_ratio_h_inv=exposure_result["shape_ratio_h_inv"],
        exposure_index=exposure_result["exposure_index"],
        exposure_category=exposure_result["risk_level"],
        exposure_category_source=exposure_result["exposure_category_source"],
        exposure_calibration_version=exposure_result["calibration_version"],
    )
