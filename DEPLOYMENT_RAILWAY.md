# Deployment Checklist — HepaTwin Backend ke Railway

Checklist langkah-demi-langkah deployment awal backend FastAPI ke **Railway**
(berdasarkan `README.md`, `Procfile`, dan `app/core/config.py` — verifikasi
aktual, bukan asumsi).

- **Repo:** `farisakbar28/hepatwin-backend-py`, branch `master`
- **Entrypoint:** `Procfile` → `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Build:** `pip install -r requirements.txt` (termasuk `-e ./ml`)
- **Runtime:** Python 3.10+ (dikembangkan di 3.11/3.14; Railway default memadai)
- **Kebutuhan:** Supabase (PostgreSQL) dengan tabel `hepatwin_compounds` (1.336
  baris) + kebijakan RLS; artefak model di `app/models/` (sudah tracked).

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
      final. Saat ini dipakai `["*"]` sesuai keputusan tim (lihat §3, `CORS`).

## 1. Buat Project & Service di Railway

1. Buka https://railway.app → **New Project** → **Deploy from GitHub repo**.
2. Pilih repo `hepatwin-backend-py` → **Add Variables / Deploy**.
3. Railway otomatis mendeteksi Python (Nixpacks) dan membaca `requirements.txt`
   untuk build serta `Procfile` untuk start command — **tidak perlu** mengubah
   *Build Command* / *Start Command* di Settings.
4. Pastikan **Root Directory** kosong (root repo), bukan subfolder.
5. (Opsional) Pin versi Python: tambahkan variable `NIXPACKS_PYTHON_VERSION`
   (mis. `3.12`) bila ingin versi yang stabil eksplisit.

## 2. Environment Variables (wajib di dashboard Railway → Variables)

| Variable | Wajib | Nilai / Sumber | Catatan |
|---|---|---|---|
| `DATABASE_URL` | ✅ | Supabase → *Settings → Database → Connection string* (transaction/pooler, `postgresql://...`) | Dipakai SQLAlchemy dengan `sslmode=require` + `statement_timeout=15000`. **Tanpa ini backend tidak bisa lookup senyawa.** |
| `SUPABASE_URL` | — | `https://<ref>.supabase.co` | Untuk klien SDK; lookup runtime tetap via `DATABASE_URL`. |
| `SUPABASE_ANON_KEY` | — | Supabase → *Settings → API* (anon key) | Boleh publik (client-side). |
| `SUPABASE_SERVICE_ROLE_KEY` | — | Supabase → *Settings → API* (service role) | **Rahasia** — jangan pernah diekspos ke frontend. |
| `BACKEND_CORS_ORIGINS` | ✅ | Saat ini `["*"]`; untuk produksi final ganti origin eksplisit, mis. `["https://hepatwin.vercel.app"]` | JSON array atau dipisah koma. `allow_credentials` otomatis nonaktif bila `"*"` (lihat `app/main.py`). |
| `DEBUG` | ✅ | `False` | `True` akan membocorkan `timing_ms` per-tahap ke response simulate — **jangan** untuk produksi. |
| `AI_MODEL_PATH` | — | `app/models/model_gatnn_dnn.pt` (default) | Ubah hanya bila artefak model diletakkan di path lain. |

> Jangan commit `.env`; semua nilai di atas diatur langsung di dashboard
> Railway (atau via `railway` CLI / environments).

## 3. Deploy & Verifikasi

1. **Deploy** — tekan **Deploy**. Pantau tab *Deployments* → log build.
   - Build sukses: `pip install` selesai termasuk `-e ./ml` dan
     `torch`/`torch-geometric`/`rdkit`/`scipy`/`scikit-learn`.
   - Start sukses: log berisi `Uvicorn running on http://0.0.0.0:<PORT>`.
   - **Cold boot ~5–7 detik** (import torch/RDKit + load model + warm-up) —
     normal, bukan per-request.
2. **Health probe** (Railway menganggap service deployed saat port `$PORT`
   mulai listen; `/health` dipakai untuk monitoring eksternal):
   ```bash
   curl https://<railway-domain>/health
   # {"status":"ok","version":"1.0.0","ai_engine_ready":true,"pkpd_engine_ready":true}
   ```
   `ai_engine_ready:true` → model GATNN-DNN + kalibrator termuat benar.
