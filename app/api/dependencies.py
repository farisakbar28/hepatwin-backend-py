"""Resolver dependency SimulationOrchestrator (P2: lifecycle via lifespan).

SEBELUMNYA: `orchestrator = SimulationOrchestrator()` dieksekusi saat module
DI-IMPORT -- import `app.main`/`app.api.dependencies` memaksa model AI
(torch.load + kalibrator + warm-up) termuat walau tidak ada request sama
sekali (termasuk jalur /health dan skrip diagnostik).

SEKARANG (P2): instansiasi dipindah ke lifespan (`app.state.orchestrator`,
lihat app/main.py) -- import menjadi ringan, model dimuat saat server mulai
melayani. `get_orchestrator` membaca `app.state.orchestrator`; bila belum ada
(TestClient TANPA context manager, skrip di luar lifecycle) memakai
`get_shared_orchestrator` -- singleton lazy per proses (lock + double-check)
yang menjamin model TIDAK pernah dimuat lebih dari sekali di satu proses.
"""
import threading
from typing import Optional

from fastapi import Request

from app.services.simulation_orchestrator import SimulationOrchestrator

_shared: Optional[SimulationOrchestrator] = None
_shared_lock = threading.Lock()


def build_orchestrator() -> SimulationOrchestrator:
    """Konstruksi model AI + PBPK engine (berat: torch.load + kalibrator +
    warm-up internal HybridAIEngine._warm_up()). Dipanggil dari lifespan
    (lewat to_thread) atau fallback lazy."""
    return SimulationOrchestrator()


def get_shared_orchestrator() -> SimulationOrchestrator:
    """Singleton lazy per proses (double-checked lock) -- model dimuat SEKALI
    walau lifespan berjalan berulang (mis. banyak TestClient dalam satu proses)."""
    global _shared
    if _shared is None:
        with _shared_lock:
            if _shared is None:
                _shared = build_orchestrator()
    return _shared


def get_orchestrator(request: Request) -> SimulationOrchestrator:
    """Utk `Depends(get_orchestrator)`: instance dari `app.state.orchestrator`
    (dipasang lifespan), atau fallback singleton lazy bila lifespan belum
    berjalan. Keduanya menunjuk ke instance yang SAMA (satu model per proses)."""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if orchestrator is not None:
        return orchestrator
    return get_shared_orchestrator()
