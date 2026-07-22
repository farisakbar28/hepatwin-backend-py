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

## 3. HARUS DILANJUTKAN — urutan prioritas

Ikuti urutan ini (sesuai `EXECUTION_PLAN.md` Sprint 1 minggu 2–3). Jangan
lompat kecuali ada alasan kuat dan dicatat kenapa.

### 3.1 T1.9 — Baseline LightGBM (PALING PRIORITAS, tidak ada blocker)

```
Dasar : PRD §13 item #4 · Arsitektur §D.6
File  : ml/scripts/05_train_baseline.py (baru)
```

- Impor featurizer dari `app.chem.features` — **JANGAN salin kodenya**.
- Load HANYA `ml/data/processed/train.csv` (708 baris). **JANGAN sentuh
  `valid.csv` atau `external_test.csv` untuk training** — valid untuk
  validasi internal (5-fold CV), external_test tetap tersegel.
- LightGBM param sesuai Arsitektur §D.6 (`class_weight="balanced"`, dll).
- 5-fold CV **pada train saja**. Hitung: akurasi, AUROC, AUC-PR, sensitivity,
  specificity, MCC.
- Simpan ke `ml/reports/05_baseline.json` — **angka nyata dari eksekusi**,
  bukan contoh/karangan (AGENTS.md §3.3).
- Verifikasi reproducibility: jalankan 2x dengan seed sama → angka identik.

### 3.2 T1.10 — Implementasi GNN

```
Dasar : PRD §7, §8.3 · Arsitektur §D.4
File  : backend/app/engines/ml/backend_gnn.py → SESUAIKAN path: app/services/ atau app/chem/? DISKUSIKAN, jangan asumsi
```

- Arsitektur sudah didefinisikan di `ai_engine.py` (`HybridGNN` class) —
  **cek dulu apakah bisa dipakai langsung atau perlu direfactor** ke pola
  training yang benar (saat ini `HybridGNN` didesain untuk inference tunggal,
  bukan batch training — kemungkinan perlu penyesuaian).
- torch + torch-geometric (CPU) sudah terinstall di `.venv`.
- 5-fold CV pada training set saja, seed tetap,
  `torch.use_deterministic_algorithms(True)`.

### 3.3 T1.11 — Gerbang kelayakan GNN (`BLOCKED-HUMAN` untuk KEPUTUSAN, agent boleh MENGUKUR)

```
Dasar : PRD §13 item #4 · Arsitektur §D.5
File  : docs/GATE_DECISION_GNN.md (baru)
```

Agent boleh mengukur & menyusun tabel (AUROC GNN vs baseline, ukuran Docker
image, waktu inferensi, dll — lihat kriteria lengkap di
`EXECUTION_PLAN.md` T1.11). **Keputusan pivot `ML_BACKEND=gnn` vs `=tabular`
BUKAN keputusan agent** — laporkan tabel hasil, minta keputusan tim.

### 3.4 T1.12–T1.14 — Predictor interface, latih model final, explainability

- `DILIBackend` Protocol (`predict_proba`, `explain`), dua implementasi
  (`backend_tabular`, `backend_gnn`) sama-sama memenuhi Protocol.
- `model_meta.json` — `metrics` **HARUS `null`** sampai T1.16 dijalankan.
  Jangan isi angka apa pun sebelum itu (AGENTS.md §3.3).
- Explainability: SHAP → filter hanya fitur `smarts::` yang lolos
  `validated_library()` (saat ini KOSONG → output harus list kosong, bukan
  error, bukan indeks numerik).

### 3.5 T1.16 — Validasi eksternal (KRITIS, SEKALI SAJA)

Baca `EXECUTION_PLAN.md` T1.16 dan `AGENTS.md` §3.4 berkali-kali sebelum
menyentuh `external_test.csv`. Setelah dibuka, DILARANG menyetel model
berdasarkan hasilnya. Tabel pembanding wajib menyertakan baseline Mostafa et
al. (2024): akurasi 0,631 · MCC 0,245.

### 3.6 T1.17–T1.18 — endpoint `/model-info`, integrasi ke `/simulate`

Ganti bobot random `HybridAIEngine` dengan model terlatih asli. Update
`model_status` logic bila perlu (kemungkinan tidak perlu berubah, sudah benar
strukturnya).

### 3.7 Test coverage yang HILANG (gap penting, prioritas tinggi meski di luar sprint 1)

`docs/Claude.md` §8 sendiri bilang: *"Dua test yang paling bernilai dan paling
sering dilupakan: assert nol overlap dan assert heatmap_generik."* **Kedua
test itu BELUM ADA sebagai automated test**, baru diverifikasi manual sesi
ini:

- `tests/test_contract.py` (T3.2) — assert `visual_pattern` mode triase
  SELALU `"heatmap_generik"` untuk berbagai SMILES. **Test paling penting
  yang belum ditulis.**
- `tests/test_data_integrity.py` (T1.6) — assert nol overlap InChIKey blok-1
  train↔external_test secara otomatis (bukan cuma manual check sesi ini).
- Tidak ada test integrasi untuk endpoint (`/health`, `/simulate`,
  `/compounds`) sama sekali.

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

### 5.1 Bug kemungkinan di `pkpd_engine.py` — kasus singular `ka == ke`

`calculate_oral_absorption()` baris ~79:
```python
if time_hours <= lag_time_hr or (ka - ke) == 0:
    return 0.0
```
PRD §8.1 dan Arsitektur §C.1 mensyaratkan: bila `abs(ka - ke) < 1e-6`, pakai
**bentuk limit** `(F·Dose·ka·t/Vd)·exp(-ke·t)`, BUKAN mengembalikan 0.0 begitu
saja. Dengan nilai KA=3.47/KE=0.55 saat ini bug ini tidak aktif (ka≠ke), tapi
kalau parameter berubah nanti (mis. setelah validasi Farmasi), hasilnya akan
salah secara diam-diam tanpa error. **Belum diperbaiki sesi ini** — di luar
cakupan kerja yang sedang berjalan saat ditemukan. Prioritaskan sebelum T2.x
manapun disentuh.

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

### 5.4 `EXECUTION_PLAN.md` belum direkonsiliasi statusnya

`docs/AUDIT_TASKS.md` Bagian 4 meminta status task T0.2/T0.3/T0.4/T0.6/T0.7 di
`EXECUTION_PLAN.md` ditandai `DONE` (sudah setara terpenuhi lewat audit TA.x)
dengan catatan menunjuk task TA yang menyelesaikannya. **Belum dikerjakan.**
Ini murni dokumentasi, aman dikerjakan kapan saja, tidak butuh keputusan tim.

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
