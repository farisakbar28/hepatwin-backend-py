from fastapi import APIRouter, Depends

from app.api.dependencies import get_orchestrator
from app.services.simulation_orchestrator import SimulationOrchestrator

router = APIRouter()

@router.get("/health")
def health_check(orchestrator: SimulationOrchestrator = Depends(get_orchestrator)) -> dict:
    ai_ready = getattr(orchestrator.ai_engine, 'ready', False)
    # 'ready' hanya berarti servernya menyala, BUKAN bahwa bobot terlatih
    # berhasil dimuat. Bedakan eksplisit (temuan audit F1, AGENTS.md §3.10).
    ai_weights_loaded = getattr(orchestrator.ai_engine, 'weights_loaded', False)
    # The pkpd_engine is deterministic and doesn't load files, so it is always ready after init
    pkpd_ready = True

    return {
        "status": "ok",
        "version": "1.0.0",
        "ai_engine_ready": ai_ready,
        "ai_weights_loaded": ai_weights_loaded,
        "pkpd_engine_ready": pkpd_ready
    }