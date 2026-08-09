# Deployment Checklist — HepaTwin Backend ke FastAPI Cloud (Hobby / Free Tier)

Checklist langkah-demi-langkah deployment backend HepaTwin ke **FastAPI Cloud**
(Hobby / free tier) untuk kebutuhan **penyisihan GEMASTIK** — backend dapat
diakses publik oleh frontend dan juri selama proses penyisihan. Bukan target
high-traffic dan bukan production berskala besar.

Semua langkah di dokumen ini ditulis berdasarkan **dokumentasi resmi FastAPI
Cloud** (fastapicloud.com/docs, status saat dokumen ini ditulis) dan kondisi
aktual repository `hepatwin-backend-py`. Hal yang belum terdokumentasi resmi
ditandai **perlu verifikasi** — jangan dianggap pasti.

- **Repo:** `farisakbar28/hepatwin-backend-py`, branch `master`
- **Entrypoint:** `app.main:app` — FastAPI Cloud **auto-detect** aplikasi pada
  layout `app/main.py` (lihat §1). Tidak perlu start command manual.
- **Dependencies:** di-install oleh FastAPI Cloud dari `requirements.txt`
  (lihat §4).
- **Kebutuhan:** Supabase (PostgreSQL) dengan tabel `hepatwin_compounds`
  (1.336 baris) + kebijakan RLS; artefak model di `app/models/` (sudah
  tracked, tidak di-ignore).

---

## FastAPI Cloud Hobby Tier — yang Wajib Diketahui

| Aspek | Fakta (sumber resmi) |
|---|---|
| **Harga** | **Hobby = $0/bulan**, tanpa kartu kredit (Pro $20/seat/bulan) |
| **Scale-to-zero** | **Diaktifkan secara default** — bila tidak ada traffic, app di-scale ke 0 instance dan bangun kembali saat ada request. Request pertama setelah idle menambah cold start |
| **Resource limit (RAM/CPU)** | **Tidak dipublikasikan secara numerik** oleh FastAPI Cloud saat ini (masih beta/early rollout) — *perlu verifikasi* dengan mencoba deployment aktual |
| **Python** | Semua versi Python yang masih didukung (**3.10+**); default versi stabil terbaru |
| **URL publik** | `https://<app-name>.fastapicloud.dev` — **HTTPS otomatis** |
| **GitHub integration** | Tersedia: hubungkan repo di Dashboard (App → Settings → Source Repository); push ke branch default memicu build + deploy otomatis |
| **Instalasi dependency** | Otomatis dari `requirements.txt` atau `pyproject.toml` |
| **Upload file** | Menghormati `.gitignore`; bisa dikustomisasi via `.fastapicloudignore` |

> **Frontend (Vercel):** karena scale-to-zero default, request pertama setelah
> idle akan lambat (cold start: boot ulang + muat model torch/RDKit). Pastikan
> UI menangani keterlambatan ini (loading state / retry), bukan timeout pendek.

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

## 1. Siapkan Dependency & Entrypoint

**CLI FastAPI Cloud (`fastapi deploy`) tersedia lewat group `fastapi[standard]`.**
`requirements.txt` sudah mendeklarasikan `fastapi[standard]>=0.111.0`, jadi CLI
ikut ter-install saat `pip install -r requirements.txt` (keputusan ini
memang mengubah baris dependency — disetujui, lihat §9).

**Entrypoint:** repo ini memakai layout `app/main.py` → FastAPI Cloud
**auto-detect** instance `app` (tanpa perlu konfigurasi entrypoint). Verifikasi
lokal wajib dilakukan:

```bash
fastapi dev        # jalankan dari root repo, tanpa argumen path
```

Bila `fastapi dev` berjalan tanpa error tanpa argumen path, maka
`fastapi deploy` akan bekerja dengan deteksi yang sama. (Jika nanti app
dipindah ke lokasi non-standar, konfigurasi eksplisit dapat dilakukan lewat
`[tool.fastapi] entrypoint = "..."` di `pyproject.toml`.)

**Python version:** di-pin via file `.python-version` di root repo (isi:
`3.11.11`) — FastAPI Cloud memakai versi tersebut (keputusan disetujui, lihat
§9). Alternatif yang setara: field `requires-python` di `pyproject.toml` root.

---

## 2. Login & Deploy Pertama

```bash
# 1) Pastikan CLI tersedia (lihat §1), lalu login
fastapi login          # browser akan terbuka untuk autentikasi

# 2) Set environment variables (lihat §3)

# 3) Deploy dari root repo
fastapi deploy
```

Output yang diharapkan:

```text
Deploying to FastAPI Cloud...
🚀 Preparing for liftoff! Almost there...
✅ Deployment successful!
🐔 Ready the chicken! Your app is ready at https://<app-name>.fastapicloud.dev
```

- CLI meng-upload kode (menghormati `.gitignore`; kustomisasi via
  `.fastapicloudignore` bila perlu), lalu FastAPI Cloud meng-install
  dependencies dan men-deploy app.
