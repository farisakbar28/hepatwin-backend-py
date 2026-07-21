from app.services.simulation_orchestrator import SimulationOrchestrator

orchestrator = SimulationOrchestrator()

def get_orchestrator() -> SimulationOrchestrator:
    return orchestrator
