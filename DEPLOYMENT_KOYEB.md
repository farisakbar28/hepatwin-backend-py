# Deployment Checklist — HepaTwin Backend ke Koyeb (Free Tier)

Checklist langkah-demi-langkah deployment backend FastAPI ke **Koyeb**
(berdasarkan `README.md`, `Procfile`, `Dockerfile`, dan `app/core/config.py` —
verifikasi aktual, bukan asumsi).

- **Repo:** `farisakbar28/hepatwin-backend-py`, branch `master`
- **Entrypoint:** `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
  (Koyeb default HTTP port **8000**)
- **Build:** `Dockerfile` disertakan (PyTorch **CPU-only**); alternatif buildpack
  (Nixpacks/Cloud Native Buildpacks) juga didukung via `Procfile` +
  `requirements.txt`.
- **Runtime:** Python 3.11 (image `python:3.11-slim`); Free Instance = 0.1 vCPU,
  512 MB RAM, 2 GB SSD.
- **Kebutuhan:** Supabase (PostgreSQL) dengan tabel `hepatwin_compounds`
  (1.336 baris) + kebijakan RLS; artefak model di `app/models/` (sudah tracked).

---

## 0. Prasyarat (sekali saja, sebelum deploy)

- [ ] Repository sudah di-push ke GitHub (`master`).
- [ ] Project Supabase sudah berisi tabel `hepatwin_compounds` (1.336 baris,
      1.231 `is_simulatable = TRUE`).
      ```sql
      SELECT count(*) FROM public.hepatwin_compounds;  -- harap 1336
      SELECT count(*) FROM public.hepatwin_compounds WHERE is_simulatable = TRUE;  -- harap 1231
      ```
- [ ] Migration RLS sudah diterapkan
      (`supabase/migrations/20260805_01_rls_hepatwin_compounds.sql`): akses
      read-only `anon` + CRUD `service_role`. Verifikasi:
      ```sql
      SELECT policyname FROM pg_policies WHERE tablename = 'hepatwin_compounds';
      ```
- [ ] (Opsional) URL production frontend Vercel sudah diketahui untuk CORS
      final. Saat ini dipakai `["*"]` sesuai keputusan tim (lihat §2, `CORS`).

## 1. Connect GitHub & Buat Service di Koyeb

1. Buka https://app.koyeb.com → **Create App** → **Create Web Service**.
2. **GitHub:** hubungkan akun GitHub → pilih repo `hepatwin-backend-py` →
   pilih branch `master` → *Git-driven deployment*.
3. Koyeb otomatis mendeteksi **`Dockerfile`** di root repo dan memakainya
   (rekomendasi — kontrol penuh + PyTorch CPU-only). Jika Dockerfile dihapus,
   Koyeb jatuh ke **buildpack** (mendeteksi `requirements.txt`) dan membaca
   `Procfile` untuk start command.
4. **Instance & region:** pilih **Free instance** (Nano: 0.1 vCPU / 512 MB RAM /
   2 GB SSD; hanya satu per organisasi; region Frankfurt atau Washington, D.C.).
5. **Port HTTP:** pastikan exposed port service = **8000** (default Koyeb)
   agar cocok dengan `EXPOSE 8000` / `--port 8000` di Dockerfile.
6. (Opsional) Jika memakai buildpack dan ingin mem-pin versi Python, set
   variable build `NIXPACKS_PYTHON_VERSION` (mis. `3.11`).

> **Catatan free tier:** instance Free **tidur (scale-to-zero) setelah ±1 jam
> tanpa traffic** dan *cold start* saat ada request baru (~5–7 detik boot).
> Ini perilaku platform, bukan bug aplikasi.

## 2. Environment Variables (dashboard Koyeb → Service → Variables)

| Variable | Wajib | Nilai / Sumber | Catatan |
|---|---|---|---|
| `DATABASE_URL` | ✅ | Supabase → *Settings → Database → Connection string* (transaction/pooler, `postgresql://...`) | Dipakai SQLAlchemy dengan `sslmode=require` + `statement_timeout=15000`. **Tanpa ini backend tidak bisa lookup senyawa.** |
| `SUPABASE_URL` | — | `https://<ref>.supabase.co` | Untuk klien SDK; lookup runtime tetap via `DATABASE_URL`. |
| `SUPABASE_ANON_KEY` | — | Supabase → *Settings → API* (anon key) | Boleh publik (client-side). |
| `SUPABASE_SERVICE_ROLE_KEY` | — | Supabase → *Settings → API* (service role) | **Rahasia** — jangan pernah diekspos ke frontend. |
| `BACKEND_CORS_ORIGINS` | ✅ | Saat ini `["*"]`; untuk produksi final ganti origin eksplisit, mis. `["https://hepatwin.vercel.app"]` | JSON array atau dipisah koma. `allow_credentials` otomatis nonaktif bila `"*"` (lihat `app/main.py`). |
| `DEBUG` | ✅ | `False` | `True` akan membocorkan `timing_ms` per-tahap ke response simulate — **jangan** untuk produksi. |
| `AI_MODEL_PATH` | — | `app/models/model_gatnn_dnn.pt` (default) | Ubah hanya bila artefak model diletakkan di path lain. |

