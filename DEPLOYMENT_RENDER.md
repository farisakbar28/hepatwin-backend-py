# Deployment Checklist — HepaTwin Backend ke Render (Free Tier)

Checklist langkah-demi-langkah deployment backend FastAPI ke **Render**
(berdasarkan `render.yaml`, `README.md`, `Procfile`, dan `app/core/config.py` —
verifikasi aktual, bukan asumsi).

- **Repo:** `farisakbar28/hepatwin-backend-py`, branch `master`
- **Entrypoint:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  (Render meng-set env `PORT` otomatis — default **10000**)
- **Build:** native Python (`pip install -r requirements.txt`); PyTorch
  **CPU-only** via `--extra-index-url https://download.pytorch.org/whl/cpu`
  di `requirements.txt` — krusial untuk Free Tier (512 MB RAM).
- **Runtime:** Python 3.11 (dipin di `render.yaml` via `PYTHON_VERSION`).
- **Kebutuhan:** Supabase (PostgreSQL) dengan tabel `hepatwin_compounds`
  (1.336 baris) + kebijakan RLS; artefak model di `app/models/` (sudah tracked).

---

## Render Free Tier — Batasan & Perilaku yang Wajib Diketahui

Seluruh langkah di dokumen ini mengasumsikan **Render Free Tier**:

| Aspek | Batasan / Perilaku Free Tier |
|---|---|
| **RAM** | **512 MB** (shared) — alasan utama PyTorch CPU-only (§3) |
| **CPU** | **0.1 vCPU** (shared) |
| **Disk** | **Ephemeral** — semua file lokal terhapus saat restart/redeploy/spin-down. Aplikasi ini **stateless**: state satu-satunya di Supabase (in-memory cache saja), jadi aman |
| **Instance** | Maksimal **1 instance** (tanpa scaling horizontal) |
| **Idle spin-down** | Tidur otomatis setelah **15 menit** tanpa traffic; jam instance tidak terpakai saat tidur |
| **Cold start** | ±**30–60 detik** (~1 menit) saat bangun dari tidur; Render menampilkan halaman loading ke browser — **normal, bukan bug** |
| **Instance hours** | **750 jam/bulan** per workspace |
| **Build minutes** | **500 menit/bulan** — wheel CPU-only menjaga build cepat & hemat kuota |
| **Bandwidth** | **5 GB outbound/bulan** (inbound gratis) |
| **Tidak tersedia di Free** | Preview Environments, background workers, cron jobs, persistent disk |

> **Frontend (Vercel):** karena cold start ±30–60 dtk, pastikan UI menangani
> keterlambatan request pertama setelah idle (loading state / retry), bukan
> timeout pendek.

---

## 0. Prasyarat (sekali saja, sebelum deploy)

- [x] Repository sudah di-push ke GitHub (`master`).
- [x] Project Supabase sudah berisi tabel `hepatwin_compounds` (1.336 baris,
      1.231 `is_simulatable = TRUE`).
      ```sql
      SELECT count(*) FROM public.hepatwin_compounds;  -- harap 1336
      SELECT count(*) FROM public.hepatwin_compounds WHERE is_simulatable = TRUE;  -- harap 1231
      ```
- [x] Migration RLS sudah diterapkan
      (`supabase/migrations/20260805_01_rls_hepatwin_compounds.sql`): akses
      service-role saja (`service_role`), tanpa RLS untuk anon — lookup via
      service-role key di backend.
- [ ] URL frontend final (Vercel) sudah siap untuk `BACKEND_CORS_ORIGINS`
      (opsional saat masih `["*"]`).

---

## 1. Connect GitHub & Buat Service di Render

**Opsi A — Blueprint (`render.yaml`), direkomendasikan:**

1. Buka https://render.com → **New** → **Blueprint**.
2. Pilih repository `hepatwin-backend-py`.
3. Render membaca `render.yaml` → service `hepatwin-backend` (Free).
4. Set **nilai rahasia** (yang `sync: false`) manual di Dashboard
   (lihat §2) — Render tidak menimpa nilai yang Anda isi manual.
5. **Deploy Blueprint**.

**Opsi B — Manual (Web Service):**

1. **New** → **Web Service** → connect GitHub → pilih repository.
2. Isi form **Configure** sesuai tabel di bawah → **Create Web Service**.

Isian form **Configure New Web Service** (field → nilai):

