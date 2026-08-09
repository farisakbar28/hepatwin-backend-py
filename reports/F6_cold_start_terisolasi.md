# F6 -- Cold Start Terisolasi (proses Python terpisah, tanpa import lain sebelumnya)

Metodologi: skrip ini HANYA meng-import `TestClient` + `app.main.app` sebelum permintaan pertama --
mereproduksi skenario proses backend yang baru saja `uvicorn app.main:app` dijalankan, BUKAN proses yang
sudah menjalankan modul lain (yang secara tidak sengaja memanaskan import torch/rdkit/numba lebih dulu).

| Tahap | Durasi |
|---|---|
| Import `app.main` + `TestClient` (sejak P2: import modul torch/RDKit saja; load model AI + warm-up kini di lifespan startup, TIDAK di import) | 8092 ms |
| Startup `lifespan` (P2, pengganti `@app.on_event`/`warm_up_default_executor`; muat model + warm-up + registry, dalam `TestClient(app)` context manager) | (tercakup dalam waktu `with` block sebelum request pertama, tidak terpisah presisi lewat TestClient) |
| **Request PERTAMA** `/simulate` setelah proses siap | **40 ms** |
| Request KEDUA (`warm`, senyawa berbeda) | 48 ms |
| **Gabungan dari proses baru start s.d. respons pertama diterima** (`import + startup + request pertama`) | **9407 ms** (9.41 detik) |

## Rekonsiliasi dengan temuan `ml/reports/C12_limitations.md` / `app/main.py`

Dokumentasi pra-`fusion` menyatakan "request PERTAMA ke POST /simulate pada proses backend yang baru
start memakan ~8-10 detik". F6 mengukur ulang secara terisolasi dan MEMISAHKAN dua komponen yang
sebelumnya kemungkinan besar terukur sebagai SATU angka gabungan:

1. **Biaya boot proses (SEKALI per lifecycle proses, SEBELUM traffic apa pun bisa dilayani):**
   import modul torch/RDKit = **8.09 detik** (sejak P2: load bobot model + kalibrator + JIT numba + warm-up internal terjadi di lifespan startup, terukur dalam `combined`).
   Ini BUKAN latensi request -- ini waktu proses perlu siap sebelum menerima permintaan APAPUN, analog
   dengan waktu boot container/pod, biasanya ditutupi *readiness probe* sebelum traffic dirutekan.
2. **Latensi request pertama SETELAH proses siap:** **0.04 detik** -- inilah yang
   relevan dengan anggaran PRD UC-02 (<=5 detik), karena itu mengukur waktu PEMROSESAN permintaan, bukan
   waktu proses siap menerima permintaan.
3. Jumlah keduanya (**9.41 detik**) MENDEKATI angka lama "~8-10 detik"
   -- REKONSILIASI yang masuk akal: pengukuran lama kemungkinan menghitung dari proses baru start s.d.
   respons pertama diterima (menggabungkan #1 dan #2), bukan murni waktu pemrosesan request.

**Kesimpulan F6:** dengan proses SUDAH siap menerima traffic (kondisi normal operasional -- server sudah
lolos *readiness probe*), permintaan PERTAMA sesungguhnya memakan **0.04 detik**,
DI BAWAH anggaran 5 detik PRD UC-02. Biaya boot proses (8.09 detik) tetap nyata
dan relevan secara OPERASIONAL (mis. waktu deploy/restart sebelum siap melayani), tapi BUKAN bagian dari
anggaran latensi per-request yang diukur DoD D7. Ini TIDAK membatalkan temuan lama -- ini MEMPERJELAS
komponen mana yang sebenarnya berkontribusi, lewat pengukuran independen (bukan dugaan).
