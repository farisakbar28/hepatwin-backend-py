import sys
from pathlib import Path

# Fix ModuleNotFoundError when run directly via python app/main.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import health
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import HepaTwinError

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.exception_handler(HepaTwinError)
async def hepatwin_error_handler(request: Request, exc: HepaTwinError):
    logger.warning(f"{exc.code}: {exc.user_message}")
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "detail": exc.user_message},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Detail exception dicatat ke log, TIDAK pernah masuk response client
    # (Arsitektur §E.6, AGENTS.md §6, temuan audit F5).
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True if "*" not in settings.BACKEND_CORS_ORIGINS else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(api_router, prefix=settings.API_V1_STR)