- HTTPS aktif otomatis pada URL `https://<app-name>.fastapicloud.dev`.

---

## 3. Environment Variables

Set lewat **CLI** atau **Dashboard** (App → Environment Variables; toggle
**Secret** untuk nilai rahasia; dukungan bulk-import format `.env`):

```bash
fastapi cloud env set DATABASE_URL "postgresql://..."
fastapi cloud env set SUPABASE_URL "https://<ref>.supabase.co"
fastapi cloud env set --secret SUPABASE_ANON_KEY "..."
fastapi cloud env set --secret SUPABASE_SERVICE_ROLE_KEY "..."
fastapi cloud env set BACKEND_CORS_ORIGINS '["https://hepatwin.vercel.app"]'
fastapi cloud env set DEBUG "false"
```

| Variable | Wajib? | Sumber nilai | Catatan |
|---|---|---|---|
| `DATABASE_URL` | **Ya** | Supabase → Project Settings → Database → Connection string (pooler/transaction) | SQLAlchemy; tambahkan `sslmode=require`; **kritis** — tanpa ini lookup 500 |
| `SUPABASE_URL` | Ya | Supabase → Project Settings → API → Project URL | `https://<ref>.supabase.co` |
| `SUPABASE_ANON_KEY` | Ya | Supabase → Project Settings → API → anon key | **Rahasia → `--secret`** |
| `SUPABASE_SERVICE_ROLE_KEY` | **Ya** | Supabase → Project Settings → API → service_role key | **Rahasia → `--secret`**; jangan diekspos ke frontend |
| `BACKEND_CORS_ORIGINS` | Ya | URL frontend (Vercel) | JSON array: `["https://hepatwin.vercel.app"]`; `["*"]` sementara untuk uji |
| `AI_MODEL_PATH` | Opsional | default `app/models/model_gatnn_dnn.pt` | Path relatif terhadap repo root |
| `DEBUG` | Ya | — | **`false`** di produksi (menambah `timing_ms` bila true) |

> **Jangan commit `.env`** — semua nilai di atas diatur langsung di FastAPI
> Cloud (CLI/dashboard), bukan di repository.

---

## 4. Build & Dependency (PyTorch CPU-only)

- FastAPI Cloud meng-install dependencies dari `requirements.txt` di build
  cloud. `requirements.txt` memakai
  `--extra-index-url https://download.pytorch.org/whl/cpu` dengan specifier
  polos `torch>=2.3.1` — pip memilih wheel **CPU-only** karena versi `+cpu`
  dari index CPU sortir lebih tinggi dari versi plain PyPI. Ini menjaga ukuran
  instal & RAM tetap hemat (penting untuk tier gratis dengan resource
  terbatas) — verifikasi pasca-deploy: `torch.__version__` berakhiran `+cpu`.
- `requirements.txt` meng-install paket `hepatwin-ml` dari **wheel
  pre-built** `ml/dist/hepatwin_ml-0.1.0-py3-none-any.whl` (dipakai
  `app/services/ai_engine.py`); `ml/` ikut ter-upload karena berada dalam
  repo dan tidak di-ignore.
  > ⚠️ Awalnya memakai `-e ./ml` (editable) lalu `./ml` (build source di
  > cloud) — keduanya gagal di build cloud dengan `error in 'egg_base'
  > option: 'src' does not exist` (layout src `packages.find where=["src"]`
  > + build source tidak stabil di environment build cloud). Solusi: install
  > **wheel pre-built** yang tidak memerlukan langkah build di cloud.
  > Rebuild wheel setelah mengubah `ml/src`:
  > `python -m pip wheel ./ml -w ml/dist`
- Artefak model (`app/models/*.pt`, `*.pkl`) ter-track di git dan **tidak**
  di-ignore (`.gitignore` mengecualikan `*.pt` hanya di luar `app/models/`) →
  ikut ter-upload.

**Verifikasi pasca-deploy (via Logs / dashboard):**

```bash
python -c "import torch; print(torch.__version__)"   # harus berakhiran +cpu
python -c "import rdkit; print(rdkit.__version__)"
python -c "import hepatwin_ml; print('hepatwin_ml OK')"
```

---

## 5. Verifikasi & Smoke Test

1. Tunggu status deployment sukses (CLI atau dashboard).
2. Request pertama setelah deploy akan memuat cold start (boot + muat model
   torch/RDKit) — **normal**, terutama dengan scale-to-zero.
3. Jalankan smoke test (ganti `https://<app-name>.fastapicloud.dev`):

