from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import SimulationRequest, SimulationResponse
from app.api.dependencies import get_orchestrator
from app.services.simulation_orchestrator import SimulationOrchestrator

router = APIRouter()

@router.post("/simulate", response_model=SimulationResponse)
async def simulate_dili(
    request: SimulationRequest, 
    db: Session = Depends(get_db),
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    return await orchestrator.handle_simulation(request, db)
