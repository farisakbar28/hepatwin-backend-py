from fastapi import APIRouter

from app.api.endpoints import compounds, model_info, simulation, validate_smiles

api_router = APIRouter()
api_router.include_router(simulation.router, tags=["simulation"])
api_router.include_router(compounds.router, tags=["compounds"])
api_router.include_router(model_info.router, tags=["model_info"])
api_router.include_router(validate_smiles.router, tags=["validation"])