| Field (label UI) | Nilai yang diisi | Catatan |
|---|---|---|
| **Name** | `hepatwin-backend` | Bebas; ini nama service di dashboard |
| **Language** | `Python 3` | Native build, tanpa Docker |
| **Branch** | `master` | Sesuai repo |
| **Region** | `Oregon (US West)` | Bebas; konsisten dengan `render.yaml` |
| **Root Directory** | *(kosong)* | Repo root — bukan monorepo |
| **Build Command** | `pip install -r requirements.txt` | Abaikan prefix `$` pada field |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | **WAJIB diganti** dari placeholder `gunicorn your_application.wsgi` — module FastAPI adalah `app.main` (`app/main.py`), bukan `main:app`; `$PORT` di-set otomatis oleh Render |
| **Instance Type** | `Free` (512 MB RAM) | Sesuai batasan Free Tier di atas |

3. Setelah service dibuat (Dashboard):
   - **Settings → Health Check Path** → `/health` (atau isi di Advanced saat
     create bila tersedia).
   - **Environment** → set variabel §2 (termasuk `PYTHON_VERSION=3.11.11`
     opsional, dan `DEBUG=false`).
   - Klik **Deploy** (manual) atau biarkan Auto-Deploy dari `master`.

---

## 2. Environment Variables (Dashboard Render → Service → Environment)

Set variabel berikut di Dashboard Render:

| Variable | Wajib? | Sumber nilai | Catatan |
|---|---|---|---|
| `DATABASE_URL` | **Ya** | Supabase → Project Settings → Database → Connection string (pooler/transaction) | SQLAlchemy; tambahkan `sslmode=require`; **kritis** — tanpa ini lookup 500 |
| `SUPABASE_URL` | Ya | Supabase → Project Settings → API → Project URL | `https://<ref>.supabase.co` |
| `SUPABASE_ANON_KEY` | Ya | Supabase → Project Settings → API → anon key | |
| `SUPABASE_SERVICE_ROLE_KEY` | **Ya** | Supabase → Project Settings → API → service_role key | **Rahasia — jangan diekspos ke frontend** |
| `BACKEND_CORS_ORIGINS` | Ya | URL frontend (Vercel) | JSON array: `["https://hepatwin.vercel.app"]`; `["*"]` sementara untuk uji |
| `AI_MODEL_PATH` | Opsional | default `app/models/model_gatnn_dnn.pt` | Sudah diset di `render.yaml` |
| `DEBUG` | Ya | — | **`false`** di produksi (menambah `timing_ms` bila true) |
| `PYTHON_VERSION` | Opsional | — | `3.11.11` (sudah diset di `render.yaml`) |

> **Port:** Render meng-set `PORT` otomatis (default **10000**) — **jangan**
> di-set manual; start command memakai `$PORT`.
>
> **Jangan commit `.env`** — semua nilai di atas diatur langsung di Dashboard
> Render (atau `render.yaml` untuk yang non-rahasia).

---

## 3. Build & Dependency (PyTorch CPU-only)

- `requirements.txt` memakai `--extra-index-url https://download.pytorch.org/whl/cpu`
  dengan specifier polos `torch>=2.3.1` — pip memilih wheel CPU-only karena
  versi `+cpu` dari index CPU sortir lebih tinggi dari versi plain PyPI
  (specifier `+cpu` tidak valid untuk `>=` di PEP 508). Build cepat dan
  memori saat instal < 512 MB.
- Wheel RDKit manylinux membutuhkan OpenMP (`libgomp.so.1`); image build
  native Render umumnya sudah menyediakannya. Bila import RDKit gagal dengan
  `libgomp.so.1: cannot open shared object file`, gunakan deployment Docker
  (snippet Dockerfile di §6) atau laporkan — jangan downgrade RDKit.
- `-e ./ml` di `requirements.txt` menginstal paket `hepatwin-ml` dari
  `ml/src` (featurization/model/explain dipakai `app/services/ai_engine.py`);
  `ml/` ikut ter-copy karena berada dalam repo.

**Verifikasi pasca-build (Render → Logs):**

```bash
python -c "import torch; print(torch.__version__)"   # harus berakhiran +cpu
python -c "import rdkit; print(rdkit.__version__)"
```

---

## 4. Deploy & Verifikasi

1. Klik **Deploy** (atau auto-deploy per push ke `master`).
2. Tunggu build selesai; service Free akan **spins down setelah 15 menit idle**
   dan cold start kembali ±30–60 detik pada request pertama — ini **normal**
   untuk Free Tier (bukan bug; lihat seksi batasan di atas).
3. **Verifikasi wheel torch CPU-only** (Render → Logs):
   ```bash
   python -c "import torch; print(torch.__version__)"   # harus berakhiran +cpu
   ```
   Bila tidak berakhiran `+cpu`, pin eksplisit `torch==<versi>+cpu` di
   `requirements.txt` lalu redeploy (lihat §6).
