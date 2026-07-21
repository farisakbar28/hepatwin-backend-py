from fastapi import APIRouter, Depends
from app.models.schemas import SimulationRequest, SimulationResponse
from app.api.dependencies import get_orchestrator
from app.services.simulation_orchestrator import SimulationOrchestrator

router = APIRouter()

@router.post("/simulate", response_model=SimulationResponse)
def simulate_dili(request: SimulationRequest, orchestrator: SimulationOrchestrator = Depends(get_orchestrator)):
    return orchestrator.handle_request(request)