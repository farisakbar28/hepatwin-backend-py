# F6 -- Cold Start Terisolasi (proses Python terpisah, tanpa import lain sebelumnya)

Metodologi: skrip ini HANYA meng-import `TestClient` + `app.main.app` sebelum permintaan pertama --
mereproduksi skenario proses backend yang baru saja `uvicorn app.main:app` dijalankan, BUKAN proses yang
sudah menjalankan modul lain (yang secara tidak sengaja memanaskan import torch/rdkit/numba lebih dulu).

| Tahap | Durasi |
|---|---|
| Import `app.main` + `TestClient` (memicu load model AI, kalibrator, JIT numba PBPK, warm-up internal `HybridAIEngine._warm_up()`) | 5146 ms |
| Startup event FastAPI (`warm_up_default_executor`, dalam `TestClient(app)` context manager) | (tercakup dalam waktu `with` block sebelum request pertama, tidak terpisah presisi lewat TestClient) |
| **Request PERTAMA** `/simulate` setelah proses siap | **1945 ms** |
| Request KEDUA (`warm`, senyawa berbeda) | 1435 ms |
| **Gabungan dari proses baru start s.d. respons pertama diterima** (`import + startup + request pertama`) | **7132 ms** (7.13 detik) |

## Rekonsiliasi dengan temuan `ml/reports/C12_limitations.md` / `app/main.py`

Dokumentasi pra-`fusion` menyatakan "request PERTAMA ke POST /simulate pada proses backend yang baru
start memakan ~8-10 detik". F6 mengukur ulang secara terisolasi dan MEMISAHKAN dua komponen yang
sebelumnya kemungkinan besar terukur sebagai SATU angka gabungan:

1. **Biaya boot proses (SEKALI per lifecycle proses, SEBELUM traffic apa pun bisa dilayani):**
   import torch/RDKit + load bobot model + kalibrator + JIT numba + warm-up internal = **5.15 detik**.
   Ini BUKAN latensi request -- ini waktu proses perlu siap sebelum menerima permintaan APAPUN, analog
   dengan waktu boot container/pod, biasanya ditutupi *readiness probe* sebelum traffic dirutekan.
2. **Latensi request pertama SETELAH proses siap:** **1.94 detik** -- inilah yang
   relevan dengan anggaran PRD UC-02 (<=5 detik), karena itu mengukur waktu PEMROSESAN permintaan, bukan
   waktu proses siap menerima permintaan.
3. Jumlah keduanya (**7.13 detik**) MENDEKATI angka lama "~8-10 detik"
   -- REKONSILIASI yang masuk akal: pengukuran lama kemungkinan menghitung dari proses baru start s.d.
   respons pertama diterima (menggabungkan #1 dan #2), bukan murni waktu pemrosesan request.

**Kesimpulan F6:** dengan proses SUDAH siap menerima traffic (kondisi normal operasional -- server sudah
lolos *readiness probe*), permintaan PERTAMA sesungguhnya memakan **1.94 detik**,
DI BAWAH anggaran 5 detik PRD UC-02. Biaya boot proses (5.15 detik) tetap nyata
dan relevan secara OPERASIONAL (mis. waktu deploy/restart sebelum siap melayani), tapi BUKAN bagian dari
anggaran latensi per-request yang diukur DoD D7. Ini TIDAK membatalkan temuan lama -- ini MEMPERJELAS
komponen mana yang sebenarnya berkontribusi, lewat pengukuran independen (bukan dugaan).