4. Setelah status **Live**, jalankan smoke test (ganti `https://<app>.onrender.com`):

```bash
# 1) Health — harus {"status":"ok","ai_engine_ready":true,...}
curl https://<app>.onrender.com/health

# 2) Debug PBPK (parameter alometrik & metrik exposure)
curl "https://<app>.onrender.com/api/v1/pbpk/debug?usia=40&jenis_kelamin=L&berat_badan_kg=70&tinggi_badan_cm=168&dosis_mg=10500&xlogp=0.86"

# 3) Autocomplete lookup (offline, deterministic)
curl "https://<app>.onrender.com/api/v1/compounds/autocomplete?q=acet&limit=3"

# 4) Simulasi penuh — skenario APAP 10.500 mg (respons merah / kritis)
curl -X POST https://<app>.onrender.com/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"hepatwin_id":"HT0012","dosis_mg":10500,"covariates":{"usia":40,"jenis_kelamin":"L","berat_badan_kg":70,"tinggi_badan_cm":168}}'
```

5. Verifikasi **error path** tetap benar: `404` (ID di luar katalog), `422`
   (senyawa biologik / SMILES tidak valid), `503` (model AI tidak termuat).

---

## 5. Checklist Pasca-Deploy

- [ ] `GET /health` → `ai_engine_ready: true` (model + kalibrator termuat).
- [ ] `POST /api/v1/simulate` mengembalikan `dili_score`, `risk_level`,
      `exposure_index`, `shap_detail`, `time_series_pbpk` — kontrak identik
      dengan lokal.
- [ ] `GET /api/v1/pbpk/debug` mengembalikan parameter alometrik (v2.3).
- [ ] Autocomplete lookup berfungsi (1.231 senyawa simulatable).
- [ ] `DEBUG=false` dan `BACKEND_CORS_ORIGINS` terisi di Dashboard Render.
- [ ] Cold start pertama ±30–60 dtk → request warm selanjutnya normal.
- [ ] Tidak ada secret di Logs (Render Logs tidak mencetak env vars).
- [ ] Deployment otomatis dari `master` aktif (Auto-Deploy).
- [ ] Aplikasi stateless: tidak ada state yang ditulis ke disk lokal
      (disk Free Tier ephemeral) — state hanya di Supabase.

---

## 6. Troubleshooting

| Gejala | Kemungkinan penyebab | Perbaikan |
|---|---|---|
| `ai_engine_ready:false` / `503` | Artefak model gagal dimuat | Cek path `AI_MODEL_PATH`; pastikan `app/models/*.pt` ter-track di git |
| Kalibrator gagal dimuat | `scikit-learn` tidak terinstal | Pastikan install `-r requirements.txt` (sudah memuat `scikit-learn>=1.7.2`) |
| `500` pada lookup | `DATABASE_URL` salah / tabel kosong | Cek koneksi + `sslmode=require`; verifikasi query §0 |
| CORS `403` dari frontend | `BACKEND_CORS_ORIGINS` belum berisi origin Vercel | Set origin eksplisit (bukan `*`) |
| `torch.__version__` tanpa `+cpu` | Resolver pip memilih wheel PyPI | Pin eksplisit `torch==<versi>+cpu` di `requirements.txt`, redeploy |
| RDKit error `libgomp.so.1` | OpenMP hilang di image | Gunakan Docker deployment (snippet di bawah) |
| Build OOM / lambat | Wheel CUDA terinstal | Pastikan `--extra-index-url` CPU ada; jangan install ulang dari PyPI |
| Cold start ±1 menit | Perilaku Free Tier (idle spin-down) | Normal; upgrade ke paid bila butuh selalu-hidup |

**Opsional — Docker deployment (alternatif native build):**

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
COPY ml ./ml
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV AI_MODEL_PATH=app/models/model_gatnn_dnn.pt
ENV DEBUG=false
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> Bila memakai Docker di Render, set **Start Command** ke
> `uvicorn app.main:app --host 0.0.0.0 --port $PORT` dan pastikan exposed
> port = `$PORT` (Render).

---

## 7. Referensi

- `render.yaml` — blueprint IaC (build/start command, health check, env vars).
- `README.md` — env vars, API, model artifacts, batasan.
- `supabase/migrations/20260805_01_rls_hepatwin_compounds.sql` — kebijakan RLS.
- `PBPK_Engine_Audit_Report_v2_3.md` — audit/validasi engine PBPK.
