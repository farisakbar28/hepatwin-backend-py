import asyncio
import logging
import sys
import time
from pathlib import Path

# Fix ModuleNotFoundError when run directly via python app/main.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Bootstrap `hepatwin_ml` (ml/src) bila belum ter-install di environment.
# Runtime FastAPI Cloud TIDAK dapat meng-install paket lokal (build source
# gagal "egg_base: src does not exist"; wheel pre-built gagal "Distribution
# not found") dan platform menolak env var PYTHONPATH (HTTP 422). `ml/src`
# murni .py dan selalu ikut ter-upload, jadi diimpor langsung dari sana.
# Lokal: paket sudah ter-install (`pip install ./ml`) -> blok ini tidak
# aktif (nol perubahan behavior).
try:
    import hepatwin_ml  # noqa: F401
except ModuleNotFoundError:
    _ml_src = Path(__file__).resolve().parent.parent / "ml" / "src"
    if _ml_src.is_dir():
        sys.path.insert(0, str(_ml_src))

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


@app.on_event("startup")
async def warm_up_default_executor() -> None:
    """C10: paksa satu batch tugas lewat run_in_executor(None, ...) saat
    startup, sebagai mitigasi terhadap latensi tinggi pada request pertama.

    🔴 TEMUAN JUJUR (diverifikasi lewat pengukuran langsung terhadap uvicorn
    sungguhan, bukan hanya TestClient): request PERTAMA ke POST /simulate
    pada proses yang baru start makan ~8-10 detik -- melanggar anggaran PRD
    UC-02 (<=5 detik) -- sedangkan request kedua dst konsisten ~1-1.5 detik.
    Warm-up ini (main thread di HybridAIEngine._warm_up() + executor thread
    konkuren di sini) TERBUKTI membuat pemanggilan LANGSUNG (asyncio.run,
    tanpa lewat stack HTTP/ASGI) jadi cepat (<10ms) setelah warm-up. TAPI
    request HTTP nyata pertama (baik lewat TestClient maupun uvicorn asli)
    TETAP lambat meski warm-up ini sudah berjalan sukses saat startup --
    akar masalah pastinya BELUM ditemukan (diduga interaksi ASGI
    server/anyio dengan thread pool, bukan lagi inisialisasi PyTorch/RDKit
    itu sendiri). Dipertahankan di sini karena terbukti tidak merugikan dan
    membantu sebagian, TAPI dicatat eksplisit sebagai keterbatasan belum
    tuntas di ml/reports/C12_limitations.md -- bukan diklaim selesai."""
    from app.api.dependencies import orchestrator

    if not orchestrator.ai_engine.ready:
        logger.warning("Lewati warm-up executor: model AI tidak siap.")
        return

    loop = asyncio.get_running_loop()
    try:
        # KONKUREN (asyncio.gather), bukan sekuensial -- request nyata submit
        # ai_task+shap_task+pbpk_task BERSAMAAN (lihat simulation_orchestrator.py),
        # yang memaksa ThreadPoolExecutor default membuat >=3 thread pekerja
        # baru sekaligus. Warm-up sekuensial hanya menghangatkan 1 thread
        # (dipakai ulang tiap await), menyisakan 2 thread "dingin" untuk
        # request pengguna pertama -- diverifikasi jadi penyebab sisa
        # latensi tinggi setelah warm-up sekuensial pertama dicoba.
        await asyncio.gather(
            loop.run_in_executor(None, orchestrator.ai_engine.predict_dili_risk, "C"),
            loop.run_in_executor(None, orchestrator.ai_engine.get_shap_detail, "C"),
            loop.run_in_executor(None, orchestrator.pbpk_engine.simulate, 100.0, 30, "L", 70.0, 170.0),
        )
        logger.info("Warm-up executor startup selesai.")
    except Exception as exc:  # noqa: BLE001 -- warm-up gagal tidak boleh menggagalkan startup
        logger.warning("Warm-up executor startup gagal (non-fatal): %s", exc)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """C10: HTTPException (mis. 503 model tidak siap, 422 SMILES invalid) TIDAK
    lewat sini -- FastAPI menanganinya lewat handler bawaan sebelum sampai ke
    catch-all ini. Handler ini hanya untuk error TAK TERDUGA -- pesan generik
    ke klien, traceback lengkap ke log server (bukan dibocorkan ke response body)."""
    logger.exception("Unhandled exception saat memproses %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Silakan coba lagi atau hubungi administrator."},
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