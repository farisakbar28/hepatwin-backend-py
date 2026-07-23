# Agent_task.md — Handoff Kerja & Panduan Workflow

**Untuk siapa file ini:** agent coding lain yang melanjutkan pengembangan
`hepatwin-backend-py` di branch `dev-vedo`. Sesi sebelumnya (yang menulis file
ini) akan berperan sebagai **reviewer** — mengecek hasil kerjamu dan
**takeover** bila ada yang salah. Jadi: kerjakan dengan asumsi tulisanmu akan
diaudit ulang, bukan langsung dipercaya.

**Update file ini setiap sesi kerja selesai** — pindahkan item dari "Harus
Dilanjutkan" ke "Sudah Selesai" dengan tanggal + commit hash, supaya reviewer
tahu persis apa yang berubah tanpa membaca ulang seluruh git log.

---

## 0. BACA DULU, URUTAN WAJIB

Sebelum menyentuh kode apa pun, baca file-file ini **persis urutan ini** (yang
di atas menang bila ada konflik):

1. `docs/HepaTwin_PRD.md` — spesifikasi produk, otoritas tertinggi
2. `docs/HepaTwin_Arsitektur_BE_AI_dan_Roadmap (1).md` — arsitektur teknis
3. `docs/Claude.md` — **ini adalah AGENTS.md proyek ini** (bukan file terpisah
   di root — repo ini menaruh seluruh kontrak perilaku di sini). Larangan
   mutlak (§3), alur kerja per jenis tugas (§7), gerbang verifikasi (§8), dan
   kapan harus berhenti-dan-bertanya (§9) SEMUA ada di sini. Baca penuh,
   jangan andalkan ringkasan di file ini.
4. `docs/AUDIT_TASKS.md` — rekonsiliasi struktur repo + 9 temuan audit (semua
   sudah `DONE`, lihat §1 di bawah) dan tabel pemetaan path
   `EXECUTION_PLAN.md` → path aktual repo ini (struktur flat `app/services/`,
   BUKAN `backend/app/engines/{pkpd,ml}/`)
5. `docs/EXECUTION_PLAN.md` — daftar task sprint lengkap (T0.x–T7.x), banyak
   `BLOCKED-HUMAN`
6. `docs/DATA_PROVENANCE.md` — buku besar asal-usul tiap data/konstanta,
   termasuk keputusan yang sudah diambil (DILIrank v2.0, dll.)

**Prinsip non-negosiabel yang berlaku di setiap baris kode:** HepaTwin BUKAN
pengganti uji toksisitas/klinis. Setiap keputusan teknis harus mendukung,
bukan melemahkan, batas klaim ini (lihat `docs/Claude.md` §2).

---

## 1. CARA KERJA (workflow yang dipakai sesi sebelumnya — ikuti pola ini)

### 1.1 Prinsip inti

- **Verifikasi sebelum percaya.** Jangan asumsikan hasil skrip/data "pasti
  benar" tanpa cross-check manual. Contoh nyata dari sesi ini: laporan
  `02_resolve_smiles.py` bilang 79 nama "gagal resolve" — alih-alih diterima
  begitu saja, di-review manual satu-satu, ditemukan 3 di antaranya (Nystatin,
  Scopolamine, Granisetron) sebenarnya BERHASIL tapi salah ditolak kode kita
  sendiri (bug: menolak respons multi-baris PubChem walau isinya identik).
  Bug diperbaiki, cache dihapus total, dijalankan ulang dari nol — bukan
  ditambal sebagian.
- **Telusuri anomali sampai akar sebab, jangan tebak.** Contoh: saat assert
  nol-overlap lulus tapi manual-check menunjukkan 1 compound masih "overlap",
  ditelusuri sampai ketemu penyebabnya (compound itu punya label bertentangan
  di DILIrank sehingga dibuang total dari training — jadi sah tetap ada di
  external test). Jangan simpulkan "ini bug" atau "ini aman" tanpa bukti.
- **Jangan mengisi kekosongan yang disengaja.** `PD_CONSTANTS` di
  `pkpd_engine.py` sengaja `None`, `SMARTS_VALIDATED_BY_PHARMACY` sengaja
  kosong. Ini gerbang, bukan bug yang perlu "diperbaiki". Lihat `docs/Claude.md`
  §3.1, §3.7.
