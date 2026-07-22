# AGENTS.md — HepaTwin

Kontrak perilaku untuk coding agent. Bukan dokumentasi. Setiap aturan di sini mengubah cara kamu bertindak.

Bahasa: komunikasi dengan pengguna **Bahasa Indonesia**. Kode, nama variabel, dan commit message **Bahasa Inggris**.

---

## 1. HIERARKI KEBENARAN

Saat ada konflik, urutan ini menentukan. Yang di atas menang.

1. `docs/HepaTwin_PRD.md` — spesifikasi produk, otoritas tertinggi
2. `docs/HepaTwin_Arsitektur_BE_AI_dan_Roadmap.md` — arsitektur teknis, turunan PRD
3. Kode yang sudah ada di repo
4. Instruksi pengguna dalam sesi ini
5. Pengetahuan umummu

**Jika instruksi pengguna bertentangan dengan PRD: JANGAN langsung jalankan. Sebutkan pasal PRD yang bertentangan, lalu tanyakan apakah ini perubahan scope resmi.**

Baca PRD sebelum menyentuh kode di area yang belum kamu kerjakan di sesi ini. Jangan mengandalkan ringkasan di file ini — file ini hanya memuat aturan perilaku, bukan seluruh spesifikasi.

---

## 2. KONTEKS PROYEK (30 detik)

HepaTwin adalah aplikasi web edukasi yang memvisualisasikan kerusakan hati akibat obat (DILI) dalam bentuk digital twin 3D. Untuk lomba GEMASTIK 2026, divisi Pengembangan Perangkat Lunak.

Dua mode:
- **Edukasi Mendalam** — 2 senyawa flagship (parasetamol, amoxicillin-clavulanate), visual zonal
- **Triase Umum** — input SMILES bebas, skor risiko + heatmap generik

Dua mesin komputasi:
- **Mesin A deterministik** — persamaan diferensial PK/PD untuk parasetamol
- **Mesin B probabilistik** — model ML dari struktur kimia untuk sisanya

Stack: FastAPI (backend, Railway) + React/React Three Fiber (frontend, Vercel). Repo ini adalah **backend + ML saja** kecuali dinyatakan lain.

Prinsip non-negosiabel: produk ini **BUKAN** pengganti uji toksisitas/klinis. Setiap keputusan teknis harus mendukung, bukan melemahkan, batas klaim ini.

---

## 3. LARANGAN MUTLAK

Melanggar salah satu ini adalah kegagalan tugas, sekalipun kode berjalan.

### 3.1 JANGAN mengisi konstanta ilmiah

File `app/engines/pkpd/constants.py` berisi `k_in`, `k_elim`, `k_meta`, `k_GSH`, `theta_thr` dengan nilai `None`. **Itu disengaja.** PRD §13 item #1 menandainya sebagai item validasi wajib anggota Farmasi.

- JANGAN isi dengan angka dari pengetahuanmu
- JANGAN isi dengan angka "masuk akal" atau placeholder yang terlihat nyata
- JANGAN hapus atau lemahkan `assert_ready()`
- JANGAN buat jalur bypass agar aplikasi bisa menyala tanpa konstanta

Hal yang sama berlaku untuk parameter peluruhan garis nomogram dan bentuk persamaan GSH.

Jika suatu tugas membutuhkan konstanta ini, **berhenti dan laporkan** bahwa tugas terblokir oleh PRD §13 #1.

### 3.2 JANGAN menambahkan prediksi pola zonal ke Mode Triase

PRD §4.2 menempatkan prediksi pola mekanisme spesifik (hepatoselular vs kolestatik) untuk Mode Triase **di luar scope versi ini**.

- `visual_pattern` untuk mode triase **selalu** bernilai `"heatmap_generik"`
- Tipe `VisualPatternTriase = Literal["heatmap_generik"]` tidak boleh diperluas
- JANGAN menambah model, fitur, atau heuristik yang menebak pola untuk SMILES bebas
- Test kontrak yang menegakkan ini tidak boleh dilonggarkan atau di-skip

Ini berlaku walaupun idenya bagus. Perluasan scope butuh revisi PRD, bukan commit.

### 3.3 JANGAN mengarang angka performa