> **Port:** Koyeb meng-set `PORT` otomatis (default = port terendah yang
> diekspos, 8000). `Procfile` memakai `${PORT:-8000}` dan `Dockerfile`
> hardcode `--port 8000` — keduanya aman selama exposed port = 8000.
>
> Jangan commit `.env`; semua nilai di atas diatur langsung di dashboard Koyeb.

## 3. Optimasi Memori Micro 512 MB (PyTorch CPU-only)

- Image default PyPI untuk `torch` membawa wheel CUDA (ukuran image bisa
  membengkak hingga beberapa GB dan boros RAM).
- Repo menyediakan **`requirements-koyeb.txt`** yang menginstal PyTorch
  **CPU-only**:
  ```text
  --extra-index-url https://download.pytorch.org/whl/cpu
  torch>=2.3.1
  ```
- `Dockerfile` yang disertakan sudah memakai `requirements-koyeb.txt` —
  build lebih cepat dan footprint RAM lebih kecil pada Micro 512 MB.
- Model GATNN-DNN berjalan murni di CPU (`torch.device("cpu")` di
  `app/services/ai_engine.py`) — wheel CUDA memang tidak pernah diperlukan.

## 4. Deploy & Verifikasi

1. **Deploy** — tekan **Create/Deploy Service**. Pantau tab *Builds/Logs*.
   - Build sukses: `pip install` selesai (torch CPU wheel + rdkit +
     torch-geometric + scikit-learn + `-e ./ml`).
   - Start sukses: log berisi `Uvicorn running on http://0.0.0.0:8000`.
   - **Cold boot ~5–7 detik** (import torch/RDKit + load model + warm-up) —
     normal, bukan per-request.
2. **Health check** (konfigurasi di Service → Health Check — HTTP probe):
   - Path: `/health` · Method: `GET` · Grace period: 5 s · Interval: 60 s ·
     Timeout: 5 s · Restart limit: 3.
   - Verifikasi manual:
     ```bash
     curl https://<your-app>.koyeb.app/health
     # {"status":"ok","version":"1.0.0","ai_engine_ready":true,"pkpd_engine_ready":true}
     ```
     `ai_engine_ready:true` → model GATNN-DNN + kalibrator termuat benar.
3. **Smoke test endpoint debug PBPK**:
   ```bash
   curl "https://<your-app>.koyeb.app/api/v1/pbpk/debug?usia=40&jenis_kelamin=L&berat_badan_kg=70&tinggi_badan_cm=168&dosis_mg=10500&xlogp=0.86"
   # Harapan: BMI≈24.80, V_P_L≈3.01, V_L_L≈1.799, Q_C_L_h≈360.0, Q_L_L_h≈90.0,
   # Kp_R≈1.37, Cl_met_L_h≈15.0, exposure_category terisi, dan
   # exposure_category_source == "INTERNAL_DISTRIBUTIONAL_CALIBRATION"
   ```
4. **Smoke test lookup autocomplete** (verifikasi koneksi DB + data nyata):
   ```bash
   curl "https://<your-app>.koyeb.app/api/v1/compounds/autocomplete?q=acet&limit=3"
   # Harapan: total=3, item pertama Acetaminophen (HT0012), is_simulatable=true
   ```
