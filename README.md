# HepaTwin Backend API

FastAPI backend untuk skrining praklinis in-silico HepaTwin. PBPK Fase 1
adalah model 4-kompartemen linear, bolus tunggal, selama 24 jam. Output PBPK
adalah indeks paparan komputasional untuk riset/edukasi—bukan diagnosis,
rekomendasi dosis, atau keputusan terapi.

## Stack

- **API:** FastAPI + Pydantic v2 (Python 3.11+, sesuai `.python-version` = 3.11.11 dan runtime FastAPI Cloud).
- **AI:** PyTorch GATNN-DNN (inferensi statis, tanpa retraining runtime) +
  RDKit (graf molekul & ECFP4) — featurization/model/explain diimpor dari
  paket `hepatwin-ml` (`ml/src/hepatwin_ml`, murni .py). Lokal:
  `python -m pip install ./ml`; di cloud runtime di-bootstrap otomatis oleh
  `app/main.py` dari `ml/src` (tanpa dependency/env var).
- **Explainability:** atribusi tingkat gugus & atom (`hepatwin_ml.explain`,
  lihat `ml/reports/C8_shap.md`).
- **PBPK:** SciPy `solve_ivp` (RK45) — 4 kompartemen linear, penskalaan
  alometrik v2.3 (Deurenberg %BF, Soejima Q_L age-factor, Kp_R heuristic
  terkendali).
- **Database:** Supabase (PostgreSQL) via SQLAlchemy — lookup deterministik
  offline pada tabel `hepatwin_compounds`.

## Kontrak Supabase v2.3

- Katalog tertutup 1.336 senyawa (1.231 simulatable).
- Format ID: `HTdddd` (misal `HT0012`).
- Separator `segment_list`: titik koma (`;`).
- Nilai `dili_concern`: raw canonical (misal `vMost-DILI-concern`).

## API Utama

### `POST /api/v1/simulate`

Menerima identifier katalog dan kovariat:

```json
{
  "hepatwin_id": "HT0012",
  "dosis_mg": 10500,
  "covariates": {
    "usia": 40,
    "jenis_kelamin": "L",
    "berat_badan_kg": 70,
    "tinggi_badan_cm": 168
  }
}
```

Response meliputi `dili_score`, `risk_level`, `visual_color`, `blinking_speed`,
`affected_segments`, `cmax_liver_mg_l`, `auc_liver_mg_h_l` (dengan alias
backward-compatible `cmax_hati`, `auc_hati`), `shape_ratio_h_inv` (alias
`cmax_auc_ratio`), `exposure_index`, `exposure_category`, provenance
kalibrasi, `time_series_pbpk`, `explainability_shap`, `shap_detail`,
`fusion_reason`, `thresholds_used`, dan `disclaimer_permanent`.

Error handling: `404` untuk ID di luar daftar, `422` untuk senyawa biologik
(`is_simulatable = FALSE`) atau SMILES tidak valid, `503` bila model AI tidak
termuat (artefak gagal dimuat saat startup — tidak pernah mengembalikan skor
palsu).

### `GET /api/v1/pbpk/debug`

Menampilkan seluruh parameter alometrik serta metrik PBPK untuk validasi
pakar/juri: `BMI`, `metabolic_risk_flag`, `V_P_L`, `V_L_L`, `V_K_L`, `V_R_L`,
`Q_C_L_h`, `Q_L_L_h`, `Q_K_L_h`, `Q_R_L_h`, `body_fat_percent_raw/clamped`,
`xlogp_eff`, `Kp_R`, `Cl_met_L_h`, `Cl_renal_L_h`, `cmax_liver_mg_l`,
`auc_liver_mg_h_l`, `shape_ratio_h_inv`, `exposure_index`,
`exposure_category`, `exposure_category_source`.

### Lainnya

- `GET /api/v1/compounds/autocomplete?q=...&limit=...` — daftar tertutup
  1.231 senyawa simulatable (ETag + Cache-Control).