- JANGAN menulis nilai AUC/akurasi/MCC yang bukan hasil eksekusi nyata
- JANGAN memakai angka target PRD (0,75–0,85) sebagai hasil
- JANGAN mengisi `model_meta.json` dengan angka contoh
- Jika belum ada hasil, tulis `null` dan katakan belum diukur

PRD §8.3 dan §14.5 mewajibkan pelaporan angka aktual apa adanya, termasuk bila di bawah target.

### 3.4 JANGAN menyentuh external test set di luar gerbang

External test set (Xu et al. 2015) hanya boleh dievaluasi **satu kali**, pada tahap yang ditentukan roadmap (Sprint 1 minggu 3 hari 4).

- JANGAN mengevaluasi model padanya untuk "cek cepat"
- JANGAN menyetel hyperparameter berdasarkan hasilnya
- JANGAN memakainya sebagai validation set

Jika diminta melakukannya lebih awal, peringatkan bahwa itu membatalkan status validasi eksternal.

### 3.5 JANGAN mengarang sitasi ilmiah

- JANGAN menulis nama penulis, tahun, judul jurnal, atau DOI dari ingatan
- JANGAN menambah referensi baru ke dokumen apa pun
- Sitasi yang boleh dipakai hanya yang sudah ada di PRD §15
- Jika docstring butuh sitasi yang belum ada, tulis `# TODO(farmasi): sitasi diperlukan`

### 3.6 JANGAN mengubah teks disclaimer

Teks disclaimer dikunci di PRD §14.2 dan ditandai non-negotiable. Perubahan apa pun — termasuk membuatnya dinamis — butuh persetujuan Ketua Tim dan anggota Farmasi. Ada usulan terbuka soal ini di dokumen arsitektur Bagian A.1; **usulan bukan persetujuan**.

### 3.7 JANGAN memberi nama farmakologis pada gugus yang belum divalidasi

`app/chem/smarts_library.py` punya `SMARTS_VALIDATED_BY_PHARMACY`. Hanya gugus di dalam himpunan itu yang boleh muncul di output explainability dengan nama farmakologis.

- Gugus belum tervalidasi boleh dipakai sebagai fitur model
- Gugus belum tervalidasi TIDAK boleh muncul di response API dengan nama
- JANGAN menambahkan nama ke `SMARTS_VALIDATED_BY_PHARMACY` sendiri

Dasar: PRD §8.5 dan §13 item #2.

### 3.8 JANGAN memakai dataset NCTR

PRD §8.4 mengecualikannya secara eksplisit karena merupakan sumber historis penyusun DILIrank — risiko data leakage.

### 3.9 JANGAN mengubah dependensi produksi tanpa alasan

`backend/requirements.txt` hanya untuk **inference**. Jangan tambahkan pustaka training, plotting, atau notebook ke sana. Ukuran image berdampak langsung pada NFR waktu respons (PRD §6).

### 3.10 JANGAN membiarkan model tanpa bobot terlatih berjalan tanpa penanda

Bila artefak model (`model.pt` atau setara) tidak berhasil dimuat, sistem boleh tetap berjalan dengan bobot inisialisasi acak **hanya untuk keperluan development**, dan **wajib** menandainya secara eksplisit di response (`model_status` atau field setara). Dilarang mengembalikan skor dari model tak terlatih tanpa penanda ini, di lingkungan manapun.

Ditambahkan dari temuan audit `docs/AUDIT_TASKS.md` F1, diselesaikan TA.3: `HybridAIEngine.model_status` (`"trained"` | `"untrained_random_weights"`), diekspos lewat `SimulationResponse.model_status` dan `GET /health` (`ai_weights_loaded`).

---

## 4. STRUKTUR REPO

```
hepatwin/
├── AGENTS.md                      file ini
├── CLAUDE.md                      satu baris: @AGENTS.md
├── docs/
│   ├── HepaTwin_PRD.md            otoritas tertinggi
│   └── HepaTwin_Arsitektur_BE_AI_dan_Roadmap.md
├── backend/                       MASUK ke Docker image
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                   routes_*.py, schemas.py
│   │   ├── engines/
│   │   │   ├── pkpd/              absorption, liver_napqi, nomogram, constants
│   │   │   └── ml/                predictor, backend_tabular, backend_gnn, explain
│   │   ├── chem/                  standardize, smarts_library, features
│   │   ├── core/                  config, cache, errors, registry
│   │   └── artifacts/             model.joblib, model_meta.json, train_fps.npz
│   ├── tests/
│   ├── requirements.txt           HANYA inference
│   └── Dockerfile
└── ml/                            TIDAK masuk Docker image
    ├── data/{raw,interim,processed}/
    ├── notebooks/
    ├── scripts/01_..07_*.py
    └── reports/
```

