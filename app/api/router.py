from fastapi import APIRouter
from app.api.endpoints import simulation, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(simulation.router, tags=["simulation"])