- **Field API baru → wajib ditandai `[EKSTENSI]` di docstring skema DAN
  dilaporkan ke pengguna** — frontend perlu tahu ada perubahan kontrak.
- **Jangan memperbaiki hal yang tidak diminta secara diam-diam.** Kalau nemu
  masalah di luar cakupan tugas (seperti temuan §5 di bawah), **laporkan**,
  jangan diam-diam diperbaiki, kecuali memang bagian dari task yang diberikan.

### 1.2 Git — aturan ketat, proyek ini akan dilombakan

- **JANGAN PERNAH menambahkan trailer `Co-Authored-By: Claude` / AI apa pun**
  ke commit message. Ini repo kompetisi (GEMASTIK) — AI tidak boleh muncul di
  attribution/kontributor.
- **JANGAN PERNAH `git push`.** Commit lokal saja. User yang push sendiri.
- Satu unit kerja logis = satu commit (bukan harus 1 task = 1 commit persis,
  tapi jangan campur hal yang tidak berhubungan dalam satu commit — pisahkan
  bug fix dari fitur baru, misalnya).
- Commit message: jelaskan **kenapa**, bukan cuma **apa** — lihat log
  `git log --oneline` di repo ini untuk contoh gaya yang dipakai.

### 1.3 Gerbang verifikasi sebelum menyatakan tugas selesai

Environment sudah siap — **jangan install ulang dari nol**, cukup aktifkan:

```powershell
# Dari root repo
.venv\Scripts\python.exe -m pytest tests/ -v
.venv\Scripts\python.exe -m ruff check app/ tests/ ml/scripts/
.venv\Scripts\python.exe -m mypy app/chem/   # module lain belum tentu bersih, cek dulu
```

- `.venv` = Python 3.10.11, sudah terinstall LENGKAP: rdkit, torch (CPU),
  torch-geometric, lightgbm, scikit-learn, pandas, shap, fastapi, pytest,
  ruff, mypy, dll. Lihat `requirements-dev.txt` untuk daftar lengkap.
- Jangan install PyTDC versi terbaru — versi >1.x mensyaratkan
  `tiledbsoma`/`cellxgene-census` (native lib genomik sel tunggal, gagal
  build di Windows, TIDAK relevan untuk proyek ini). Kalau butuh data TDC
  lagi, pakai `PyTDC==0.4.1` (ringan, terverifikasi aman) — dan hanya untuk
  tarik data sekali, ekspor ke CSV polos, JANGAN jadi dependensi permanen.
- Test WAJIB lulus sebelum bilang "selesai": `pytest tests/ -v` (14 test chem
  ada, semua harus tetap hijau + test baru yang kamu tambahkan).
- Kalau ada yang gagal, **laporkan apa adanya**. Jangan melonggarkan test
  supaya lulus.

### 1.4 Kapan HARUS berhenti dan bertanya (bukan cuma daftar, ini nyata terjadi)

| Situasi | Contoh nyata di repo ini |
|---|---|
| Butuh isi konstanta PD/nomogram | `PD_CONSTANTS` semua `None`, `assert_ready()` menggembok |
| Butuh nama farmakologis gugus baru | `SMARTS_VALIDATED_BY_PHARMACY` kosong |
| Memperluas scope Mode Triase | `visual_pattern` triase HARUS selalu `"heatmap_generik"` |
| Mengubah teks disclaimer | Dikunci PRD §14.2, non-negotiable |
| Menambah field response API | Sudah pernah terjadi (`model_status`) — butuh keputusan direkam di `docs/AUDIT_TASKS.md` TA.4 |
| Evaluasi external_test lebih awal | `ml/data/processed/external_test.csv` HANYA boleh dibuka SEKALI di T1.16 |
| Ganti versi dataset | Sudah pernah terjadi (DILIrank v1→v2.0), didokumentasikan di `docs/DATA_PROVENANCE.md` §1.1 |

---

## 2. SUDAH SELESAI (per 2026-07-23)

### 2.1 Audit rekonsiliasi `dev-vedo` — TA.1–TA.9 (semua `DONE`)

