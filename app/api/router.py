from fastapi import APIRouter
from app.api.endpoints import simulation

api_router = APIRouter()
api_router.include_router(simulation.router, tags=["simulation"])