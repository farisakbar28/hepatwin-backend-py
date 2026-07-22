# EXECUTION_PLAN.md — HepaTwin Backend & AI

Daftar task eksekusi. Dibaca bersama `AGENTS.md` (aturan perilaku) dan `docs/HepaTwin_PRD.md` (spesifikasi).

---

## CARA PAKAI FILE INI (untuk agent)

1. Cari task pertama berstatus `TODO` yang seluruh `Blokir`-nya sudah `DONE`
2. Baca kolom `Dasar` → buka pasal PRD tersebut sebelum menulis kode
3. Kerjakan hanya **satu task** per sesi kerja kecuali diminta lain
4. Jalankan gerbang verifikasi di `AGENTS.md` §8
5. Ubah `Status` menjadi `DONE` dan isi `Catatan` bila ada temuan
6. Jangan mengerjakan task berstatus `BLOCKED-HUMAN` — laporkan dan berhenti

**Jangan mengubah urutan task.** Dependensi antar task sudah dipetakan; melompat akan menghasilkan kode yang harus ditulis ulang.

### Legenda status

| Status | Arti |
|---|---|
| `TODO` | Siap dikerjakan bila blokirnya sudah selesai |
| `WIP` | Sedang dikerjakan |
| `DONE` | Selesai + gerbang verifikasi lulus |
| `BLOCKED-HUMAN` | Menunggu keputusan/validasi manusia. **Agent dilarang mengerjakan** |
| `SKIP` | Dibatalkan, tulis alasannya di Catatan |

### Konvensi

- Satu task ≈ satu commit atau satu PR kecil
- Task yang menyentuh `pkpd/` wajib cek `AGENTS.md` §3.1 lebih dulu
- Task yang menyentuh skema API wajib dilaporkan ke pengguna (frontend terdampak)

---

# SPRINT 0 — FONDASI

Target: kerangka backend berdiri, frontend tidak terblokir, permintaan validasi ke Farmasi terkirim.

---

### T0.1 — Inisialisasi repo dan struktur folder

```
Status : TODO
Blokir : —
Dasar  : Arsitektur §B.3
File   : seluruh struktur folder
```

**Langkah:**
1. Buat struktur folder persis seperti Arsitektur §B.3
2. Tambahkan `.gitignore`: `.venv/`, `__pycache__/`, `*.joblib`, `ml/data/`, `.env`
3. Tambahkan `backend/requirements.txt` (inference) dan `requirements-dev.txt` (training) terpisah
4. Buat `__init__.py` kosong di setiap package Python
5. Salin `AGENTS.md`, `CLAUDE.md`, dan folder `docs/` ke root

**Selesai bila:**
- [ ] `tree -L 3` menampilkan struktur sesuai Arsitektur §B.3
- [ ] `pip install -r backend/requirements.txt` berhasil
- [ ] `python -c "from rdkit import Chem; assert Chem.MolFromSmiles('CCO')"` lulus

---

### T0.2 — Konfigurasi aplikasi

```
Status : TODO
Blokir : T0.1
Dasar  : Arsitektur §B.3
File   : backend/app/core/config.py
```

**Langkah:**
1. Gunakan `pydantic-settings` `BaseSettings`
2. Setting minimal: `app_env`, `cors_origins`, `ml_backend` (`gnn`|`tabular`), `artifacts_dir`, `cache_db_path`, `rate_limit_per_minute`, `mock_mode`
3. `ml_backend` default `tabular`, tapi tandai di docstring bahwa nilai final ditentukan gerbang T1.14
4. Baca dari environment variable, sediakan `.env.example`

**Selesai bila:**
- [ ] `from app.core.config import settings` berhasil
- [ ] Nilai bisa dioverride lewat env var
- [ ] `.env.example` berisi semua kunci tanpa nilai rahasia

---

### T0.3 — Taksonomi error

```
Status : TODO
Blokir : T0.1
Dasar  : Arsitektur §E.4
File   : backend/app/core/errors.py
```

**Langkah:**
1. Buat base class `HepaTwinError` dengan atribut `code`, `user_message`, `http_status`
2. Turunkan kelas untuk setiap kode di Arsitektur §E.4: `E_SMILES_INVALID`, `E_MOL_TOO_LARGE`, `E_INORGANIC`, `E_MIXTURE`, `E_DOSE_RANGE`, `E_MODEL_UNAVAILABLE`
3. Buat exception handler FastAPI yang mengubahnya jadi JSON response
4. Handler **tidak boleh** menyertakan stack trace di response

**Selesai bila:**
- [ ] Setiap kode di §E.4 punya kelas
- [ ] Test: raise setiap error → response JSON berisi `code` dan `user_message`, tanpa traceback
- [ ] Exception tak terduga → 500 dengan pesan generik, detail hanya ke log

---

### T0.4 — Cache SQLite

```
Status : TODO
Blokir : T0.2
Dasar  : Arsitektur §E.5
File   : backend/app/core/cache.py
```

**Langkah:**
1. Tabel: `cache(key TEXT PRIMARY KEY, value TEXT, created_at TIMESTAMP)`
2. Fungsi `make_key(engine, model_version, inchikey_block1, dose, duration) -> str` menggunakan SHA-256
3. `model_version` **wajib** masuk komposisi key
4. Fungsi `get(key)`, `set(key, value)`, `clear()`
5. Buat tabel otomatis saat startup bila belum ada

**Selesai bila:**
- [ ] Test: `set` lalu `get` mengembalikan nilai sama
- [ ] Test: key berbeda saat `model_version` berbeda, input lain identik
- [ ] File DB dibuat otomatis di path dari config

---

### T0.5 — Skema API

```
Status : BLOCKED-HUMAN
Blokir : T0.1
Dasar  : PRD §7.1 langkah 4 · Arsitektur §E.2, §E.3
File   : backend/app/api/schemas.py
```