3. **Smoke test endpoint debug PBPK**:
   ```bash
   curl "https://<railway-domain>/api/v1/pbpk/debug?usia=40&jenis_kelamin=L&berat_badan_kg=70&tinggi_badan_cm=168&dosis_mg=10500&xlogp=0.86"
   # Harapan: BMI≈24.80, V_P_L≈3.01, V_L_L≈1.799, Q_C_L_h≈360.0, Q_L_L_h≈90.0,
   # Kp_R≈1.37, Cl_met_L_h≈15.0, exposure_category terisi, dan
   # exposure_category_source == "INTERNAL_DISTRIBUTIONAL_CALIBRATION"
   ```
4. **Smoke test lookup autocomplete** (verifikasi koneksi DB + data nyata):
   ```bash
   curl "https://<railway-domain>/api/v1/compounds/autocomplete?q=acet&limit=3"
   # Harapan: total=3, item pertama Acetaminophen (HT0012), is_simulatable=true
   ```
5. **Smoke test simulasi end-to-end** (AI + PBPK + fusi, ~1.9–2.3 detik warm):
   ```bash
   curl -X POST https://<railway-domain>/api/v1/simulate \
     -H "Content-Type: application/json" \
     -d '{"hepatwin_id":"HT0012","dosis_mg":10500,"covariates":{"usia":40,"jenis_kelamin":"L","berat_badan_kg":70,"tinggi_badan_cm":168}}'
   # Harapan: 200; visual_color="red" (HIGH_EXPOSURE, skenario APAP 10.500 mg);
   # segment_mapping_type="PEDAGOGICAL_HEURISTIC"; timing_ms=null (DEBUG=False)
   ```
6. **Error path** (opsional):
   - `POST /api/v1/simulate` dgn `hepatwin_id` fiktif → `404`.
   - Dgn senyawa biologik (`hepatwin_id` yang `is_simulatable=false`, mis.
     `HT0003`) → `422`.

## 4. Checklist Pasca-Deploy

- [ ] `DEBUG=False` dan `BACKEND_CORS_ORIGINS` terisi di Railway.
- [ ] `/health` → `ai_engine_ready: true`, `pkpd_engine_ready: true`.
- [ ] `/api/v1/pbpk/debug` mengembalikan parameter v2.3 lengkap.
- [ ] Autocomplete & detail senyawa berfungsi (DB Supabase terhubung).
- [ ] `/api/v1/simulate` mengembalikan 200 dengan kontrak lengkap; `404/422`
      untuk kasus invalid.
- [ ] Frontend (Vercel) mengakses backend: tidak ada error CORS/network.
- [ ] (Opsional) Uptime/health monitoring eksternal menunjuk ke `GET /health`.
- [ ] (Opsional) Log error dipantau via tab *Deployments/Logs* — traceback
      hanya muncul di log server, bukan di response body.

## 5. Troubleshooting

| Gejala | Kemungkinan penyebab | Perbaikan |
|---|---|---|
| `ai_engine_ready: false` / simulate `503` | Model gagal dimuat saat startup | Cek log "Artefak model tidak ditemukan di ..."; pastikan `app/models/model_gatnn_dnn.pt` + metadata ter-deploy dan `AI_MODEL_PATH` benar. |
| Log "Kalibrator tidak ditemukan" → `score_is_calibrated` tidak terisi | `calibrator_gatnn_dnn.pkl` tidak ada / sklearn tidak terinstall | Pastikan file di `app/models/` ter-deploy dan `scikit-learn>=1.7.2` terinstall (sudah ada di `requirements.txt`). |
| Simulate/autocomplete `500` (DB) | `DATABASE_URL` salah/tidak reachable | Periksa connection string pooler; pastikan `sslmode=require` didukung; cek Supabase dashboard. |
| Frontend `403`/CORS | Origin frontend tidak diizinkan | Set `BACKEND_CORS_ORIGINS` ke origin Vercel eksplisit; restart service. |
| Request pertama lambat (~5–7 dtk) | Cold boot proses (import torch/RDKit + load model) | Normal; request berikutnya ~1.9–2.3 dtk. Bukan bug. |
| Build gagal di `torch-geometric` | Wheel untuk versi Python tertentu belum tersedia | Pin `NIXPACKS_PYTHON_VERSION` ke versi yang didukung (mis. 3.12) lalu redeploy. |

## 6. Referensi

- `README.md` — ringkasan API, env vars, batasan.
- `Procfile` — start command.
- `supabase/migrations/20260805_01_rls_hepatwin_compounds.sql` — kebijakan RLS.
- `PBPK_Engine_Audit_Report_v2_3.md` — audit mesin PBPK (deliverable PRD §11.1).