- `GET /api/v1/compounds/{hepatwin_id}` — detail senyawa.
- `GET /health` — status proses + kesiapan engine AI/PBPK + **observabilitas
  produksi**: `cache_stats` (hit/miss/hit-rate/ukuran utk cache `simulate`,
  `explain`, `smarts`, `pbpk_base` -- efektivitas cache terpantau langsung
  dari endpoint live) dan `memory_rss_mb` (RSS proses, memantau margin aman
  512 MB Hobby tier tanpa akses log server).

## Environment Variables

| Variable | Keterangan |
|---|---|
| `DATABASE_URL` | **Wajib.** Koneksi Postgres Supabase (SQLAlchemy, `sslmode=require`). |
| `SUPABASE_URL` | URL project Supabase — dipakai pipeline riset `ml/` (klien SDK di `ml/src/hepatwin_ml/data/load_supabase.py`) & test RLS; opsional untuk runtime API. |
| `SUPABASE_ANON_KEY` | Anon key Supabase (dipakai pipeline riset `ml/`). |
| `SUPABASE_SERVICE_ROLE_KEY` | Service-role key Supabase — hanya dipakai test RLS eksternal (`tests/security/test_rls_policies.py`); tidak dikonsumsi runtime API (klien SDK service-role dihapus). Jangan diekspos ke publik. |
| `BACKEND_CORS_ORIGINS` | Origin yang diizinkan, JSON array atau koma (default `["http://localhost:3000"]`). |
| `AI_MODEL_PATH` | Path artefak model (default `app/models/model_gatnn_dnn.pt`). |
| `DEBUG` | `False` di produksi; `True` menambahkan `timing_ms` per-tahap pada response simulate. |
| `PYTHONPATH` | **Tidak perlu di-set** — `app/main.py` menambahkan `ml/src` ke `sys.path` otomatis bila `hepatwin-ml` belum ter-install (platform menolak env var ini dengan HTTP 422). |

## Model Artifacts

- `app/models/model_gatnn_dnn.pt` — bobot GATNN-DNN (forward pass murni,
  kebijakan statis, tanpa retraining).
- `app/models/model_gatnn_dnn_metadata.json` — hyperparameter final (C6).
- `app/models/calibrator_gatnn_dnn.pkl` — kalibrator Platt scaling (sklearn;
  memerlukan `scikit-learn` di environment).

## Setup Lokal

```bash
python -m venv venv
# Windows: venv/Scripts/python.exe -m pip install -r requirements.txt
python -m pip install -r requirements.txt
python -m pip install ./ml   # paket hepatwin-ml (ml/src), lihat Stack
cp .env.example .env   # isi SUPABASE_URL / DATABASE_URL / keys
uvicorn app.main:app --reload
```

## Batasan (Known Limitations)

- **Model PBPK Fase 1** adalah model linear bolus tunggal tanpa absorpsi oral,
  protein binding, Km/Vmax, NAPQI/glutathione, atau IVIVE compound-specific —
  output adalah indeks paparan komputasional, bukan prediksi klinis.
- **Ambang fusi AI** (`FUSION_AI_T_LOW=0.5458`, `FUSION_AI_T_HIGH=0.6866`)
  bersifat distribusional internal (diturunkan dari katalog, lihat
  `reports/F2_penurunan_ambang.md`) — pending review Farmasi (gerbang K2),
  bukan ambang klinis.
- **Kategori exposure** memakai `P33/P66_EXPOSURE_INDEX` dari kalibrasi
  internal v2.3 (`reports/pbpk_exposure_calibration_v2_3.md`),
  `INTERNAL_DISTRIBUTIONAL_CALIBRATION` — bukan ambang klinis universal.
- **Latensi (diukur ulang pasca-P0–P3, lihat `reports/F6_latensi_d7.md` &
  `reports/F6_cold_start_terisolasi.md`):** komputasi per-simulasi **p95
  ~172 ms** (150 panggilan / 50 senyawa; request pertama setelah proses siap
  ~40 ms) — jauh di bawah target PRD ≤5 dtk. Cache in-memory (explain LRU
  2.048 + respons `/simulate` LRU 512, per input deterministik) melayani
  request identik berulang dalam ~3 ms. SHAP di-batch + matched-only (P0):
  p50 ~10 ms (sebelumnya tail hingga ~9,5 dtk, lihat
  `reports/F9_limitations_fusion.md` §10). Ekor 11,9 dtk tersisa hanya untuk
  satu senyawa ekstrem 454 atom (Aprotinin) — bukan pola sistematis. Di
  produksi (FastAPI Cloud **Hobby tier**), request pertama setelah idle
  (scale-to-zero default) menambah cold start platform (boot ulang + muat
  model, ~9,4 dtk import+startup terukur) — bukan per-request.