> **BLOCKED-HUMAN:** Perluasan skema (`engine`, `model_version`, `abstained`, `applicability_domain`, `score_interval`, `disclaimer`) adalah `[EKSTENSI]` di luar PRD §7.1. Butuh persetujuan Ketua Tim karena frontend yang mengonsumsinya. Lihat Arsitektur Bagian I keputusan #1.
>
> **Bila belum disetujui:** kerjakan hanya field yang ada di PRD §7.1 langkah 4 (`input_smiles`, `mode`, `DILI_score`, `model_confidence_note`, `explainability`, `visual_pattern`), dan ubah status jadi `TODO` dengan catatan "versi minimal PRD".

**Langkah (setelah keputusan):**
1. `SimulateRequest` sesuai Arsitektur §E.2, termasuk `model_validator` untuk validasi silang mode↔field
2. Definisikan `VisualPatternTriase = Literal["heatmap_generik"]` — **satu-satunya nilai sah**, lihat `AGENTS.md` §3.2
3. `VisualPatternFlagship = Literal["sentrilobuler", "portal_periportal"]`
4. Response model terpisah untuk mode edukasi dan triase
5. Contoh nilai di `json_schema_extra` supaya Swagger informatif

**Selesai bila:**
- [ ] Mode `edukasi_mendalam` tanpa `compound` → ValidationError
- [ ] Mode `triase_umum` tanpa `smiles` → ValidationError
- [ ] `dose_mg_kg` di luar rentang → ValidationError
- [ ] Tipe `VisualPatternTriase` tidak menerima nilai selain `heatmap_generik`

---

### T0.6 — Kerangka FastAPI + endpoint dasar

```
Status : TODO
Blokir : T0.2, T0.3, T0.5
Dasar  : Arsitektur §E.1
File   : backend/app/main.py, backend/app/api/routes_health.py, routes_compounds.py
```

**Langkah:**
1. `main.py`: buat app, daftarkan router, pasang CORS dari config, pasang exception handler dari T0.3
2. `GET /health` → `{"status": "ok", "version": <app_version>}`
3. `GET /api/v1/compounds` → daftar senyawa flagship dengan metadata (id, nama tampilan, tipe mekanisme, mode yang didukung)
4. Data senyawa flagship dari PRD §4.1 — hanya dua: `paracetamol`, `amoxicillin_clavulanate`

**Selesai bila:**
- [ ] `uvicorn app.main:app` menyala tanpa error
- [ ] `/docs` menampilkan kedua endpoint
- [ ] `GET /health` → 200
- [ ] `GET /api/v1/compounds` mengembalikan tepat 2 senyawa

---

### T0.7 — Mock mode untuk endpoint simulate

```
Status : TODO
Blokir : T0.5, T0.6
Dasar  : Arsitektur §H Sprint 0 hari 5
File   : backend/app/api/routes_simulate.py
```

**Langkah:**
1. `POST /api/v1/simulate` menerima `SimulateRequest`
2. Bila `settings.mock_mode` aktif → kembalikan response berbentuk final dengan nilai dummy yang **jelas terlihat dummy** (mis. `DILI_score: 0.5`, `model_version: "MOCK"`)
3. Bila mock mode mati dan mesin belum ada → raise `E_MODEL_UNAVAILABLE`
4. Response mode triase **wajib** `visual_pattern="heatmap_generik"`

**Selesai bila:**
- [ ] Frontend bisa memanggil endpoint dan menerima JSON berbentuk final
- [ ] Nilai dummy tidak bisa disalahartikan sebagai hasil nyata (`model_version="MOCK"`)
- [ ] Test: mode triase selalu `heatmap_generik`

---

### T0.8 — Paket permintaan validasi ke anggota Farmasi

```
Status : BLOCKED-HUMAN
Blokir : —
Dasar  : PRD §13 item #1, #2 · PRD §12
File   : docs/REQUEST_VALIDASI_FARMASI.md
```

> **BLOCKED-HUMAN:** Task ini dikerjakan manusia, bukan agent. Agent boleh membantu menyusun draf dokumen permintaannya saja.