5. **Smoke test simulasi end-to-end** (AI + PBPK + fusi, ~1.9–2.3 detik warm):
   ```bash
   curl -X POST https://<your-app>.koyeb.app/api/v1/simulate \
     -H "Content-Type: application/json" \
     -d '{"hepatwin_id":"HT0012","dosis_mg":10500,"covariates":{"usia":40,"jenis_kelamin":"L","berat_badan_kg":70,"tinggi_badan_cm":168}}'
   # Harapan: 200; visual_color="red" (HIGH_EXPOSURE, skenario APAP 10.500 mg);
   # segment_mapping_type="PEDAGOGICAL_HEURISTIC"; timing_ms=null (DEBUG=False)
   ```
6. **Error path** (opsional):
   - `POST /api/v1/simulate` dgn `hepatwin_id` fiktif → `404`.
   - Dgn senyawa biologik (`hepatwin_id` yang `is_simulatable=false`, mis.
     `HT0003`) → `422`.

## 5. Checklist Pasca-Deploy

- [ ] `DEBUG=False` dan `BACKEND_CORS_ORIGINS` terisi di Koyeb.
- [ ] Exposed port service = 8000; `/health` → `ai_engine_ready: true`,
      `pkpd_engine_ready: true`.
- [ ] HTTP health check `/health` terkonfigurasi di Service settings.
- [ ] `/api/v1/pbpk/debug` mengembalikan parameter v2.3 lengkap.
- [ ] Autocomplete & detail senyawa berfungsi (DB Supabase terhubung).
- [ ] `/api/v1/simulate` mengembalikan 200 dengan kontrak lengkap; `404/422`
      untuk kasus invalid.
- [ ] Frontend (Vercel) mengakses backend: tidak ada error CORS/network.
- [ ] (Opsional) Uptime/health monitoring eksternal menunjuk ke `GET /health`
      (juga membantu membangunkan instance Free yang tidur).

## 6. Troubleshooting

| Gejala | Kemungkinan penyebab | Perbaikan |
|---|---|---|
| `ai_engine_ready: false` / simulate `503` | Model gagal dimuat saat startup | Cek log "Artefak model tidak ditemukan di ..."; pastikan `app/models/model_gatnn_dnn.pt` + metadata ikut ter-copy ke image dan `AI_MODEL_PATH` benar. |
| Log "Kalibrator tidak ditemukan" → `score_is_calibrated` tidak terisi | `calibrator_gatnn_dnn.pkl` tidak ada / sklearn tidak terinstall | Pastikan file di `app/models/` ikut ter-copy dan `scikit-learn>=1.7.2` terinstall (sudah ada di kedua requirements). |
| Simulate/autocomplete `500` (DB) | `DATABASE_URL` salah/tidak reachable | Periksa connection string pooler; pastikan `sslmode=require` didukung; cek Supabase dashboard. |
| Frontend `403`/CORS | Origin frontend tidak diizinkan | Set `BACKEND_CORS_ORIGINS` ke origin Vercel eksplisit; redeploy/restart service. |
| Request pertama lambat (~5–7 dtk) | Cold start instance Free (tidur setelah idle) atau boot proses | Normal (platform + boot); request berikutnya ~1.9–2.3 dtk. Bukan bug. |
| Build gagal di `torch-geometric` | Wheel tidak cocok dengan versi Python | Pin `NIXPACKS_PYTHON_VERSION` (buildpack) atau ganti base image `python:3.11-slim` → versi Python lain di `Dockerfile`, lalu rebuild. |
| Image terlalu besar / build lambat | Wheel torch CUDA ikut terinstal | Pastikan build memakai `requirements-koyeb.txt` (CPU-only); jangan install dari `requirements.txt` root di Koyeb. |

## 7. Referensi

- `README.md` — ringkasan API, env vars, batasan.
- `Procfile` — start command (`${PORT:-8000}`).
- `Dockerfile` + `requirements-koyeb.txt` — build CPU-only untuk Koyeb.
- `supabase/migrations/20260805_01_rls_hepatwin_compounds.sql` — kebijakan RLS.
- `PBPK_Engine_Audit_Report_v2_3.md` — audit mesin PBPK (deliverable PRD §11.1).
