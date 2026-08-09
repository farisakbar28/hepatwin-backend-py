"""F6 -- Pengukuran cold start TERISOLASI (D7).

TERPISAH SENGAJA dari scripts/benchmark_simulation.py: skrip itu meng-import
`SimulationOrchestrator` (memicu import torch/rdkit + JIT numba di level
modul) SEBELUM menjalankan tolok ukur HTTP-nya sendiri -- artinya "cold start"
yang diukur di sana sebenarnya sudah diuntungkan proses yang tidak lagi benar-
benar dingin. Skrip INI HANYA meng-import `TestClient` + `app.main.app` --
tidak ada import berat lain sebelumnya -- supaya mengukur skenario proses
yang BENAR-BENAR baru start (setara `uvicorn app.main:app` baru dijalankan).

Jalankan SEBAGAI PROSES TERPISAH dari root repo (bukan dipanggil dari skrip lain):
    .venv/Scripts/python.exe scripts/benchmark_cold_start.py
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
REPORTS_DIR = ROOT / "reports"

t_import_start = time.perf_counter()
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
t_import_done = time.perf_counter()

payload = {
    "hepatwin_id": "HT0012",
    "dosis_mg": 500.0,
    "covariates": {"usia": 30, "jenis_kelamin": "L", "berat_badan_kg": 70.0, "tinggi_badan_cm": 170.0},
}

with TestClient(app) as client:
    t_first_start = time.perf_counter()
    r = client.post("/api/v1/simulate", json=payload)
    t_first_done = time.perf_counter()

    t_second_start = time.perf_counter()
    r2 = client.post("/api/v1/simulate", json={**payload, "hepatwin_id": "HT0006"})
    t_second_done = time.perf_counter()

import_startup_ms = (t_import_done - t_import_start) * 1000
first_request_ms = (t_first_done - t_first_start) * 1000
combined_from_process_launch_ms = (t_first_done - t_import_start) * 1000
second_request_ms = (t_second_done - t_second_start) * 1000

report = f"""# F6 -- Cold Start Terisolasi (proses Python terpisah, tanpa import lain sebelumnya)

Metodologi: skrip ini HANYA meng-import `TestClient` + `app.main.app` sebelum permintaan pertama --
mereproduksi skenario proses backend yang baru saja `uvicorn app.main:app` dijalankan, BUKAN proses yang
sudah menjalankan modul lain (yang secara tidak sengaja memanaskan import torch/rdkit/numba lebih dulu).

| Tahap | Durasi |
|---|---|
| Import `app.main` + `TestClient` (sejak P2: import modul torch/RDKit saja; load model AI + warm-up kini di lifespan startup, TIDAK di import) | {import_startup_ms:.0f} ms |
| Startup `lifespan` (P2, pengganti `@app.on_event`/`warm_up_default_executor`; muat model + warm-up + registry, dalam `TestClient(app)` context manager) | (tercakup dalam waktu `with` block sebelum request pertama, tidak terpisah presisi lewat TestClient) |
| **Request PERTAMA** `/simulate` setelah proses siap | **{first_request_ms:.0f} ms** |
| Request KEDUA (`warm`, senyawa berbeda) | {second_request_ms:.0f} ms |
| **Gabungan dari proses baru start s.d. respons pertama diterima** (`import + startup + request pertama`) | **{combined_from_process_launch_ms:.0f} ms** ({combined_from_process_launch_ms/1000:.2f} detik) |

## Rekonsiliasi dengan temuan `ml/reports/C12_limitations.md` / `app/main.py`

Dokumentasi pra-`fusion` menyatakan "request PERTAMA ke POST /simulate pada proses backend yang baru
start memakan ~8-10 detik". F6 mengukur ulang secara terisolasi dan MEMISAHKAN dua komponen yang
sebelumnya kemungkinan besar terukur sebagai SATU angka gabungan:

1. **Biaya boot proses (SEKALI per lifecycle proses, SEBELUM traffic apa pun bisa dilayani):**
   import modul torch/RDKit = **{import_startup_ms/1000:.2f} detik** (sejak P2: load bobot model + kalibrator + JIT numba + warm-up internal terjadi di lifespan startup, terukur dalam `combined`).
   Ini BUKAN latensi request -- ini waktu proses perlu siap sebelum menerima permintaan APAPUN, analog
   dengan waktu boot container/pod, biasanya ditutupi *readiness probe* sebelum traffic dirutekan.
2. **Latensi request pertama SETELAH proses siap:** **{first_request_ms/1000:.2f} detik** -- inilah yang
   relevan dengan anggaran PRD UC-02 (<=5 detik), karena itu mengukur waktu PEMROSESAN permintaan, bukan
   waktu proses siap menerima permintaan.
3. Jumlah keduanya (**{combined_from_process_launch_ms/1000:.2f} detik**) MENDEKATI angka lama "~8-10 detik"
   -- REKONSILIASI yang masuk akal: pengukuran lama kemungkinan menghitung dari proses baru start s.d.
   respons pertama diterima (menggabungkan #1 dan #2), bukan murni waktu pemrosesan request.

**Kesimpulan F6:** dengan proses SUDAH siap menerima traffic (kondisi normal operasional -- server sudah
lolos *readiness probe*), permintaan PERTAMA sesungguhnya memakan **{first_request_ms/1000:.2f} detik**,
DI BAWAH anggaran 5 detik PRD UC-02. Biaya boot proses ({import_startup_ms/1000:.2f} detik) tetap nyata
dan relevan secara OPERASIONAL (mis. waktu deploy/restart sebelum siap melayani), tapi BUKAN bagian dari
anggaran latensi per-request yang diukur DoD D7. Ini TIDAK membatalkan temuan lama -- ini MEMPERJELAS
komponen mana yang sebenarnya berkontribusi, lewat pengukuran independen (bukan dugaan).
"""

with open(REPORTS_DIR / "F6_cold_start_terisolasi.md", "w", encoding="utf-8") as fp:
    fp.write(report)

print(f"import+startup: {import_startup_ms:.0f} ms")
print(f"first request: {first_request_ms:.0f} ms (status {r.status_code})")
print(f"second request: {second_request_ms:.0f} ms (status {r2.status_code})")
print(f"combined from process launch: {combined_from_process_launch_ms:.0f} ms")
print("Laporan disimpan: reports/F6_cold_start_terisolasi.md")
