from fastapi import APIRouter
from app.models.schemas import SimulationRequest, SimulationResponse

router = APIRouter()

# Import the orchestrator instance from health so we don't instantiate it twice
from app.api.endpoints.health import orchestrator

@router.post("/simulate", response_model=SimulationResponse)
def simulate_dili(request: SimulationRequest):
    return orchestrator.handle_request(request)