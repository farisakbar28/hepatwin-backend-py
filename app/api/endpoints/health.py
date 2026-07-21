from fastapi import APIRouter
from app.services.simulation_orchestrator import SimulationOrchestrator

router = APIRouter()
# Use orchestrator to get the state of engines
orchestrator = SimulationOrchestrator()

@router.get("/health")
def health_check() -> dict:
    ai_ready = getattr(orchestrator.ai_engine, 'ready', False)
    # The pkpd_engine is deterministic and doesn't load files, so it is always ready after init
    pkpd_ready = True
    
    return {
        "status": "ok", 
        "version": "1.0.0",
        "ai_engine_ready": ai_ready,
        "pkpd_engine_ready": pkpd_ready
    }