```bash
# 1) Health — harus {"status":"ok","ai_engine_ready":true,...}
curl https://<app-name>.fastapicloud.dev/health

# 2) Debug PBPK (parameter alometrik & metrik exposure)
curl "https://<app-name>.fastapicloud.dev/api/v1/pbpk/debug?usia=40&jenis_kelamin=L&berat_badan_kg=70&tinggi_badan_cm=168&dosis_mg=10500&xlogp=0.86"

# 3) Autocomplete lookup (offline, deterministic)
curl "https://<app-name>.fastapicloud.dev/api/v1/compounds/autocomplete?q=acet&limit=3"

# 4) Simulasi penuh — skenario APAP 10.500 mg (respons merah / kritis)
curl -X POST https://<app-name>.fastapicloud.dev/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"hepatwin_id":"HT0012","dosis_mg":10500,"covariates":{"usia":40,"jenis_kelamin":"L","berat_badan_kg":70,"tinggi_badan_cm":168}}'
```

4. Verifikasi **error path** tetap benar: `404` (ID di luar katalog), `422`
   (senyawa biologik / SMILES tidak valid), `503` (model AI tidak termuat).

---

## 6. Checklist Pasca-Deploy

- [ ] `GET /health` → `ai_engine_ready: true` (model + kalibrator termuat).
- [ ] `POST /api/v1/simulate` mengembalikan `dili_score`, `risk_level`,
      `exposure_index`, `shap_detail`, `time_series_pbpk` — kontrak identik
      dengan lokal.
- [ ] `GET /api/v1/pbpk/debug` mengembalikan parameter alometrik (v2.3).
- [ ] Autocomplete lookup berfungsi (1.231 senyawa simulatable).
- [ ] `DEBUG=false` dan `BACKEND_CORS_ORIGINS` terisi (origin frontend Vercel).
- [ ] `torch.__version__` berakhiran `+cpu` di Logs.
- [ ] Tidak ada secret tercetak di Logs (nilai rahasia di-set via `--secret`).
- [ ] Aplikasi stateless: tidak ada state yang ditulis ke disk lokal — state
      hanya di Supabase (aman dengan disk ephemeral/scale-to-zero).

---

## 7. Deployment Berikutnya & GitHub Integration

**CLI:** dari root repo, cukup `fastapi deploy` lagi — CLI meng-upload versi
terbaru dan melakukan rolling deploy.

**GitHub Integration (opsional):** Dashboard → App → Settings → **Source
Repository** → hubungkan repo `hepatwin-backend-py`. Push ke branch default
(`master`) memicu build + deploy otomatis, dengan status check di GitHub.

---

## 8. Troubleshooting

| Gejala | Kemungkinan penyebab | Perbaikan |
|---|---|---|
| `ai_engine_ready:false` / `503` | Artefak model gagal dimuat | Cek `AI_MODEL_PATH`; pastikan `app/models/*.pt` ter-track di git (bukan di-ignore) |
| Import `hepatwin_ml` error | Wheel `hepatwin_ml` tidak ditemukan / gagal install | Pastikan `ml/dist/hepatwin_ml-0.1.0-py3-none-any.whl` ter-track di git dan `requirements.txt` merujuk wheel tersebut; rebuild wheel bila `ml/src` berubah (`python -m pip wheel ./ml -w ml/dist`) |
| `500` pada lookup | `DATABASE_URL` salah / tabel kosong | Cek koneksi + `sslmode=require`; verifikasi query §0 |
| CORS `403` dari frontend | `BACKEND_CORS_ORIGINS` belum berisi origin Vercel | Set origin eksplisit (bukan `*`) |
| `torch.__version__` tanpa `+cpu` | Resolver pip memilih wheel PyPI | Pin eksplisit `torch==<versi>+cpu` di `requirements.txt`, deploy ulang |
| Cold start lambat (request pertama) | Scale-to-zero default (app tidur saat idle) | Normal untuk Hobby tier; tetap hidup bila butuh: naikkan ke Pro (scale-to-zero bisa dimatikan) |
| Build OOM / lambat | Wheel CUDA terinstal | Pastikan `--extra-index-url` CPU ada; jangan install ulang dari PyPI |

---

## 9. Keputusan Deployment (sudah diterapkan)

- **`requirements.txt`:** `fastapi>=0.111.0` → `fastapi[standard]>=0.111.0`
  (CLI `fastapi deploy` ikut ter-install).
- **`Procfile` dihapus** — FastAPI Cloud tidak memakainya (deployment via
  CLI / GitHub Integration).
- **File `.python-version` ditambahkan** (isi `3.11.11`) — pin versi Python
  deterministik sesuai rekomendasi docs FastAPI Cloud.

---

## 10. Referensi

- Dokumentasi resmi FastAPI Cloud: https://fastapicloud.com/docs
  (Getting Started / Migrate an Existing Project; Environment Variables;
  Install Dependencies; GitHub Integration; Pricing).
- `README.md` — env vars, API, model artifacts, batasan.
- `supabase/migrations/20260805_01_rls_hepatwin_compounds.sql` — kebijakan RLS.
- `PBPK_Engine_Audit_Report_v2_3.md` — audit/validasi engine PBPK.
