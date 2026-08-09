import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """P2: seluruh inisialisasi berat dipindah dari import-time ke sini --
    mengimpor `app.main` TIDAK lagi memuat model AI (sebelumnya `orchestrator =
    SimulationOrchestrator()` dieksekusi saat module di-import). Model + registry
    dimuat SEKALI saat server mulai melayani, disimpan di `app.state.orchestrator`
    (dibaca `app.api.dependencies.get_orchestrator`). TestClient TANPA context
    manager / skrip di luar lifecycle tetap aman via fallback singleton lazy di
    dependencies.py (tanpa reload model).

    Menggantikan `@app.on_event("startup")` yang deprecated (FastAPI >=0.93)."""
    from app.api.dependencies import get_shared_orchestrator

    loop = asyncio.get_running_loop()

    # Registry (P1) dan model AI dimuat KONKUREN -- keduanya independen.
    # gather memastikan kedua future SELALU di-await walau salah satu gagal
    # (build_orchestrator nyaris never-raise, tapi jangan tinggalkan orphan).
    orchestrator, _ = await asyncio.gather(
        asyncio.to_thread(get_shared_orchestrator),
        loop.run_in_executor(None, _warm_compound_registry),
    )
    app.state.orchestrator = orchestrator

    await _warm_up_executor(app.state.orchestrator)
    logger.info("Lifespan startup selesai.")

    yield

    # Shutdown: lepas referensi dari app.state. Instance process-wide tetap
    # hidup di `get_shared_orchestrator` (fallback lazy) -- tidak ada reload.
    app.state.orchestrator = None
    logger.info("Lifespan shutdown selesai.")


async def _warm_up_executor(orchestrator) -> None:
    """C10: paksa satu batch tugas lewat run_in_executor(None, ...) saat
    startup, sebagai mitigasi terhadap latensi tinggi pada request pertama.

    TEMUAN F6 (diukur ulang pasca-P2/P3, `scripts/benchmark_cold_start.py`):
    pengukuran terisolasi menunjukkan request PERTAMA setelah lifespan siap
    = ~40 ms; angka "~8-10 detik" lama ternyata = gabungan import (~8.1 s) +
    startup + request pertama (9.4 s total) -- direkonsiliasi di
    `reports/F6_cold_start_terisolasi.md`. Warm-up dipertahankan sebagai
    asuransi murah (terbukti tidak merugikan) agar lazy-init thread executor
    dibayar sebelum traffic nyata. (P2: dijalankan di dalam lifespan.)"""
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


def _warm_compound_registry() -> None:
    """P1: muat CompoundRegistry (seluruh baris hepatwin_compounds) SEKALI saat
    startup, di thread executor -- lookup request path jadi murni in-memory.
    Gagal load -> non-fatal; request path jatuh ke fallback DB (TTLCache lama).
    Dicoba ulang 3x (interval 1.5s) utk toleransi DB blip saat cold start;
    TIDAK ada refresh berkala -- snapshot statis per proses (scale-to-zero
    membuat proses baru memuat ulang saat boot)."""
    from app.core.database import SessionLocal
    from app.repositories.compound_registry import ensure_registry
    for attempt in range(1, 4):
        try:
            db = SessionLocal()
            try:
                if ensure_registry(db) is not None:
                    return
            finally:
                db.close()
        except Exception as exc:  # noqa: BLE001 -- warm-up non-fatal
            logger.warning("Warm-up registry gagal (attempt %d/3): %s", attempt, exc)
        if attempt < 3:
            time.sleep(1.5)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

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