- **RAM diet Hobby 512 MB (P3, pasca-temuan 502/OOM di live):** baseline app
  ~415 MB + puncak compute ~493 MB mengetuk ambang — dimitigasi dgn (1)
  `numba` TIDAK dipin di runtime (hemat ~21 MB; PBPK pakai fallback
  pure-Python, +23 ms tak relevan vs PRD 5 dtk),  (2) atom-masking SHAP
  di-chunk 32 varian/forward + varian dibangun per-chunk (lazy) (batasi
  puncak memori molekul besar; terverifikasi live: molekul s/d ~125 atom
  stabil beruntun, >=128 atom stabil saat dipanggil tunggal, TAPI 21
  senyawa (1,71%) >=126 atom berisiko 502 bila dipanggil beberapa besar
  beruntun -- akumulasi memori arena, bukan hard limit), (3) `_trim_memory()` (glibc `malloc_trim`, Linux-only) setelah komputasi
  berat — cegah akumulasi RSS lintas request (+128 MB setelah 5 senyawa
  berbeda; tanpa `gc.collect` yang terukur ~260 ms/request), (4) explain LRU
  10.000 → 2.048
  (margin ekstra; footprint terukur ~10 MB utk 1.231 senyawa).
- **Mapping Couinaud** adalah heuristik pedagogis makrovaskular
  (`segment_mapping_type = PEDAGOGICAL_HEURISTIC`), bukan lokalisasi
  histologis klinis.

## Deployment (FastAPI Cloud — Hobby / Free Tier)

- **Platform:** [FastAPI Cloud](https://fastapicloud.com) **Hobby** ($0/bulan,
  tanpa kartu kredit) — backend publik untuk penyisihan GEMASTIK
  (`https://hepatwin-backend-py.fastapicloud.dev`, HTTPS otomatis). Bukan
  target high-traffic.
- **Sumber kode:** GitHub Integration — push `master` memicu build + deploy
  otomatis (FastAPI Cloud auto-detect `app.main:app`, install dari
  `requirements.txt`).
- **Build:** PyTorch **CPU-only** via
  `--extra-index-url https://download.pytorch.org/whl/cpu` — wheel `+cpu`
  menang atas versi plain PyPI (verifikasi: `torch.__version__` berakhiran
  `+cpu`).
- **Env vars:** di-set di Dashboard FastAPI Cloud (App → Environment
  Variables) — runtime hanya mengonsumsi `DATABASE_URL`, `BACKEND_CORS_ORIGINS`
  (origin frontend), dan `DEBUG=False`. `SUPABASE_URL` / `SUPABASE_ANON_KEY` /
  `SUPABASE_SERVICE_ROLE_KEY` **tidak dikonsumsi runtime** (hanya dipakai test
  RLS lokal & pipeline riset `ml/`) — aman ditinggalkan di cloud.
  **`PYTHONPATH` TIDAK perlu di-set** — `app/main.py` meng-bootstrap
  `hepatwin-ml` dari `ml/src` (platform menolak env var ini dengan HTTP 422).
- **Scale-to-zero (default):** app tidur saat idle; request pertama setelah
  idle menambah cold start (boot ulang + muat model) — normal untuk Hobby tier.
- Tidak bergantung pada path lokal/Windows; seluruh path relatif ke repo.

## Verifikasi

```bash
python -m pytest tests/unit tests/e2e tests/security/test_is_simulatable_enforcement.py
```

> **Catatan Windows:** bila pytest gagal dengan `PermissionError` pada direktori
temp sistem (`...\Temp\pytest-of-<user>`), gunakan basetemp eksplisit:
> `python -m pytest --basetemp=.pytest_tmp tests/unit tests/e2e ...`

Test RLS/database eksternal harus dijalankan hanya terhadap environment uji
terisolasi karena menggunakan kredensial service-role dan dapat menjalankan
CRUD.
