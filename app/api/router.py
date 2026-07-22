from fastapi import APIRouter

from app.api.endpoints import compounds, simulation

api_router = APIRouter()
api_router.include_router(simulation.router, tags=["simulation"])
api_router.include_router(compounds.router, tags=["compounds"])