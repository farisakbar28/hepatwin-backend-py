import sys
from pathlib import Path

# Fix ModuleNotFoundError when run directly via python app/main.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.api.endpoints import health

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Pesan exception mentah TIDAK boleh sampai ke klien (bisa membocorkan detail
    # internal seperti path file/traceback) - dicatat di log server, klien cuma
    # dapat pesan generik. Bug lama ini ditemukan & diperbaiki di TU.14 (upscale).
    logger.exception("Unhandled exception saat memproses %s %s", request.method, request.url)
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