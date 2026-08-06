from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import SimulationRequest, SimulationResponse
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

@router.get("/pbpk/debug")
async def pbpk_debug(
    usia: int = 45, 
    jenis_kelamin: str = "L", 
    berat_badan_kg: float = 75.0, 
    tinggi_badan_cm: float = 175.0, 
    dosis_mg: float = 100.0, 
    xlogp: float = 2.0
):
    from app.services.allometric_service import AllometricService
    from app.services.pbpk_engine import PBPKEngine
    from app.services.exposure_evaluator import ExposureEvaluatorService
    
    params = AllometricService.calculate_physiological_parameters(usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm, xlogp=xlogp)
    engine = PBPKEngine()
    time_series, cmax, auc = engine.simulate(dosis_mg, usia, jenis_kelamin, berat_badan_kg, tinggi_badan_cm, xlogp=xlogp)
    
    bmi = berat_badan_kg / ((tinggi_badan_cm/100)**2)
    exposure_result = ExposureEvaluatorService.evaluate_relative_exposure(cmax, auc, usia, bmi, dosis_mg, berat_badan_kg)
    
    return {
        "V_L": params["V_L"],
        "Q_L": params["Q_L"],
        "Cl": params["Cl_metabolism"],
        "bf_pct": params["body_fat_pct"],
        "Kp_R": params["K_P_R"],
        "cmax": cmax,
        "auc": auc,
        "ratio": exposure_result["cmax_auc_ratio"],
        "category": exposure_result["risk_level"]
    }

