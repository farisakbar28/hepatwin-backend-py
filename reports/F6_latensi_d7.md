# F6 -- Instrumentasi Latensi & Verifikasi Paralelisme (D7)

## 1. Statistik per-tahap (panggilan langsung orchestrator, n=150)

| Tahap | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| lookup_ms | 0.02 | 2.20 | 2.38 | 4.91 | 8.26 |
| ai_inference_ms | 14.88 | 27.75 | 30.32 | 184.14 | 224.34 |
| shap_ms | 8.84 | 66.77 | 136.22 | 391.99 | 9715.83 |
| pbpk_ms | 17.56 | 83.62 | 169.90 | 400.53 | 9751.44 |
| parallel_wall_ms | 17.63 | 83.67 | 169.95 | 400.60 | 9751.48 |
| exposure_eval_ms | 0.08 | 0.10 | 0.12 | 0.16 | 6.24 |
| fusion_ms | 0.01 | 0.01 | 0.02 | 0.03 | 0.13 |
| total_ms | 18.38 | 85.46 | 171.81 | 403.56 | 9764.15 |

🚩 **1/150 panggilan (0.7%) melebihi anggaran 5 detik (total_ms > 5000)** -- didominasi ekor `shap_ms` yang sangat lebar (lihat statistik `shap_ms` di atas: p50=9ms tapi max=9716ms). Sepuluh panggilan terlambat:

| hepatwin_id | shap_ms | ai_inference_ms | pbpk_ms | total_ms |
|---|---|---|---|---|
| HT0083 | 9716 | 102 | 9751 | 9764 |
| HT0994 | 428 | 30 | 437 | 440 |
| HT0288 | 355 | 27 | 363 | 366 |
| HT0001 | 263 | 224 | 260 | 275 |
| HT0880 | 204 | 28 | 213 | 216 |
| HT0936 | 206 | 25 | 213 | 215 |
| HT0083 | 164 | 212 | 213 | 214 |
| HT0001 | 13 | 155 | 193 | 193 |
| HT1072 | 136 | 22 | 142 | 146 |
| HT0440 | 136 | 31 | 141 | 143 |

> Catatan: ekor tunggal ini dipicu senyawa EKSTREM dengan atom sangat banyak (mis. Aprotinin, 454 atom: atom-masking = ~455 varian graf dalam satu batch). Bukan pola sistematis -- p95 total = 172 ms.

## 2. Verifikasi paralelisme AI‖SHAP‖PBPK

- Rata-rata wall-time paralel (`parallel_wall_ms`, waktu `await asyncio.gather(...)`): **103.63 ms**
- Rata-rata `max(t_ai, t_shap, t_pbpk)` (ekspektasi PARALEL): **103.54 ms**
- Rata-rata `t_ai + t_shap + t_pbpk` (ekspektasi SEKUENSIAL): **218.50 ms**
- **Status: PARALEL** (wall-time mendekati maksimum tiga tugas)

## 3. Duplikasi komputasi predict_dili_risk() vs get_shap_detail()

- `standardize()` sendirian: **1.762 ms**
- `predict_dili_risk()` penuh: **6.139 ms** (standardize = 28.7% dari total)
- `get_shap_detail()` penuh: **12.757 ms** (standardize = 13.8% dari total)
- PASCA-P0: `_featurize()` di `ai_engine.py` men-standardize+featurize SEKALI per pemanggilan dan memakai hasil yang SAMA utk predict & SHAP (duplikasi intra-pemanggilan dihapus). Angka di atas adalah overhead per-pemanggilan bila predict & shap dipanggil TERPISAH (seperti benchmark ini) -- pada jalur /simulate nyata, P3 cache respons membuat request identik berulang dilayani dari memori tanpa komputasi sama sekali.

## 4. Thread-safety (20 permintaan konkuren, senyawa & kovariat identik)

- Hasil unik dari 20 panggilan: **1** (ekspektasi: 1)
- **LULUS** -- seluruh 20 hasil identik

## 5. Warm end-to-end (HTTP via TestClient, stack ASGI penuh)

Cold start diukur TERPISAH lewat `scripts/benchmark_cold_start.py` (proses Python terisolasi, tanpa import lain sebelumnya) -- lihat laporan cold-start terisolasi. Angka di bawah murni distribusi WARM/steady-state (proses ini sudah menjalankan banyak inferensi sebelumnya).

- n=30 request warm lewat HTTP penuh:
| Statistik | ms |
|---|---|
| p50 | 2 |
| p90 | 2 |
| **p95** | **2** |
| p99 | 11 |
| max | 15 |

**DoD D7 (p95 end-to-end < 5 detik, populasi WARM/steady-state, HTTP penuh):** p95 = 0.00s -> **LULUS**

🚩 **Catatan P3 (cache respons /simulate):** p95 HTTP di atas diukur dengan profil request yang SAMA dengan PROFILES[0] benchmark internal, sehingga mayoritas dilayani dari cache in-memory (hit ~3 ms) -- ini efektivitas cache, BUKAN latensi komputasi hangat. Distribusi latensi komputasi murni (tanpa cache respons) ada di SS1: p95 total = 172 ms.

🚩 **Namun** perhatikan SS1 di atas: benchmark INTERNAL (bypass HTTP, 150 panggilan lintas 50 senyawa berbeda) menemukan ekor `shap_ms` yang jauh lebih lebar dari yang tertangkap 30 sampel HTTP di sini -- lihat tabel "panggilan terlambat" di SS1 bila ada. p95 HTTP di atas TIDAK BOLEH dibaca sebagai jaminan seluruh 1.231 senyawa aman di bawah 5 detik; itu hanya berlaku utuh utk sampel 30 senyawa yang diuji di sini.