**Aturan penempatan:**
- Kode yang dipanggil saat request → `backend/app/`
- Script training, eksplorasi, analisis → `ml/scripts/` atau `ml/notebooks/`
- `ml/` boleh mengimpor dari `backend/app/`. Sebaliknya **dilarang**.

**Aturan tunggal terpenting:** `backend/app/chem/features.py` adalah satu-satunya sumber featurization. Script training mengimpornya, tidak menyalinnya. Featurizer yang berbeda antara training dan inference adalah bug paling sulit dilacak di sistem ini.

---

## 5. PERINTAH

```bash
# Setup
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Jalankan API
uvicorn app.main:app --reload --port 8000

# Test
pytest tests/ -v
pytest tests/ -v -m "not slow"          # lewati test lambat
pytest tests/test_contract.py -v         # test kontrak API

# Lint & format
ruff check app/ && ruff format app/
mypy app/

# Pipeline ML (urut, dari ml/)
python scripts/01_download.py
python scripts/02_resolve_smiles.py
python scripts/03_standardize.py
python scripts/04_dedup_split.py
python scripts/05_train_baseline.py
python scripts/06_train_production.py
python scripts/07_external_eval.py       # HANYA sekali, lihat §3.4

# Docker
docker build -t hepatwin-api ./backend
docker images hepatwin-api --format "{{.Size}}"   # target ≤ 1,5 GB
```

Jika perintah di atas gagal karena file belum ada, itu wajar — repo dibangun bertahap. Laporkan, jangan mengarang implementasi yang belum dijadwalkan.

---

## 6. KONVENSI KODE

- Python 3.11, type hints wajib pada semua fungsi publik
- Pydantic v2 untuk seluruh skema API
- `snake_case` fungsi/variabel, `PascalCase` kelas, `UPPER_SNAKE` konstanta
- Docstring pada setiap fungsi ilmiah, menyebut pasal PRD yang mendasarinya
- Tanpa `print()` di `backend/app/` — gunakan `logging`
- Tanpa nilai ajaib. Konstanta ke `config.py` atau `constants.py`
- Error selalu lewat taksonomi di `core/errors.py`, jangan lempar `Exception` telanjang
- Stack trace tidak pernah masuk response API

Commit message: `<area>: <apa yang berubah>` — contoh `chem: add InChIKey dedup helper`. Area yang sah: `api`, `chem`, `pkpd`, `ml`, `core`, `tests`, `docs`, `infra`.

---

## 7. ALUR KERJA PER JENIS TUGAS

### 7.1 Sebelum tugas apa pun

1. Baca pasal PRD yang relevan dengan area yang akan disentuh
2. Cek §3 file ini — apakah tugas menyentuh larangan?
3. Jika ya → berhenti, laporkan, tanyakan
4. Jika tidak → lanjut

### 7.2 Menambah atau mengubah endpoint

1. Definisikan/perbarui skema di `app/api/schemas.py` lebih dulu
2. Cek apakah bentuk response cocok dengan PRD §7.1 langkah 4
3. Field baru di luar PRD → tandai `[EKSTENSI]` di docstring dan **laporkan ke pengguna**, karena frontend perlu tahu
4. Implementasi route
5. Tambah test integrasi di `tests/`
6. Jalankan `pytest tests/test_contract.py` — kontrak tidak boleh rusak

### 7.3 Menyentuh Mesin A (PK/PD)

1. Baca PRD §8.1 sepenuhnya sebelum mengubah apa pun
2. Persamaan sudah ditetapkan PRD — implementasikan apa adanya, jangan "diperbaiki"
3. Konstanta → §3.1, jangan diisi
4. Gunakan `solve_ivp` metode `LSODA` (sistem stiff saat overdosis)
5. Tangani kasus singular `ka ≈ ke` dengan bentuk limit
6. Test wajib lulus: nomogram di t=4 jam bernilai tepat sesuai anchor; dosis terapetik di bawah garis; overdosis memotong ke atas

### 7.4 Menyentuh Mesin B (ML)

