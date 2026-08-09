import os

from fastapi import APIRouter, Depends

from app.api.dependencies import get_orchestrator
from app.services.simulation_cache import simulation_cache_stats
from app.services.simulation_orchestrator import SimulationOrchestrator
from hepatwin_ml.explain import cache_stats as explain_cache_stats

router = APIRouter()


def _memory_rss_mb() -> float | None:
    """RSS proses (MB) TANPA dependensi eksternal: /proc/self/statm di Linux
    (produksi FastAPI Cloud), fallback psutil bila terpasang (dev), None bila
    tidak tersedia (platform lain). Dipakai /health utk memantau margin
    aman memori Hobby tier 512 MB langsung dari endpoint live."""
    try:
        with open("/proc/self/statm") as f:
            pages = int(f.read().split()[1])
        return round(pages * os.sysconf("SC_PAGE_SIZE") / (1024 * 1024), 1)
    except Exception:
        pass
    try:
        import psutil  # dev-only, tidak wajib di produksi

        return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)
    except Exception:
        return None


@router.get("/health")
def health_check(orchestrator: SimulationOrchestrator = Depends(get_orchestrator)) -> dict:
    ai_ready = getattr(orchestrator.ai_engine, 'ready', False)
    # The pkpd_engine is deterministic and doesn't load files, so it is always ready after init
    pkpd_ready = True

    # Observabilitas produksi: efektivitas cache (hit-rate) + keamanan memori
    # 512 MB terpantau langsung dari endpoint live, tanpa akses log server.
    _explain_stats = explain_cache_stats()

    return {
        "status": "ok",
        "version": "1.0.0",
        "ai_engine_ready": ai_ready,
        "pkpd_engine_ready": pkpd_ready,
        "cache_stats": {
            "simulate": simulation_cache_stats(),
            "explain": _explain_stats["explain"],
            "smarts": _explain_stats["smarts"],
            "pbpk_base": orchestrator.pbpk_engine.pbpk_cache_stats(),
        },
        "memory_rss_mb": _memory_rss_mb(),
    }