**Isi dokumen permintaan (kirim sekaligus, jangan bertahap):**
1. Konstanta PD: `k_in`, `k_elim`, `k_meta`, `k_GSH`, `theta_thr` — minta nilai + satuan + sitasi primer
2. Bentuk persamaan GSH eksplisit (PRD §8.1 langkah 3 menuliskannya implisit)
3. Parameter kalibrasi garis nomogram 150/200 — verifikasi ke sumber primer
4. Daftar SMARTS → nama farmakologis: minta ACC tertulis per item
5. Pola histologis kolestatik amoxicillin-clavulanate (PRD §13 #2)

**Selesai bila:**
- [ ] Dokumen terkirim ke anggota Farmasi
- [ ] Tenggat balasan disepakati (rekomendasi: sebelum akhir Sprint 1)
- [ ] Eskalasi ke dosen pembimbing dijadwalkan bila lewat tenggat

---

# SPRINT 1 — DATA & AI ENGINE

Target: dataset bersih, model terlatih, angka performa aktual tercatat.

## Minggu 1 — Data

---

### T1.1 — Unduh dataset mentah

```
Status : TODO
Blokir : T0.1
Dasar  : PRD §7, §8.4 · PRD §13 item #3
File   : ml/scripts/01_download.py
```

**Langkah:**
1. Unduh DILIrank dari halaman FDA LTKB → `ml/data/raw/dilirank.xlsx`
2. Unduh dataset Xu et al. (2015) sebagai external test → `ml/data/raw/xu2015.csv`
3. Verifikasi lisensi/ketentuan penggunaan kedua sumber, catat di `NOTICE.md` (PRD §13 #3)
4. Script idempoten: lewati unduhan bila file sudah ada dan checksum cocok
5. Catat jumlah baris tiap file ke `ml/reports/01_download.md`

**JANGAN:** mengunduh atau memakai dataset NCTR — dikecualikan PRD §8.4.

**Selesai bila:**
- [ ] Kedua file ada di `ml/data/raw/`
- [ ] `NOTICE.md` memuat lisensi kedua dataset
- [ ] Laporan jumlah baris tertulis

---

### T1.2 — Resolusi nama obat menjadi SMILES

```
Status : TODO
Blokir : T1.1
Dasar  : Arsitektur §H Sprint 1 minggu 1
File   : ml/scripts/02_resolve_smiles.py
```

**Konteks penting:** DILIrank berisi nama senyawa, bukan SMILES. Langkah ini wajib sebelum data bisa dipakai. Tidak tercantum eksplisit di PRD §8.4 dan mudah luput dari estimasi waktu.

**Langkah:**
1. Baca kolom nama senyawa dari DILIrank
2. Resolusi nama → struktur lewat layanan publik (mis. PubChem PUG-REST)
3. **Cache hasil ke disk** (`ml/data/interim/name_cache.json`) — script akan dijalankan berulang
4. **Hormati rate limit layanan.** Baca dokumentasi resminya untuk angka pastinya; jangan menebak
5. Fallback untuk nama garam: bila gagal, buang sufiks garam umum (`sodium`, `hydrochloride`, `tartrate`, `mesylate`, `maleate`, `besylate`, `succinate`, `citrate`, `sulfate`, `phosphate`, `acetate`) lalu coba lagi
6. Buang entri biologik yang tidak punya SMILES bermakna (pola `-mab`, `-cept`, `-ase`, protein/antibodi)
7. Catat ke laporan: berapa berhasil, berapa gagal, gagalnya karena apa

**JANGAN:** menebak struktur untuk nama yang gagal resolve. Biarkan kosong dan laporkan.

**Selesai bila:**
- [ ] `ml/data/interim/dilirank_smiles.csv` ada
- [ ] Cache berfungsi: jalankan ulang tidak memanggil ulang layanan eksternal
- [ ] `ml/reports/02_resolve.md` memuat statistik keberhasilan dan daftar nama yang gagal

---

### T1.3 — Modul standardisasi molekul

```
Status : TODO
Blokir : T0.1
Dasar  : PRD §8.4 · Arsitektur §D.7
File   : backend/app/chem/standardize.py
```

**Langkah:**
1. Fungsi `standardize(smiles) -> StandardizedMol | None`
2. Urutan: parse RDKit → `rdMolStandardize.Cleanup` → `LargestFragmentChooser` → `Uncharger`
3. Kembalikan: canonical SMILES, InChIKey lengkap, blok pertama InChIKey (14 karakter), jumlah atom berat
4. Fungsi `check_eligibility(mol)` yang melempar error dari T0.3:
   - gagal parse → `E_SMILES_INVALID`
   - atom berat < 5 atau > 100 → `E_MOL_TOO_LARGE`
   - atom di luar `{H,B,C,N,O,F,Si,P,S,Cl,Se,Br,I}` → `E_INORGANIC`
   - masih mengandung `.` setelah standardisasi → `E_MIXTURE`

**Selesai bila:**
- [ ] Test: garam ter-strip (input garam → SMILES tanpa counter-ion)
- [ ] Test: SMILES invalid → `E_SMILES_INVALID`
- [ ] Test: dua penulisan SMILES berbeda untuk molekul sama → InChIKey blok-1 identik
- [ ] Test: senyawa logam → `E_INORGANIC`

---

### T1.4 — Pipeline standardisasi dataset

```
Status : TODO
Blokir : T1.2, T1.3
Dasar  : PRD §8.4
File   : ml/scripts/03_standardize.py
```

**Langkah:**
1. Jalankan `standardize()` pada DILIrank dan Xu et al.
2. Petakan label DILIrank ke biner sesuai keputusan tim — **tulis pemetaannya di laporan**, jangan diam-diam
3. Terapkan filter kelayakan, catat berapa baris hilang per filter
4. Output: `ml/data/interim/{dilirank,xu2015}_std.csv`

**Selesai bila:**
- [ ] Tabel alur di `ml/reports/03_standardize.md`: baris masuk → per filter → baris keluar
- [ ] Kolom output: `smiles`, `inchikey`, `inchikey_block1`, `label`, `source`
- [ ] Tidak ada baris dengan `inchikey_block1` kosong

---

### T1.5 — Deduplikasi dan split

```
Status : TODO
Blokir : T1.4
Dasar  : PRD §8.4 · Arsitektur §D.7
File   : ml/scripts/04_dedup_split.py
```

**Langkah:**
1. Dedup internal DILIrank berdasarkan `inchikey_block1`
2. Bila satu `inchikey_block1` punya label berbeda → **buang keduanya**, catat di laporan
3. Dedup lintas dataset: hapus senyawa tumpang tindih **dari external test**, bukan dari training
4. Split scaffold (Bemis-Murcko) pada training set — grup scaffold tidak boleh terpecah antara train dan validation
5. Simpan juga split acak sebagai pembanding pelaporan
6. Output: `ml/data/processed/{train,valid,external_test}.csv`

**Selesai bila:**
- [ ] `assert len(set(train.inchikey_block1) & set(external_test.inchikey_block1)) == 0` lulus
- [ ] Ukuran akhir external test tercatat di laporan
- [ ] Tidak ada scaffold yang muncul di train dan valid sekaligus
- [ ] Laporan memuat jumlah senyawa yang dibuang karena konflik label

---

### T1.6 — Test regresi data

```
Status : TODO
Blokir : T1.5
Dasar  : Arsitektur §G
File   : backend/tests/test_data_integrity.py
```

**Langkah:**
1. Test yang membaca `ml/data/processed/` dan memastikan nol overlap train ↔ external test
2. Test bahwa tidak ada `inchikey_block1` duplikat dalam satu file
3. Tandai `@pytest.mark.slow` bila membaca file besar

**Selesai bila:**
- [ ] Test lulus pada data saat ini
- [ ] Test **gagal** bila sengaja disisipkan baris duplikat (uji test-nya sendiri)

---

## Minggu 2 — Baseline dan gerbang GNN

---

### T1.7 — Kamus SMARTS

```
Status : TODO
Blokir : T0.1
Dasar  : PRD §8.5 · PRD §13 item #2 · Arsitektur §D.2
File   : backend/app/chem/smarts_library.py
```

**Langkah:**
1. `SMARTS_LIBRARY: dict[str, str]` — nama gugus → pola SMARTS
2. `SMARTS_VALIDATED_BY_PHARMACY: set[str]` — **mulai kosong**
3. Fungsi `validated_library()` mengembalikan hanya yang tervalidasi
4. Kompilasi pola dengan `Chem.MolFromSmarts` saat import; gagal kompilasi → error saat startup, bukan saat request

**JANGAN:** menambahkan nama apa pun ke `SMARTS_VALIDATED_BY_PHARMACY`. Itu diisi manusia setelah ACC tertulis (`AGENTS.md` §3.7).

**Selesai bila:**
- [ ] Semua pola di `SMARTS_LIBRARY` berhasil dikompilasi RDKit
- [ ] `validated_library()` mengembalikan dict kosong saat ini
- [ ] Test: pola SMARTS invalid → error saat import modul

---

### T1.8 — Featurizer

```
Status : TODO
Blokir : T1.7
Dasar  : Arsitektur §D.3
File   : backend/app/chem/features.py
```

**Langkah:**
1. Implementasikan `featurize(mol)` dan `feature_names()` persis seperti Arsitektur §D.3
2. Komposisi: ECFP4 2048 bit + 10 deskriptor + n flag SMARTS
3. Prefiks nama fitur SMARTS dengan `smarts::` — ini yang dipakai `explain.py` untuk menyaring
4. Fungsi `featurize_batch(mols)` untuk training

**Kritis:** ini satu-satunya sumber featurization. Script training mengimpor dari sini (`AGENTS.md` §4).

**Selesai bila:**
- [ ] `len(featurize(mol)) == len(feature_names())` untuk beberapa molekul uji
- [ ] Panjang vektor konsisten lintas molekul
- [ ] Test: molekul mengandung gugus X → flag `smarts::X` bernilai 1

---

### T1.9 — Baseline model tabular

```
Status : TODO
Blokir : T1.5, T1.8
Dasar  : PRD §13 item #4 · Arsitektur §D.6
File   : ml/scripts/05_train_baseline.py
```

**Langkah:**
1. Import featurizer dari `backend/app/chem/features.py` — **jangan salin kodenya**
2. LightGBM dengan parameter di Arsitektur §D.6
3. 5-fold CV **pada training set saja** — jangan sentuh external test (`AGENTS.md` §3.4)
4. Hitung: akurasi, AUROC, AUC-PR, sensitivity, specificity, MCC (PRD §3 tujuan #5)
5. Simpan hasil ke `ml/reports/05_baseline.json` — **angka nyata dari eksekusi, bukan karangan**
6. Simpan kurva ROC dan PR sebagai PNG

**Selesai bila:**
- [ ] `05_baseline.json` berisi seluruh metrik dari eksekusi nyata
- [ ] Hasil reproducible: jalankan dua kali dengan seed sama → angka identik
- [ ] External test set tidak tersentuh (verifikasi: tidak ada pembacaan `external_test.csv` di script)

---

### T1.10 — Implementasi GNN

```
Status : TODO
Blokir : T1.8, T1.9
Dasar  : PRD §7, §8.3 · Arsitektur §D.4
File   : backend/app/engines/ml/backend_gnn.py, ml/scripts/06a_train_gnn.py
```

**Langkah:**
1. Fitur node atom: nomor atom (one-hot himpunan organik), derajat, muatan formal, jumlah H, aromatisitas, hibridisasi, keanggotaan cincin
2. Arsitektur sesuai Arsitektur §D.4: cabang graf (GCNConv 64 → ReLU → GCNConv 64 → global_mean_pool) + cabang struktural (Linear 128) → concat → Dropout 0.3 → Linear 64 → Linear 1
3. Regularisasi kuat: dropout 0.3–0.5, weight decay, early stopping pada validation fold
4. `class_weight` seimbang
5. Seed tetap + `torch.use_deterministic_algorithms(True)`
6. Evaluasi 5-fold CV pada training set saja

**Selesai bila:**
- [ ] Training selesai 5 fold tanpa crash
- [ ] Hasil reproducible dengan seed sama
- [ ] Metrik tersimpan ke `ml/reports/06a_gnn.json`
- [ ] Ukuran Docker image dengan torch-geometric terukur dan tercatat

---

### T1.11 — Evaluasi gerbang kelayakan GNN

```
Status : BLOCKED-HUMAN
Blokir : T1.9, T1.10
Dasar  : PRD §13 item #4 · Arsitektur §D.5
File   : docs/GATE_DECISION_GNN.md
```

> **BLOCKED-HUMAN:** Agent boleh mengukur dan menyusun tabel, tetapi **keputusan pivot adalah keputusan tim**, bukan agent.

**Kriteria (semua wajib lulus):**

| Kriteria | Ambang | Hasil |
|---|---|---|
| AUROC CV GNN vs baseline tabular | GNN unggul ≥ 0,02 | |
| Pipeline stabil | 5 fold tanpa crash, reproducible | |
| Ukuran Docker image inference | ≤ 1,5 GB | |
| Waktu inferensi 1 molekul (cold cache) | ≤ 2 detik | |
| SHAP pada cabang struktural berfungsi | Ya | |

**Selesai bila:**
- [ ] Tabel terisi angka hasil pengukuran nyata
- [ ] Keputusan tertulis: `ML_BACKEND=gnn` atau `ML_BACKEND=tabular`
- [ ] Bila pivot ke tabular: catat konsekuensi terhadap klaim novelty (PRD §13 #4)
- [ ] Dokumen ini masuk lampiran laporan akhir

---

## Minggu 3 — Produksi dan validasi eksternal

---

### T1.12 — Antarmuka predictor

```
Status : TODO
Blokir : T1.11
Dasar  : Arsitektur §D.1
File   : backend/app/engines/ml/predictor.py
```

**Langkah:**
1. Definisikan `DILIBackend` Protocol dengan `name`, `version`, `predict_proba(mol)`, `explain(mol)`
2. `get_backend()` memilih implementasi dari `settings.ml_backend`
3. Kedua implementasi (`backend_tabular.py`, `backend_gnn.py`) memenuhi Protocol yang sama
4. Route dan skema response **tidak boleh** berubah antara kedua jalur

**Selesai bila:**
- [ ] Ganti env `ML_BACKEND` → backend berganti tanpa mengubah kode lain
- [ ] `mypy` memverifikasi kedua implementasi memenuhi Protocol
- [ ] Test: `get_backend()` melempar error jelas bila nilai env tidak dikenal

---

### T1.13 — Latih model final

```
Status : TODO
Blokir : T1.11, T1.12
Dasar  : PRD §8.3
File   : ml/scripts/06_train_production.py
```

**Langkah:**
1. Latih pada jalur yang dipilih gerbang T1.11
2. Simpan artefak ke `backend/app/artifacts/`: model, (calibrator bila T1.15 disetujui), `train_fps.npz`, `model_meta.json`
3. `model_meta.json` memuat: `model_version`, `backend`, `trained_at`, `n_train`, `feature_names_hash`, `metrics` (**diisi `null` sampai T1.16 dijalankan**)

**JANGAN:** mengisi `metrics` dengan angka apa pun sebelum T1.16 (`AGENTS.md` §3.3).

**Selesai bila:**
- [ ] Artefak lengkap di `backend/app/artifacts/`
- [ ] `feature_names_hash` cocok dengan `feature_names()` saat ini
- [ ] `metrics` bernilai `null`

---

### T1.14 — Lapisan explainability

```
Status : TODO
Blokir : T1.13
Dasar  : PRD §8.5 · PRD §13 item #2
File   : backend/app/engines/ml/explain.py
```

**Langkah:**
1. Hitung SHAP untuk satu molekul
2. **Saring hanya fitur berprefiks `smarts::`**
3. **Saring lagi hanya yang lolos `validated_library()`** — `AGENTS.md` §3.7
4. Urutkan berdasarkan magnitudo kontribusi, kembalikan top-N dengan nama gugus
5. Bila `validated_library()` kosong → kembalikan list kosong, **jangan** kembalikan indeks fitur (PRD §8.5 melarang)

**Selesai bila:**
- [ ] Output berupa nama gugus, tidak pernah indeks numerik
- [ ] Test: gugus belum tervalidasi tidak muncul di output
- [ ] Test: `validated_library()` kosong → output list kosong, bukan error

---

### T1.15 — Kalibrasi dan applicability domain

```
Status : BLOCKED-HUMAN
Blokir : T1.13
Dasar  : Arsitektur §D.9 — [EKSTENSI], di luar PRD
File   : backend/app/engines/ml/calibration.py, backend/app/engines/ml/domain.py
```

> **BLOCKED-HUMAN:** `[EKSTENSI]` di luar PRD. Menambah perilaku abstain berdampak ke frontend. Butuh persetujuan Ketua Tim + Farmasi. Lihat Arsitektur Bagian I keputusan #2.

**Langkah (setelah disetujui):**
1. `CalibratedClassifierCV(method="isotonic")`; hitung Brier score dan reliability curve
2. `ad_similarity(query_fp, train_fps, k=3)` sesuai Arsitektur §D.9
3. Penetapan ambang: plot akurasi vs similarity pada test set, ambil titik akurasi jatuh — **berbasis data, bukan angka pilihan sendiri**
4. Di bawah ambang → response `abstained: true`, HTTP 200, bukan error

**Selesai bila:**
- [ ] Reliability curve tersimpan sebagai PNG
- [ ] Ambang AD punya justifikasi grafis, tercatat di laporan
- [ ] Test: senyawa sangat berbeda dari training → `abstained: true`

---

### T1.16 — Validasi eksternal

```
Status : TODO
Blokir : T1.13, T1.14
Dasar  : PRD §3 tujuan #5, §8.3, §8.4, §14.5
File   : ml/scripts/07_external_eval.py
```

> **PERINGATAN: Script ini dijalankan SATU KALI.** Setelah dijalankan, dilarang menyetel model berdasarkan hasilnya (`AGENTS.md` §3.4). Bila terpaksa, statusnya berubah dan wajib dinyatakan di laporan.

**Langkah:**
1. Muat model final + external test set
2. Hitung: akurasi, AUC, sensitivity, specificity, MCC (PRD §3 tujuan #5)
3. Interval kepercayaan bootstrap 1.000 resampling
4. Uji permutasi: acak label training 20×, latih ulang, bandingkan distribusi AUROC
5. Tulis `ml/reports/external_validation.md` dengan tabel pembanding wajib:

| Model | Sumber | Angka |
|---|---|---|
| Baseline RF/MLP | Mostafa, Howle, & Chen (2024) | akurasi 0,631 · MCC 0,245 |
| Target HepaTwin | PRD §3, §8.3 | AUC 0,75–0,85 |
| HepaTwin aktual | eksperimen ini | *diisi hasil nyata* |

6. Perbarui `metrics` di `model_meta.json` dengan angka aktual
7. Catat commit hash sebagai penanda pembekuan

**Angka aktual wajib dilaporkan apa adanya, termasuk bila di bawah target** (PRD §8.3, §14.5).

**Selesai bila:**
- [ ] Seluruh metrik + CI tercatat
- [ ] Hasil uji permutasi tercatat
- [ ] `model_meta.json` terisi angka nyata
- [ ] Commit hash pembekuan tercatat

---

### T1.17 — Endpoint model-info

```
Status : TODO
Blokir : T1.16
Dasar  : PRD §8.3, §14.5 · Arsitektur §E.1 — [EKSTENSI]
File   : backend/app/api/routes_model_info.py
```

**Langkah:**
1. `GET /api/v1/model-info` menyajikan isi `model_meta.json`
2. Sertakan: `model_version`, `backend`, `trained_at`, `n_train`, `n_external_test`, seluruh metrik aktual
3. Bila `metrics` masih `null` → kembalikan `null`, **jangan** isi dengan angka target

**Selesai bila:**
- [ ] Endpoint mengembalikan angka yang identik dengan `external_validation.md`
- [ ] Test: `metrics` null → response null, bukan angka karangan

---

### T1.18 — Integrasi Mesin B ke endpoint simulate

```
Status : TODO
Blokir : T1.12, T1.14, T0.7
Dasar  : PRD §7.1 langkah 3 · Arsitektur §B.2
File   : backend/app/api/routes_simulate.py
```

**Langkah:**
1. Routing tiga jalur sesuai Arsitektur §B.2
2. Mode triase: standardisasi → cek kelayakan → featurize → predict → explain → response
3. Amox-clav: sama, tetapi `visual_pattern="portal_periportal"` dan keparahan visual mengikuti skor AI (PRD §8.2)
4. Mode triase: `visual_pattern` **selalu** `heatmap_generik` (PRD §4.2, `AGENTS.md` §3.2)
5. Pasang caching dari T0.4
6. Matikan mock mode

**Selesai bila:**
- [ ] Test kontrak: mode triase selalu `heatmap_generik`, tanpa kondisional apa pun
- [ ] Test: SMILES invalid → `E_SMILES_INVALID` dengan HTTP 422
- [ ] Cache hit terverifikasi lewat log
- [ ] Waktu respons memenuhi NFR PRD §6 (< 5 detik mode triase)

---

# SPRINT 2 — MESIN PK/PD

Target: Mesin A berfungsi dan tervalidasi terhadap nomogram.

**Catatan:** PRD §11 menyarankan sprint ini diparalelkan dengan Sprint 1. Mulai T2.1 begitu Sprint 0 selesai.

---

### T2.1 — Modul absorpsi oral

```
Status : TODO
Blokir : T0.1
Dasar  : PRD §8.1 langkah 1 · Arsitektur §C.1
File   : backend/app/engines/pkpd/absorption.py
```

**Langkah:**
1. Implementasikan solusi closed-form persis seperti PRD §8.1 langkah 1
2. Parameter dari PRD §8.1: F=0,86 · CL=24,0 L/jam/70kg · V1=43,5 L/70kg · ka≈3,47/jam · ke≈0,55/jam
3. **Tangani kasus singular:** bila `abs(ka - ke) < 1e-6`, pakai bentuk limit `(F·Dose·ka·t/Vd)·exp(-ke·t)`
4. Docstring memuat batasan model PRD §8.1: dua-kompartemen disederhanakan jadi satu-kompartemen, V1 sebagai pendekatan Vd, lag time 5,3 menit tidak dimasukkan

**Selesai bila:**
- [ ] Test: kurva berbentuk naik lalu turun (satu puncak)
- [ ] Test: `ka == ke` tidak menghasilkan NaN atau ZeroDivisionError
- [ ] Test: dosis 0 → konsentrasi 0 di semua t
- [ ] Docstring memuat seluruh batasan PRD §8.1

---

### T2.2 — Gerbang konstanta PD

```
Status : TODO
Blokir : T0.1
Dasar  : PRD §13 item #1 · Arsitektur §C.3
File   : backend/app/engines/pkpd/constants.py
```

**Langkah:**
1. Implementasikan `PDConstant` dataclass dan dict `PD_CONSTANTS` persis seperti Arsitektur §C.3
2. Seluruh `value` bernilai `None`, `validated_by_pharmacy=False`, `citation=None`
3. `assert_ready()` melempar `RuntimeError` bila ada yang belum lengkap
4. Panggil `assert_ready()` saat startup aplikasi bila Mesin A diaktifkan

**JANGAN:** mengisi nilai apa pun (`AGENTS.md` §3.1).

**Selesai bila:**
- [ ] `assert_ready()` gagal saat ini, dengan pesan menyebut PRD §13 #1
- [ ] Test: mengisi sebagian konstanta → tetap gagal
- [ ] Tidak ada jalur bypass

---

### T2.3 — Sistem ODE hati

```
Status : BLOCKED-HUMAN
Blokir : T2.1, T2.2
Dasar  : PRD §8.1 langkah 2–3 · Arsitektur §C.2
File   : backend/app/engines/pkpd/liver_napqi.py
```

> **BLOCKED-HUMAN:** Terblokir T0.8. Butuh (a) nilai konstanta PD, dan (b) bentuk persamaan GSH eksplisit — PRD §8.1 langkah 3 menuliskannya implisit, sehingga state ketiga untuk `solve_ivp` belum terdefinisi. Keduanya item validasi Farmasi.

**Langkah (setelah konstanta tersedia):**
1. Implementasikan persamaan PRD §8.1 langkah 2–3
2. `scipy.integrate.solve_ivp` metode `LSODA` (sistem stiff saat overdosis)
3. Hitung rasio `[NAPQI](t) / [GSH]₀` dan titik perlintasan `theta_thr`
4. Kembalikan kurva lengkap + `threshold_crossed_at_h`

**Selesai bila:**
- [ ] Solver konvergen pada skenario terapetik dan overdosis
- [ ] Test: dosis lebih tinggi → rasio NAPQI/GSH lebih tinggi (monotonisitas)
- [ ] `assert_ready()` dipanggil sebelum komputasi

---

### T2.4 — Modul nomogram Rumack-Matthew

```
Status : BLOCKED-HUMAN
Blokir : T2.1
Dasar  : PRD §8.1 validasi silang · PRD §13 item #1 · Arsitektur §C.4
File   : backend/app/engines/pkpd/nomogram.py
```

> **BLOCKED-HUMAN:** PRD §13 #1 mewajibkan parameter kalibrasi garis 150/200 diverifikasi ke sumber primer oleh Farmasi. Jangan menetapkan parameter peluruhan sendiri.

**Langkah (setelah parameter terverifikasi):**
1. Fungsi `nomogram_line(t_hours, anchor)` untuk anchor 150 dan 200
2. Validasi rentang: hanya berlaku 4 ≤ t ≤ 24 jam, di luar itu raise ValueError
3. Docstring menyebut sumber dan status verifikasi

**Selesai bila:**
- [ ] Nilai di t=4 jam tepat sama dengan anchor
- [ ] t di luar 4–24 → ValueError
- [ ] Parameter peluruhan bersumber dari verifikasi Farmasi, tercatat di docstring

---

### T2.5 — Test validasi silang nomogram

```
Status : BLOCKED-HUMAN
Blokir : T2.1, T2.4
Dasar  : PRD §3 tujuan #3, §8.1
File   : backend/tests/test_nomogram_validation.py
```

> **BLOCKED-HUMAN:** Terblokir T2.4.

**Langkah:**
1. Skenario dosis terapetik → kurva Cplasma di bawah garis 150 sepanjang 4–24 jam
2. Skenario overdosis besar → kurva memotong ke atas garis 150 dalam rentang tersebut
3. Simpan plot validasi ke `ml/reports/nomogram_validation.png` untuk laporan

**Selesai bila:**
- [ ] Kedua test lulus
- [ ] Plot tersimpan
- [ ] Hasil memenuhi PRD §3 tujuan #3 ("konsisten posisi relatif terhadap garis 150/200")

---

### T2.6 — Integrasi Mesin A ke endpoint simulate

```
Status : BLOCKED-HUMAN
Blokir : T2.3, T2.5, T1.18
Dasar  : PRD §7.1 langkah 3 · Arsitektur §B.2
File   : backend/app/api/routes_simulate.py
```

> **BLOCKED-HUMAN:** Terblokir T2.3 dan T2.5.

**Langkah:**
1. Jalur parasetamol: Mesin A sebagai penggerak utama, skor Mesin B sebagai pendamping (PRD §7.1 langkah 3)
2. Response tambahan: `cplasma_curve`, `napqi_gsh_ratio_curve`, `nomogram` (garis 150 & 200 pada rentang waktu sama), `threshold_crossed_at_h`
3. `engine = "pkpd_deterministic"`
4. `visual_pattern = "sentrilobuler"`

**Selesai bila:**
- [ ] Response parasetamol memuat seluruh kurva
- [ ] Waktu respons < 3 detik (NFR PRD §6)
- [ ] Test integrasi lulus

---

# SPRINT 3 — DUKUNGAN VISUAL & MODE TRIASE

Fokus utama frontend. Task di sini adalah dukungan backend.

---

### T3.1 — Endpoint validasi SMILES

```
Status : TODO
Blokir : T1.3
Dasar  : PRD §7.1 langkah 1 · Arsitektur §E.1
File   : backend/app/api/routes_simulate.py
```

**Langkah:**
1. `POST /api/v1/validate-smiles` menerima `{smiles: str}`
2. Kembalikan `{valid: bool, error_code: str|null, canonical_smiles: str|null}`
3. Ringan dan cepat — dipanggil saat pengguna mengetik
4. Tidak memuat model, hanya RDKit

**Selesai bila:**
- [ ] Waktu respons < 200 ms
- [ ] Test: setiap kode error dari T0.3 terpetakan dengan benar
- [ ] Tidak memuat artefak model

---

### T3.2 — Test kontrak batas scope

```
Status : TODO
Blokir : T1.18
Dasar  : PRD §4.2 · AGENTS.md §3.2 · Arsitektur §G
File   : backend/tests/test_contract.py
```

**Langkah:**
1. Test parametrik: kirim beragam SMILES ke mode triase, assert `visual_pattern == "heatmap_generik"` untuk **semua**
2. Test: response mode triase tidak memuat field zonal apa pun
3. Test: tipe `VisualPatternTriase` menolak nilai lain

**Ini penjaga batas scope PRD §4.2. Jangan pernah dilonggarkan atau di-skip.**

**Selesai bila:**
- [ ] Test lulus untuk minimal 20 SMILES beragam
- [ ] Test gagal bila sengaja disisipkan logika pola zonal (uji test-nya sendiri)

---

### T3.3 — Optimasi waktu respons mode triase

```
Status : TODO
Blokir : T1.18
Dasar  : PRD §6 NFR
File   : backend/app/engines/ml/
```

**Langkah:**
1. Ukur waktu tiap tahap: standardisasi, featurize, predict, SHAP
2. Muat artefak model sekali saat startup, bukan tiap request
3. Precompute background SHAP saat startup bila memungkinkan
4. Verifikasi total < 5 detik (PRD §6)

**Selesai bila:**
- [ ] Profil waktu per tahap tercatat
- [ ] Cold cache < 5 detik, warm cache < 1 detik
- [ ] Artefak tidak dimuat ulang per request

---

# SPRINT 4 — DUKUNGAN DASHBOARD

---

### T4.1 — Data panel nomogram siap render

```
Status : BLOCKED-HUMAN
Blokir : T2.6
Dasar  : PRD §9.1, §9.4 mockup #2
File   : backend/app/api/routes_simulate.py
```

> **BLOCKED-HUMAN:** Terblokir T2.6.

**Selesai bila:**
- [ ] Response memuat array titik garis 150 dan 200 pada rentang waktu yang sama dengan `cplasma_curve`
- [ ] Frontend bisa merender tanpa perhitungan tambahan

---

### T4.2 — Field batasan model

```
Status : TODO
Blokir : T1.18
Dasar  : PRD §8.1 batasan · Arsitektur §E.3
File   : backend/app/api/schemas.py
```

**Langkah:**
1. Field `model_limitations: list[str]` di response
2. Untuk parasetamol: batasan PRD §8.1 (satu-kompartemen, V1 sebagai Vd, lag time diabaikan)
3. Untuk mode triase: batasan cakupan model

**Selesai bila:**
- [ ] Teks batasan bersumber dari PRD, bukan karangan
- [ ] Muncul di kedua mode

---

### T4.3 — Penyajian disclaimer

```
Status : BLOCKED-HUMAN
Blokir : T1.17
Dasar  : PRD §14.2 · Arsitektur §A.1
File   : backend/app/api/routes_simulate.py
```

> **BLOCKED-HUMAN:** PRD §14.2 mengunci teks disclaimer secara harfiah dan menandainya non-negotiable. Usulan membuatnya dinamis ada di Arsitektur §A.1, tetapi **usulan bukan persetujuan**. Butuh keputusan Ketua Tim + Farmasi (Arsitektur Bagian I keputusan #3).
>
> **Bila tidak disetujui:** kirim teks PRD §14.2 apa adanya.

**Selesai bila:**
- [ ] Disclaimer dikirim dari server, bukan hardcode di frontend
- [ ] Teks sesuai keputusan tim

---

# SPRINT 5 — DUKUNGAN EVALUASI DAMPAK

Dipimpin Farmasi (PRD §10, §12). Task di sini adalah dukungan teknis.

---

### T5.1 — Precompute skenario demo

```
Status : TODO
Blokir : T1.18
Dasar  : Arsitektur §F.2
File   : ml/scripts/08_precompute_demo.py
```

**Langkah:**
1. Kurasi daftar senyawa yang akan dipakai saat sesi evaluasi
2. Hitung seluruh response, simpan sebagai JSON statis
3. Frontend menyajikannya tanpa memanggil backend

**Selesai bila:**
- [ ] JSON precompute tersedia
- [ ] Sesi demo tidak bergantung pada backend live

---

### T5.2 — Verifikasi stabilitas lingkungan sesi

```
Status : TODO
Blokir : T5.1
Dasar  : PRD §10
File   : —
```

**Selesai bila:**
- [ ] Uji coba di lingkungan yang akan dipakai (lab komputer)
- [ ] Mode offline terverifikasi berfungsi

---

# SPRINT 6 — INTEGRASI, DEPLOY, HARDENING

---

### T6.1 — Dockerfile dan optimasi image

```
Status : TODO
Blokir : T1.18
Dasar  : Arsitektur §F.1
File   : backend/Dockerfile
```

**Langkah:**
1. Implementasikan Dockerfile sesuai Arsitektur §F.1
2. Verifikasi `requirements.txt` hanya berisi dependensi inference
3. Ukur ukuran image, bandingkan terhadap batas 1,5 GB

**Selesai bila:**
- [ ] `docker build` berhasil
- [ ] Ukuran image ≤ 1,5 GB, tercatat
- [ ] Container menyala dan `/health` mengembalikan 200

---

### T6.2 — Rate limiting dan CORS

```
Status : TODO
Blokir : T6.1
Dasar  : Arsitektur §E.6
File   : backend/app/main.py
```

**Selesai bila:**
- [ ] Rate limit 30 req/menit per IP di `/simulate`
- [ ] CORS whitelist domain Vercel proyek, **bukan** `*`
- [ ] Batas ukuran body request aktif
- [ ] Test: request ke-31 dalam satu menit → 429

---

### T6.3 — Deploy ke Railway

```
Status : TODO
Blokir : T6.1, T6.2
Dasar  : PRD §7 · Arsitektur §F
File   : —
```

**Selesai bila:**
- [ ] Backend live di URL publik
- [ ] `/health` 200 dari luar
- [ ] Frontend Vercel berhasil memanggil (CORS terverifikasi)
- [ ] Variabel environment produksi terpasang

---

### T6.4 — Keep-alive

```
Status : TODO
Blokir : T6.3
Dasar  : Arsitektur §F.2
File   : —
```

**Selesai bila:**
- [ ] Cron eksternal ping `/health` tiap 10 menit
- [ ] Cold start terukur dan tercatat

---

### T6.5 — Uji end-to-end kedua mode

```
Status : TODO
Blokir : T6.3
Dasar  : PRD §11 Sprint 6 · Arsitektur §G
File   : backend/tests/test_e2e.py
```

**Selesai bila:**
- [ ] Kedua mode berfungsi dari browser
- [ ] Seluruh kode error terpetakan dengan benar di UI
- [ ] Waktu respons memenuhi NFR PRD §6 di lingkungan produksi

---

# SPRINT 7 — FINALISASI

---

### T7.1 — Model card

```
Status : TODO
Blokir : T1.16
Dasar  : PRD §8.3, §14.5
File   : docs/MODEL_CARD.md
```

**Isi wajib:**
1. Data latih: sumber, ukuran, skema label, tanggal
2. Cakupan: jenis molekul yang didukung dan tidak
3. Batasan: seluruh batasan yang diakui PRD
4. Metrik aktual dari T1.16 — **angka nyata**
5. Penggunaan yang tidak dianjurkan (PRD §14)

**Selesai bila:**
- [ ] Seluruh angka bersumber dari `model_meta.json`
- [ ] Tidak ada angka target yang disajikan sebagai hasil

---

### T7.2 — Dokumentasi API final

```
Status : TODO
Blokir : T6.5
Dasar  : Arsitektur §E
File   : docs/API_CONTRACT.md
```

**Selesai bila:**
- [ ] Seluruh endpoint terdokumentasi dengan contoh request/response
- [ ] Field `[EKSTENSI]` ditandai eksplisit
- [ ] Taksonomi error lengkap

---

### T7.3 — NOTICE lisensi

```
Status : TODO
Blokir : T1.1
Dasar  : PRD §13 item #3
File   : NOTICE.md
```

**Selesai bila:**
- [ ] Lisensi seluruh dataset tercatat
- [ ] Lisensi seluruh pustaka pihak ketiga tercatat
- [ ] Atribusi sesuai ketentuan masing-masing

---

### T7.4 — Laporan validasi eksternal final

```
Status : TODO
Blokir : T1.16
Dasar  : PRD §3 tujuan #5, §8.3
File   : ml/reports/external_validation.md
```

**Selesai bila:**
- [ ] Tabel pembanding Mostafa et al. (2024) tercantum (PRD §8.3 mewajibkan)
- [ ] Angka aktual dilaporkan apa adanya
- [ ] Interval kepercayaan dan ukuran test set tercantum
- [ ] Batasan metodologis PRD §8.4 dinyatakan eksplisit

---

## RINGKASAN BLOKIR MANUSIA

Task berikut **tidak boleh** dikerjakan agent sampai ada keputusan/validasi manusia:

| Task | Menunggu | Dari |
|---|---|---|
| T0.5 | Persetujuan perluasan skema API | Ketua Tim |
| T0.8 | Pengiriman permintaan validasi | Manusia |
| T1.11 | Keputusan pivot GNN/tabular | Tim |
| T1.15 | Persetujuan kalibrasi + AD | Ketua Tim + Farmasi |
| T2.3 | Konstanta PD + persamaan GSH | Farmasi |
| T2.4 | Parameter nomogram | Farmasi |
| T2.5, T2.6, T4.1 | Rantai dari T2.3/T2.4 | Farmasi |
| T4.3 | Keputusan teks disclaimer | Ketua Tim + Farmasi |

**Jalur kritis terpanjang melewati validasi Farmasi.** T0.8 harus dikirim di hari pertama Sprint 0. Bila tidak, seluruh Mesin A (Sprint 2) dan Mode Edukasi Mendalam akan terblokir.