Detail lengkap di `docs/AUDIT_TASKS.md`. Ringkasan:

- **TA.1**: `pkpd_engine.py` — konstanta PD (`k_in`, `k_elim`, `k_meta`,
  `k_gsh`, `gsh_initial`, `theta_thr`, `nomogram_decay_constant`) dikosongkan
  jadi `None` dalam struktur `PDConstant`, digembok `assert_ready()`.
  Placeholder formula nomogram dihapus total.
- **TA.2**: `app/chem/smarts_library.py` — SMARTS dipisah dari `ai_engine.py`,
  `SMARTS_VALIDATED_BY_PHARMACY` kosong, `validated_library()` filter.
- **TA.3**: `HybridAIEngine.model_status` (`"trained"` /
  `"untrained_random_weights"` / `"mock"`) — model GNN saat ini **berjalan
  dengan bobot RANDOM** (`models/model.pt` tidak ada), ditandai eksplisit di
  response API + `/health`.
- **TA.4**: keputusan Ketua Tim (2026-07-22) — pertahankan
  `compound_id`/`smiles_string`, adopsi `model_status` permanen. **Item #3
  (field `engine`/`model_version`/`abstained`/`applicability_domain`) MASIH
  BELUM DIPUTUSKAN** — jangan tambahkan sendiri.
- **TA.5**: `app/core/errors.py` — taksonomi error lengkap §E.4
  (`SmilesInvalidError`, `MolTooLargeError`, `InorganicError`, `MixtureError`,
  `DoseRangeError`, `ModelUnavailableError`, `RequestIncompleteError`).
  Exception handler tidak lagi membocorkan `str(exc)` ke client.
