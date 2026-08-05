# `ml/` — Pipeline Riset & Pelatihan HepaTwin GATNN-DNN

Pipeline ini terpisah secara **logis** dari runtime FastAPI (`app/`): dependensi riset
didaftar di `ml/requirements.txt` (bukan digabung ke `requirements.txt` root), dan kode
riset (`ml/src/hepatwin_ml/`) tidak diimpor balik oleh `app/` kecuali lewat instalasi
paket eksplisit (lihat catatan C10 di `ml/reports/C10_*` setelah task itu selesai).

> **[KEPUTUSAN AI — PENDING REVIEW]** `EXECUTION_PLAN_FIX_MODEL.md` (C1) meminta virtualenv
> Python terpisah (`.venv-ml`) dari environment backend. Di environment pengembangan repo
> ini, `app/` (`requirements.txt` root) **sudah** mensyaratkan `torch`, `torch-geometric`,
> `rdkit`, `shap` untuk keperluan inferensi runtime (`ai_engine.py` memuat model GATNN-DNN
> di proses yang sama) — jadi kedua daftar dependensi tumpang tindih secara inheren, dan
> `.venv` tunggal yang sudah ada di repo ini memuat superset keduanya. Dipilih: **pakai
> ulang `.venv` tunggal itu** alih-alih membuat `.venv-ml` terpisah secara fisik, karena
> membuat env kedua berarti mengunduh ulang `torch`/`torch-geometric` (~2 GB) tanpa manfaat
> isolasi nyata (versi paket yang sama dipakai kedua sisi). Pemisahan yang dipertahankan:
> **dua file requirements berbeda** (`ml/requirements.txt` vs root `requirements.txt`),
> sesuai literal acceptance criteria C1 ("dibuktikan: dua file requirements berbeda").
> Kalau tim mau env yang benar-benar terisolasi (mis. untuk CI), jalankan langkah "Environment
> terpisah" di bawah.

## Setup cepat (pakai `.venv` yang sudah ada di root repo)

```bash
# dari root repo
.venv/Scripts/python.exe -m pip install -r ml/requirements.txt
.venv/Scripts/python.exe -m pip freeze > ml/requirements.lock.txt   # kunci versi
.venv/Scripts/python.exe -c "import torch, torch_geometric, rdkit, shap, lightgbm, xgboost; print('OK')"
```

## Environment terpisah (opsional, mis. untuk CI atau isolasi penuh)

```bash
python -m venv .venv-ml
.venv-ml/Scripts/python.exe -m pip install -r ml/requirements.txt
```

## ⚠️ Kredensial

`ml/src/hepatwin_ml/data/load_supabase.py` (C2) membaca `.env` lewat `python-dotenv` untuk
kredensial Supabase. **`.env` TIDAK BOLEH pernah di-commit** — sudah ada di `.gitignore` root.
Pipeline riset memakai **`SUPABASE_ANON_KEY`** (bukan `SUPABASE_SERVICE_ROLE_KEY`) karena
hanya perlu baca, dan service role key melewati Row Level Security.

## Menjalankan pipeline

Urutan task ada di `../EXECUTION_PLAN_FIX_MODEL.md` (C2 → C12). Ringkas:

```bash
# C2 — featurisasi dari Supabase
.venv/Scripts/python.exe -m hepatwin_ml.data.load_supabase   # (setelah C2 ditulis)

# C5 — split
.venv/Scripts/python.exe -m hepatwin_ml.data.splits          # (setelah C5 ditulis)

# C6 — training
.venv/Scripts/python.exe -m hepatwin_ml.train                # (setelah C6 dijalankan)

# Test
.venv/Scripts/python.exe -m pytest ml/tests/ -v
```

## Struktur

| Path | Isi |
|---|---|
| `src/hepatwin_ml/data/` | Loader Supabase, standardisasi SMILES, label, split, hold-out |
| `src/hepatwin_ml/features/` | Graf molekul (34-dim node/6-dim edge), fingerprint (MACCS+ECFP4+SMARTS=1200), pola SMARTS |
| `src/hepatwin_ml/models/` | Arsitektur `GATv2Conv`+DNN hybrid, baseline (RF/LightGBM/XGBoost/LR/MLP) |
| `src/hepatwin_ml/{train,evaluate,calibrate,explain}.py` | Loop training, evaluasi metrik, kalibrasi probabilitas, explainability |
| `tests/` | Unit test pipeline (pytest) |
| `reports/` | Laporan tiap task (C2, C4, C5, C7, C8, C9, C12) |
| `reports/_upscale_archive/` | Arsip laporan dari branch `upscale` — bukti hyperparameter final berasal dari nested CV 10-fold yang nyata |
| `data/`, `models/` | Artefak yang dihasilkan pipeline (di-gitignore, kecuali seal reproduktibilitas — lihat `.gitignore` root §8) |

Konteks & keputusan desain lengkap ada di `../PROJECT_FIX_MODEL.md`.
