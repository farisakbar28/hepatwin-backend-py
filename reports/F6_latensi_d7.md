# F6 -- Instrumentasi Latensi & Verifikasi Paralelisme (D7)

## 1. Statistik per-tahap (panggilan langsung orchestrator, n=150)

| Tahap | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| lookup_ms | 0.03 | 134.84 | 145.85 | 372.79 | 2111.38 |
| ai_inference_ms | 13.24 | 22.18 | 24.39 | 58.90 | 75.60 |
| shap_ms | 6.60 | 11.11 | 13.15 | 43.76 | 51.58 |
| pbpk_ms | 0.54 | 0.59 | 0.69 | 14.23 | 18.45 |
| parallel_wall_ms | 13.53 | 22.39 | 24.67 | 59.20 | 75.90 |
| exposure_eval_ms | 0.02 | 0.02 | 0.02 | 0.02 | 0.03 |
| fusion_ms | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| total_ms | 16.54 | 149.92 | 161.32 | 385.14 | 2136.30 |

Seluruh 150 panggilan berada di bawah anggaran 5 detik.

## 2. Verifikasi paralelisme AI‖SHAP‖PBPK

- Rata-rata wall-time paralel (`parallel_wall_ms`, waktu `await asyncio.gather(...)`): **15.70 ms**
- Rata-rata `max(t_ai, t_shap, t_pbpk)` (ekspektasi PARALEL): **15.49 ms**
- Rata-rata `t_ai + t_shap + t_pbpk` (ekspektasi SEKUENSIAL): **24.47 ms**
- **Status: PARALEL** (wall-time mendekati maksimum tiga tugas)

## 3. Duplikasi komputasi predict_dili_risk() vs get_shap_detail()

- `standardize()` sendirian: **2.131 ms**
- `predict_dili_risk()` penuh: **7.552 ms** (standardize = 28.2% dari total)
- `get_shap_detail()` penuh: **3.971 ms** (standardize = 53.7% dari total)
- Kedua fungsi memanggil `standardize()` + featurisasi graph/fingerprint secara TERPISAH (diverifikasi lewat pembacaan kode `ai_engine.py`). Signifikansi duplikasi diukur di atas -- **usulan** (BUKAN diterapkan, di luar cakupan F6 sesuai EXECUTION_PLAN_FUSION.md langkah 3: "usulkan, jangan langsung terapkan"): jalur gabungan yang men-standardize+featurize SEKALI, lalu memakai hasilnya utk kedua forward pass, akan menghemat sekitar durasi `standardize()` di atas dikali dua dikurangi satu kali -- signifikan hanya bila proporsinya besar relatif thd total.

## 4. Thread-safety (20 permintaan konkuren, senyawa & kovariat identik)

- Hasil unik dari 20 panggilan: **1** (ekspektasi: 1)
- **LULUS** -- seluruh 20 hasil identik

## 5. Warm end-to-end (HTTP via TestClient, stack ASGI penuh)

Cold start diukur TERPISAH lewat `scripts/benchmark_cold_start.py` (proses Python terisolasi, tanpa import lain sebelumnya) -- lihat `reports/F6_cold_start_terisolasi.md`. Angka di bawah murni distribusi WARM/steady-state (proses ini sudah menjalankan banyak inferensi sebelumnya).

- n=30 request warm lewat HTTP penuh:
| Statistik | ms |
|---|---|
| p50 | 188 |
| p90 | 205 |
| **p95** | **218** |
| p99 | 234 |
| max | 238 |

**DoD D7 (p95 end-to-end < 5 detik, populasi WARM/steady-state, HTTP penuh):** p95 = 0.22s -> **LULUS**

## 6. \U0001F6A9 Temuan: varians antar-proses pada `shap_ms` (belum tuntas dijelaskan)

Skrip ini dijalankan **TIGA kali** (proses Python terpisah tiap kali, 50 senyawa x 3 profil = 150
panggilan/proses). Dua run TERAKHIR (angka di SS1-5 di atas) konsisten cepat. Run **PERTAMA**
(sebelum caveat metodologis cold-start di SS5 ditambahkan) menunjukkan pola yang JAUH berbeda pada
tahap `shap_ms`, dicatat di sini dari output asli sebelum file laporan ditimpa run berikutnya:

| Run | shap_ms p50 | shap_ms p90 | shap_ms p95 | shap_ms p99 | shap_ms max | total_ms p95 | total_ms max |
|---|---|---|---|---|---|---|---|
| 1 (awal) | 19.52 | 1192.60 | 1286.04 | 1479.51 | **9524.98** | 1607.15 | **10193.92** |
| 2 | 6.49 | 10.67 | 12.45 | 41.73 | 48.12 | 152.47 | 1778.82 |
| 3 (final, tabel SS1) | 6.60 | 11.11 | 13.15 | 43.76 | 51.58 | 161.32 | 2136.30 |

**Run 1 memuat SATU (atau beberapa) panggilan `get_shap_detail()` yang memakan hingga ~9.5 DETIK** --
cukup sendirian utk membuat `total_ms` panggilan itu (~10.2 detik) MELEBIHI anggaran 5 detik PRD UC-02.
Identitas senyawa spesifik penyebabnya TIDAK bisa direkonstruksi -- `reports/F6_raw_stage_timings.csv`
ditimpa run berikutnya sebelum anomalinya disadari (kesalahan prosedural, dicatat sebagai pelajaran,
bukan disembunyikan).

**Belum ditemukan akar sebab pastinya** (di luar wewenang F6 utk mendiagnosis lebih dalam ke
`hepatwin_ml.explain()` -- modul itu bagian Alur C, sudah "selesai" per `PROJECT_FUSION.md` SS2, di luar
cakupan `fusion`). Dugaan yang MASUK AKAL tapi TIDAK terverifikasi:
- Warm-up internal `HybridAIEngine._warm_up()` hanya memakai SMILES `"C"` (metana, 1 atom berat) --
  molekul nyata jauh lebih besar/kompleks. Bila `explain()` memicu kompilasi/alokasi tunda yang hanya
  terpicu oleh graf molekul berukuran nyata (bukan oleh warm-up trivial), efeknya HANYA muncul pada
  panggilan PERTAMA yang memakai molekul "nyata" dalam proses -- konsisten dengan pola run 1 (satu
  lonjakan besar, bukan berulang), TAPI TIDAK menjelaskan mengapa run 2 & run 3 (struktur identik,
  50 senyawa sama, urutan sama) tidak mereproduksinya sama sekali.
- Kemungkinan lain: jitter lingkungan (CPU/disk/OS scheduling di mesin pengembangan, background process
  lain) tidak berkaitan dengan kode sama sekali.

**Implikasi utk DoD D7:** p95 HTTP warm (0.22 detik, SS5) dan p95 internal (0.16 detik, SS1, dari run
final) **LULUS anggaran dengan margin besar** pada dua run yang konsisten -- tapi run 1 membuktikan
p99/max EKOR bisa jauh melampaui 5 detik pada kondisi yang belum dipahami penuh. **Rekomendasi**
(bukan diterapkan di F6 -- di luar cakupan, dan berisiko "mengakali" hasil per prinsip kerja #2): tim
memonitor `logger.info("F6 timing ...")` (dipasang F6 di `simulation_orchestrator.py`) di lingkungan
produksi/staging utk mengonfirmasi apakah pola run 1 muncul lagi, sebelum mengklaim p95 keseluruhan
katalog 1.231 senyawa AMAN tanpa syarat.