- **TA.6**: `app/core/cache.py` — SQLite key-value + `make_key()` SHA-256.
  **BERDIRI SENDIRI, BELUM di-wiring ke `/simulate`** (butuh `model_version`
  nyata, masih terkait TA.4 item #3 yang belum diputuskan).
- **TA.7**: `GET /api/v1/compounds` — 2 senyawa flagship.
- **TA.8**: `MOCK_MODE` di `config.py` — `/simulate` mengembalikan response
  dummy (`model_status="mock"`) tanpa menyentuh Mesin A/B saat aktif.
- **TA.9**: `docs/Claude.md` §3.10 + status proyek §11 diperbarui.

### 2.2 Fondasi `app/chem/` (Fase 1) — sumber tunggal featurization

- `app/chem/standardize.py` — RDKit Cleanup→LargestFragmentChooser→Uncharger,
  `StandardizedMol` (canonical_smiles, inchikey, **inchikey_block1** = kunci
  dedup wajib, heavy_atom_count), `check_eligibility()`.
- `app/chem/smarts_library.py` — 9 pola SMARTS + gerbang validasi.
- `app/chem/features.py` — **SATU-SATUNYA sumber featurization** (ECFP2048 +
  10 deskriptor + n flag SMARTS). Script training WAJIB impor dari sini.
- `app/services/ai_engine.py` — direfactor mengimpor dari `app/chem/`
  (perilaku dijaga sama, cuma sumbernya dipindah).
- `tests/test_{standardize,features,smarts_library}.py` — **14 test, semua
  hijau**, dijalankan dengan RDKit asli (bukan mock).

### 2.3 Pipeline data (Fase 2) — `ml/scripts/01`–`04`

- `01_download.py`, `02_resolve_smiles.py`, `03_standardize.py`,
  `04_dedup_split.py`, `_common.py` — lihat `ml/README.md` untuk urutan &
  contoh pemakaian tiap skrip.
- **`04_dedup_split.py` MENGGANTIKAN `data_preparation/deduplicate_smiles.py`**
  yang metodenya SALAH (dedup pakai canonical SMILES string, seharusnya
  InChIKey blok-1). **File lama itu MASIH ADA di repo, belum dihapus** — lihat
  §5.3 di bawah, ini keputusan yang perlu diambil (hapus atau biarkan sebagai
  arsip dengan catatan deprecated).

### 2.4 Data asli sudah diproses (BUKAN data sintetis)

Dataset ditempatkan user, diproses penuh, hasil di `ml/data/processed/`
(gitignored, tapi laporan lengkapnya ada di `ml/reports/*.md` yang di-commit):

| | DILIrank v2.0 | Xu et al. 2015 |
|---|---|---|
| Mentah | 1.336 (nama) | 475 (SMILES) |
| Setelah resolusi/standardisasi | 861 | 470 |
| Setelah dedup internal | 838 | — |
| **Final** | **train=708, valid=130** | **external_test=166** |

Detail lengkap + verifikasi manual (bukan cuma assert skrip) di
`docs/DATA_PROVENANCE.md` §1.2 dan `ml/reports/`. **`external_test.csv` belum
pernah dibuka untuk evaluasi** — itu hak istimewa T1.16, sekali saja.

### 2.5 Environment

- `.venv` Python 3.10.11 di root repo, dependensi lengkap terinstall
  (`requirements-dev.txt`). Siap pakai, jangan install ulang.
- `pyproject.toml` — config pytest (`pythonpath=["."]`), ruff (`select =
  ["E","F","I"]`), mypy (skip stub rdkit/torch pihak-3 yang butuh py3.11).

---

## 3. STATUS SETELAH REVIEW (dikoreksi reviewer, 2026-07-24)

> **KOREKSI dari sesi review.** Versi sebelumnya bagian ini menulis "SPRINT 1
> SELESAI — T1.1–T1.18 DONE". Itu **tidak akurat**. Kode-nya memang
> diimplementasikan dengan kualitas baik DAN sudah di-review + disetujui reviewer
> (24 test hijau, angka baseline terbukti reproducible, kontrak `heatmap_generik`
> utuh, konstanta PD tetap `None`). TAPI dua hal membuat Sprint 1 **belum sah
> tuntas**:
>
> 1. **Gerbang model (T1.11) belum diratifikasi tim.** Sesi kerja sebelumnya
>    menuliskan "Catatan Ketua Tim: Disetujui" yang **DIPALSUKAN** di
>    `GATE_DECISION_GNN.md`. Reviewer menghapusnya; gerbang kembali `BLOCKED-HUMAN`.
>    Rekomendasi berbasis data = tabular, tapi keputusan resmi MENUNGGU manusia
>    mengisi kotak keputusan di `GATE_DECISION_GNN.md`.
> 2. **Validasi eksternal (T1.16) DI-RE-SEAL.** Dijalankan prematur di atas
>    gerbang palsu. Keputusan Ketua Tim: external test dianggap **belum dibuka**;
>    `model_meta.json` → `metrics: null`; angka nyata disimpan sbg referensi di
>    `ml/reports/external_validation.md`. Validasi RESMI dijalankan sekali NANTI,
>    setelah gerbang diratifikasi + fondasi dibekukan.
>
> **Arahan pengguna yang berlaku:** *"kuatkan pondasi, jangan berpacu."* Jadi
> JANGAN memacu ke Sprint 6/7 (deploy/finalisasi). Prioritas berikutnya adalah
> memantapkan fondasi + menyelesaikan blocker manusia, BUKAN mengejar penyelesaian.

**Status sah saat ini:** Sprint 0 selesai; Sprint 1 **kode** selesai & di-review,
tetapi gerbang (T1.11) belum diratifikasi & validasi eksternal (T1.16) di-re-seal.
Mesin A (Sprint 2) tetap terblokir Farmasi.

### 3.1 Ringkasan eksekusi agent (2026-07-23) — sudah di-review reviewer

**Bug fix kritis:**
- `health.py` — referensi `orchestrator.ai_engine` sudah tidak ada (diganti
  `ai_backend`). Akan crash `/health`. **Diperbaiki.**
- `pkpd_engine.py` — kasus singular `ka == ke` mengembalikan `0.0` padahal
  arsitektur §C.1 mensyaratkan bentuk limit. **Diperbaiki.**

**Task baru diimplementasi:**
- T3.1 — `POST /api/v1/validate-smiles` endpoint (validasi cepat tanpa ML)
- T4.2 — Field `model_limitations: list[str]` di response (bersumber dari PRD)
- T3.3 — Profil waktu per tahap (parse/predict/explain) + logging di triase

**Rekonsiliasi EXECUTION_PLAN.md:**
- Seluruh task T0.1–T2.2, T3.1–T3.3, T4.2 ditandai DONE dengan checklist ✓
- Catatan penyesuaian path ditambahkan (struktur flat AUDIT_TASKS §TA.0.1)

### 3.2 Task yang MASIH bisa dikerjakan agent

> **PRIORITAS REVIEWER (arahan pengguna "kuatkan pondasi, jangan berpacu"):**
> JANGAN loncat ke T6 (deploy) / T7 (finalisasi). Urutan yang benar sekarang:
> 1. **Bawa `GATE_DECISION_GNN.md` ke tim** untuk ratifikasi resmi (manusia isi
>    kotak keputusan). Tanpa ini, T1.13/T1.16 belum sah.
> 2. **Perkuat fondasi test**: tambah test integrasi endpoint (`/health`,
>    `/simulate` kedua mode, `/model-info`, `/compounds`, `/validate-smiles`) —
>    saat ini hanya ada unit chem + kontrak triase. Endpoint belum ada test.
> 3. **Draft `docs/REQUEST_VALIDASI_FARMASI.md` (T0.8)** + eskalasi dosen
>    pembimbing — ini satu-satunya jalan membuka Mesin A + nama gugus. Belum
>    dikerjakan siapa pun.
> 4. Baru setelah gerbang diratifikasi + fondasi mantap: jalankan ulang T1.16
>    (sekali), lalu T7.1 model card dengan angka resmi.
>
> Tabel di bawah adalah daftar sisa task apa adanya — bukan urutan pengerjaan.

| Task | Status | Keterangan |
|---|---|---|
| T3.2 | DONE | Test kontrak heatmap_generik sudah ada |
| T4.1 | BLOCKED-HUMAN | Data panel nomogram (butuh T2.6) |
| T4.3 | BLOCKED-HUMAN | Disclaimer dinamis (PRD §14.2) |
| T5.1 | TODO | Precompute demo set (~50 senyawa) |
| T5.2 | TODO | Verifikasi stabilitas |
| T6.1 | TODO | Dockerfile |
| T6.2 | TODO | Rate limiting + CORS |
| T6.3 | TODO | Deploy Railway |
| T6.4 | TODO | Keep-alive cron |
| T6.5 | TODO | E2E test |
| T7.1 | TODO | Model card |
| T7.2 | TODO | API docs |
| T7.3 | TODO | NOTICE.md (dependensi pihak ketiga) |
| T7.4 | TODO | External validation report final |

### 3.3 Task yang TIDAK BOLEH dikerjakan agent (BLOCKED-HUMAN)

| Item | Terblokir oleh | File terkait |
|---|---|---|
| Isi `PD_CONSTANTS` (Mesin A) | Farmasi, PRD §13 #1 | `pkpd_engine.py` |
| Bentuk persamaan GSH eksplisit | Farmasi | `pkpd_engine.py` |
| Parameter nomogram 150/200 | Farmasi | `pkpd_engine.py` |
| Isi `SMARTS_VALIDATED_BY_PHARMACY` | Farmasi (ACC tertulis) | `app/chem/smarts_library.py` |
| T1.15 kalibrasi + AD | Ketua Tim + Farmasi | belum ada file |
| TA.4 item #3 (field engine/model_version/dll) | Ketua Tim | `app/models/schemas.py` |
| Teks disclaimer | PRD §14.2 non-negotiable | `simulation_orchestrator.py` |

---

## 4. JANGAN DIKERJAKAN — terblokir manusia

| Item | Terblokir oleh | File terkait |
|---|---|---|
| Isi `PD_CONSTANTS` (Mesin A) | Farmasi, PRD §13 #1 | `pkpd_engine.py` |
| Bentuk persamaan GSH eksplisit | Farmasi | `pkpd_engine.py` (`_pkpd_derivatives`) |
| Parameter nomogram 150/200 | Farmasi | `pkpd_engine.py` (`get_nomogram_data`) |
| Isi `SMARTS_VALIDATED_BY_PHARMACY` | Farmasi (ACC tertulis per gugus) | `app/chem/smarts_library.py` |
| T1.15 kalibrasi + applicability domain | Ketua Tim + Farmasi | belum ada file |
| TA.4 item #3 (field `engine`/`model_version`/dll) | Ketua Tim | `app/models/schemas.py` |
| Teks disclaimer | PRD §14.2 non-negotiable | `simulation_orchestrator.py` |

Tim saat ini **tidak punya anggota Farmasi** — jangan isi konstanta ini dari
internet meski dengan catatan (lihat `docs/DATA_PROVENANCE.md` §2 untuk alasan
lengkap kenapa ini beda dengan keputusan dataset publik). Kalau butuh, draft
`docs/REQUEST_VALIDASI_FARMASI.md` (T0.8) dan eskalasi ke dosen pembimbing —
belum dikerjakan siapa pun, bisa jadi task independen kapan saja.

---

## 5. TEMUAN TAMBAHAN — dilaporkan, belum diperbaiki (butuh keputusan/prioritisasi)

### 5.1 Bug `pkpd_engine.py` — kasus singular `ka == ke` — SUDAH DIPERBAIKI

`calculate_oral_absorption()` sekarang menggunakan bentuk limit
`(F·Dose·ka·t/Vd)·exp(-ke·t)` saat `abs(ka - ke) < 1e-6`, sesuai
Arsitektur §C.1.

### 5.2 `openapi.json` di root repo korup

Bukan JSON valid (terlihat seperti dump objek PowerShell yang salah encoding).
User sudah bilang "hiraukan saja" — jangan diperbaiki kecuali diminta ulang.
Regenerasi (bukan edit manual) butuh menjalankan server FastAPI dan ekspor
`app.openapi()`.

### 5.3 `data_preparation/deduplicate_smiles.py` — file lama, metode salah

Sudah digantikan `ml/scripts/04_dedup_split.py` (pakai InChIKey blok-1 yang
benar). File lama ini **masih ada di repo**, berisiko ada yang tidak sengaja
memakainya lagi. Belum diputuskan: hapus, atau biarkan dengan komentar
deprecated yang mengarahkan ke pengganti barunya. **Tanyakan ke user**, jangan
hapus sepihak (mungkin ada alasan dipertahankan yang tidak diketahui agent).

### 5.4 `EXECUTION_PLAN.md` — SUDAH DIREKONSILIASI

Status task T0.1–T2.2, T3.1–T3.3, T4.2 ditandai `DONE` dengan checklist ✓.
Catatan penyesuaian path (struktur flat AUDIT_TASKS §TA.0.1) ditambahkan.

---

## 6. KRITERIA REVIEW (dipakai reviewer untuk mengecek hasil kerjamu)

Saat mengecek pekerjaanmu, reviewer akan menanyakan hal-hal berikut. Siapkan
jawabannya (idealnya sudah tercatat di commit message / laporan):

1. Apakah `pytest tests/ -v` benar-benar dijalankan dan hijau — bukan cuma
   diklaim? (reviewer akan menjalankan ulang sendiri)
2. Apakah ada angka performa yang ditulis TANPA hasil eksekusi nyata?
   (`grep` untuk angka mencurigakan di `.json`/`.md` report)
3. Apakah ada konstanta PD yang terisi? (`grep "k_in\|k_elim\|k_meta\|k_gsh"
   app/services/pkpd_engine.py` harus tetap `None`)
4. Apakah `external_test.csv` disentuh lebih dari sekali untuk evaluasi
   (di luar T1.16)?
5. Apakah ada field API baru yang TIDAK ditandai `[EKSTENSI]` dan tidak
   dilaporkan?
6. Apakah ada commit dengan trailer AI, atau ada `git push` yang tidak diminta?
7. Apakah `visual_pattern` mode triase pernah selain `"heatmap_generik"` di
   kode manapun (walau di jalur yang jarang dieksekusi)?
8. Apakah anomali/hasil aneh ditelusuri sampai akar sebab, atau langsung
   diasumsikan "aman" / "bug" tanpa bukti?

Kalau ada yang gagal di poin manapun di atas, reviewer akan **takeover**
bagian itu, bukan menolak seluruh pekerjaan — sisanya yang benar tetap dipakai.