1. Cek `ML_BACKEND` di env — `gnn` atau `tabular`. Keduanya harus tetap memenuhi `DILIBackend` Protocol
2. Perubahan featurizer → **wajib latih ulang model**. Model lama + featurizer baru = prediksi salah tanpa error. Laporkan konsekuensi ini
3. Perubahan `feature_names()` → perbarui `model_meta.json`, dan tambahkan assert bahwa panjang fitur cocok dengan artefak
4. SHAP hanya boleh mengekspos fitur berprefiks `smarts::` yang lolos `validated_library()`
5. Jangan mengubah seed atau split tanpa menyebutkan bahwa angka lama jadi tidak sebanding

### 7.5 Pipeline data

1. Script dijalankan berurutan `01` → `07`. Jangan lompat
2. Setiap script idempoten — aman dijalankan ulang, hasil sama
3. Panggilan API eksternal wajib di-cache ke disk. Jangan hit ulang layanan yang sama untuk input yang sama
4. Hormati rate limit layanan eksternal. Cek dokumentasi resminya, jangan menebak angkanya
5. Dedup memakai **blok pertama InChIKey (14 karakter)**, bukan string SMILES
6. Senyawa tumpang tindih dibuang dari **external test**, bukan dari training
7. Setiap script menulis ringkasan ke `ml/reports/` — berapa baris masuk, berapa keluar, berapa hilang di tiap filter

**Catatan penting:** DILIrank berisi nama obat, bukan SMILES. Langkah resolusi nama → struktur diperlukan sebelum data bisa dipakai. Tingkat keberhasilan tidak akan 100%; catat kegagalannya, jangan menambal dengan tebakan struktur.

### 7.6 Menambah dependensi

1. Tanya dulu: apakah dipakai saat inference atau hanya saat training?
2. Inference → `backend/requirements.txt`, dan laporkan dampaknya ke ukuran image
3. Training → `requirements-dev.txt`
4. Pustaka besar (torch, torch-geometric) → laporkan ukuran sebelum menambah, cek terhadap batas 1,5 GB

---

## 8. GERBANG VERIFIKASI SEBELUM MENYATAKAN SELESAI

Jangan pernah menyatakan tugas selesai sebelum semua yang berlaku terpenuhi.

- [ ] `pytest tests/ -v` lulus
- [ ] `ruff check app/` bersih
- [ ] `mypy app/` bersih pada file yang disentuh
- [ ] Test kontrak lulus: response mode triase selalu `heatmap_generik`
- [ ] Test regresi data lulus: nol overlap InChIKey antara train dan external test
- [ ] Tidak ada konstanta PD yang terisi (jika menyentuh `pkpd/`)
- [ ] Tidak ada angka performa karangan di file mana pun
- [ ] Field API baru sudah dilaporkan sebagai `[EKSTENSI]`
- [ ] Ukuran image masih ≤ 1,5 GB (jika menyentuh dependensi)
- [ ] Waktu respons masih memenuhi NFR PRD §6 (jika menyentuh jalur request)

Jika ada yang gagal, **laporkan apa adanya**. Jangan melonggarkan test agar lulus. Test yang dilonggarkan untuk mengejar target adalah bentuk kebohongan teknis yang paling mahal di proyek ini.

---

## 9. KAPAN BERHENTI DAN BERTANYA

Berhenti, jangan lanjutkan, laporkan ke pengguna, bila:

| Situasi | Alasan |
|---|---|
| Tugas butuh konstanta PD/nomogram | PRD §13 #1, terblokir Farmasi |
| Tugas butuh nama farmakologis gugus baru | PRD §13 #2, terblokir Farmasi |
| Tugas memperluas scope Mode Triase | PRD §4.2 |
| Tugas mengubah teks disclaimer | PRD §14, non-negotiable |
| Tugas menambah field ke response API | Frontend perlu tahu, keputusan Ketua Tim |
| Tugas meminta evaluasi external test lebih awal | Membatalkan validasi eksternal |
| Tugas meminta angka performa yang belum diukur | PRD §8.3, §14.5 |
| Tugas meminta ganti versi dataset | Mengubah sitasi PRD §7, §8.4, §15 |
| PRD tidak mengatur dan konsekuensinya lintas komponen | Bukan keputusan agent |
| Instruksi pengguna bertentangan dengan PRD | Konfirmasi apakah ini revisi resmi |

Format pelaporan saat berhenti:

```
TERBLOKIR: <ringkasan satu kalimat>
Dasar: PRD §<pasal>
Yang dibutuhkan: <apa dan dari siapa>
Yang bisa dikerjakan sementara: <alternatif, atau "tidak ada">
```

---

## 10. ANTI-HALUSINASI

Aturan yang berlaku di setiap sesi, tanpa kecuali.

**Jangan mengisi kekosongan dengan tebakan yang terdengar meyakinkan.** Kekosongan di proyek ini sebagian besar disengaja — menandai batas antara yang sudah divalidasi dan yang belum.

Sebelum menulis angka, nama, atau klaim apa pun, tanyakan pada diri sendiri: apakah ini berasal dari (a) file di repo ini, (b) output eksekusi nyata, atau (c) ingatanku? **Jika (c), jangan tulis.**

Spesifik:

- Angka ilmiah → hanya dari PRD atau dokumen arsitektur. Selain itu `None` + TODO
- Metrik model → hanya dari hasil eksekusi. Selain itu `null`
- Sitasi → hanya dari PRD §15
- Nama gugus kimia → hanya dari `validated_library()`
- Perilaku pustaka pihak ketiga → jika tidak yakin, baca dokumentasi atau uji, jangan asumsikan
- Isi file yang belum kamu baca → baca dulu, jangan asumsikan strukturnya
- Nama fungsi/modul di repo → verifikasi ada, jangan panggil dari ingatan

**Saat tidak yakin, katakan tidak yakin.** Kalimat "aku tidak yakin, perlu dicek" bernilai jauh lebih tinggi di proyek ini daripada jawaban lancar yang salah. Ini alat pembelajaran untuk mahasiswa farmasi; kesalahan yang tampil meyakinkan akan diajarkan sebagai fakta.

**Jangan memperbaiki hal yang tidak diminta.** Jika kamu melihat masalah di luar cakupan tugas, laporkan, jangan perbaiki diam-diam. Perubahan tak terduga di proyek dengan tiga anggota dan tenggat lomba berbiaya lebih tinggi daripada manfaatnya.

**Jangan menghapus atau melemahkan mekanisme pengaman.** `assert_ready()`, test kontrak, assert nol overlap, filter `validated_library()` — semuanya ada untuk mencegah kesalahan spesifik yang sudah teridentifikasi. Jika salah satunya menghalangi tugasmu, itu sinyal tugasnya yang perlu ditinjau, bukan pengamannya.

---

## 11. STATUS PROYEK

Perbarui bagian ini setiap akhir sprint.

```
Sprint aktif      : Sprint 0 — Fondasi (audit rekonsiliasi dev-vedo TA.1-TA.9 selesai, lihat docs/AUDIT_TASKS.md)
ML_BACKEND        : belum ditentukan (gerbang kelayakan Sprint 1 minggu 2)
Konstanta PD      : BELUM tervalidasi Farmasi → Mesin A (paracetamol) & nomogram terblokir via assert_ready()
SMARTS tervalidasi: 0 dari 9 (SMARTS_VALIDATED_BY_PHARMACY kosong di app/services/ai_engine.py)
Model GNN         : BELUM ada bobot terlatih (models/model.pt tidak ada) → HybridAIEngine.model_status = "untrained_random_weights"
External test     : BELUM dibuka
Metrik aktual     : belum ada
Audit dev-vedo    : TA.1, TA.2, TA.3, TA.4, TA.5, TA.6, TA.7, TA.8, TA.9 selesai (2026-07-22).
                    TA.4: Ketua Tim memutuskan pertahankan compound_id/smiles_string,
                    adopsi model_status permanen. TA.6 (cache.py) berdiri sendiri,
                    belum diwiring ke /simulate (butuh model_version nyata, EXECUTION_PLAN T1.18).
MOCK_MODE         : tersedia (default False) — /simulate mengembalikan response dummy
                    (model_status="mock") tanpa menyentuh Mesin A/B saat aktif
Keputusan tertunda: 6 item arsitektur (Bagian I) + TA.4 item #3 (adopsi field
                    [EKSTENSI] lain: engine/model_version/abstained/applicability_domain
                    — masih belum diputuskan, lihat docs/AUDIT_TASKS.md)
```
