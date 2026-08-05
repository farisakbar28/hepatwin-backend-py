# PROJECT_FIX_MODEL.md — Konteks & Spesifikasi Branch `fix-model`

**Proyek:** HepaTwin — GEMASTIK XIX 2026, Tim Kicau Mania
**Branch:** `fix-model`, dibuat dari `master`
**Cakupan:** Alur Kerja C (C1–C12) — Backend AI GATNN-DNN & Explainability SHAP
**PIC:** Kadek Vedo Putra Soma Raharja (Backend AI Engineer)
**Versi dokumen:** 1.0
**Status:** Draft — beberapa butir menunggu ratifikasi Ketua Tim / Farmasi (lihat §7)

> **Untuk agent (Claude Code):** baca dokumen ini SELURUHNYA sebelum menyentuh kode apa pun. Dokumen ini menjelaskan *apa* dan *mengapa*. Dokumen `EXECUTION_PLAN_FIX_MODEL.md` menjelaskan *bagaimana* dan *urutannya*. Jangan mulai dari execution plan tanpa membaca dokumen ini — ada empat temuan data (§4) yang akan membuat agent salah arah kalau dilewat.

---

## 1. Ringkasan Perubahan dari Pekerjaan Sebelumnya

Branch `upscale` (pekerjaan sebelumnya, TU.0–TU.22) sudah menghasilkan pipeline ML lengkap: arsitektur GATNN-DNN, nested cross-validation, external hold-out, uji signifikansi, dan **hyperparameter terbaik yang sudah tervalidasi**. Branch `fix-model` **tidak membuang** pekerjaan itu — ia memakainya ulang dengan tiga perubahan sumber data & lingkup:

| Aspek | Branch `upscale` (lama) | Branch `fix-model` (baru) |
|---|---|---|
| **Sumber SMILES** | Resolusi online nama obat → PubChem PUG REST (berjam-jam, 8% gagal) | **Sudah tersedia di Supabase** (`hepatwin_compounds.canonical_smiles`) — tidak ada panggilan PubChem sama sekali |
| **Sumber label DILI** | DILIrank 2.0 (file CSV mentah) | **Supabase** kolom `dili_concern` (isi identik DILIrank 2.0) |
| **Dataset kedua** | LiverTox digabung jadi baris training (Arm B) — terbukti **menurunkan** performa | **Tidak ada Arm B.** LiverTox hanya mengisi kolom `injury_pattern` untuk *lookup* zona, bukan baris training |
| **Explainability** | SHAP pada 9 flag SMARTS → keluaran `List[str]` nama gugus | **SHAP tingkat atom** untuk highlight molekul 2D (lihat §4.4) |
| **Hyperparameter** | Dicari lewat nested CV (10-fold, ~70 menit) | **Sudah ketemu, dipakai langsung** (§3) — tidak perlu diulang |
| **Runtime** | `app/` belum terhubung database | `master` sudah punya Supabase, repository, lookup service, PBPK engine |

**Prinsip utama branch ini:** ini pekerjaan **integrasi & penajaman**, bukan riset ulang dari nol. Sebagian besar kode `ml/` dari `upscale` dipakai ulang apa adanya.

---

## 2. Arsitektur Sistem (Konteks Besar)

HepaTwin punya **dua mesin komputasi paralel yang independen** — keduanya tidak saling memanggil:

```
                    Pengguna pilih senyawa (autocomplete)
                                  │
                    Lookup Supabase by hepatwin_id
                    (offline, deterministik, tanpa API luar)
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼─────────┐      ┌──────────▼──────────┐
          │  MESIN AI (C)     │      │  MESIN PBPK (D)     │
          │  ← LINGKUP KITA   │      │  ← PIC: Faris       │
          │                   │      │                     │
          │ SMILES → graf     │      │ Dosis + kovariat    │
          │       + ECFP4     │      │ → solver ODE        │
          │       ↓           │      │ → C_hati(t)         │
          │  GATNN-DNN        │      │ → Cmax, AUC         │
          │       ↓           │      │                     │
          │  P(DILI) + SHAP   │      │                     │
          └─────────┬─────────┘      └──────────┬──────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    LAPISAN FUSI RULE-BASED (F)
                    + LOOKUP ZONA dari database
                                  │
                    Visualisasi 3D Couinaud (E)
```

**Lingkup branch `fix-model` = kotak "MESIN AI (C)" saja.** Jangan menyentuh `pbpk_engine.py`, jangan mengubah logika fusi di luar yang diminta C10, jangan menyentuh frontend.

---

## 3. Hyperparameter Final (Sudah Tervalidasi — JANGAN DICARI ULANG)

Hasil nested cross-validation 10-fold pada branch `upscale` (`ml/reports/22_final_holdout_eval.json`), dipilih sebagai modus dari 10 fold outer:

```yaml
gatnn_dnn:
  lr: 0.0005
  hidden: 64
  dropout: 0.2
```

**Arsitektur yang menyertainya (tetap, dari `upscale`):**

| Komponen | Nilai |
|---|---|
| Layer graf | `GATv2Conv` × 2, `heads=4`, `edge_dim=6`, `concat=True` |
| Aktivasi graf | ELU |
| Pooling | `global_mean_pool` |
| Node features | **34 dimensi** |
| Edge features | **6 dimensi** |
| Cabang DNN | Linear(1200→512) → Linear(512→128), ReLU + Dropout |
| Fusion | concat(graf 256 + DNN 128) = 384 → Linear(384→128) → Linear(128→1) |
| Keluaran | **LOGIT** (bukan probabilitas — sigmoid hanya saat inferensi setelah kalibrasi) |
| Loss | `BCEWithLogitsLoss` dengan `pos_weight` dari train fold saja |
| Optimizer | AdamW, `weight_decay=1e-4` |
| Scheduler | `ReduceLROnPlateau(factor=0.5, patience=10)` |
| Early stopping | `patience=30`, monitor `val_auc` |

**Baseline pembanding (C7) yang sudah ada di `upscale/ml/src/hepatwin_ml/models/baselines.py`:**
Random Forest, LightGBM, XGBoost, Logistic Regression, MLP — semua dengan pembobotan kelas. C7 secara eksplisit meminta pembanding "ECFP4 + XGBoost", dan XGBoost sudah tersedia dengan hyperparameter final `max_depth=5, learning_rate=0.1`.

---

## 4. 🔴 EMPAT TEMUAN DATA — WAJIB DIPAHAMI SEBELUM MULAI

Temuan berikut berasal dari analisis langsung `hepatwin_compounds_rows.csv` (1.336 baris, 42 kolom). Semuanya diverifikasi dengan eksekusi kode, bukan asumsi.

### 4.1 Zona kerusakan BUKAN task machine learning — ini lookup deterministik

Ada anggapan bahwa zona kerusakan perlu **diprediksi** model. Data menunjukkan itu tidak diperlukan, dan secara desain tidak diinginkan.

**Bukti 1 — zona adalah fungsi 1:1 dari `injury_pattern`, tanpa variasi sama sekali:**

| `injury_pattern` | n | `histologic_zone` | `segment_count` | `hotspot_display_mode` | `hotspot_base_intensity` |
|---|---|---|---|---|---|
| Hepatoseluler | 252 | Zona 3 (perivenosa) | 4 | focal | high |
| Kolestatik | 131 | Zona 1 (periportal) | 3 | focal | high |
| Campuran | 44 | Zona 1 + Zona 3 | 8 | diffuse | low |
| Tidak Terklasifikasi | 909 | Tidak ditentukan | 8 | diffuse | dim |

Tidak ada satu pun baris yang menyimpang dari pemetaan ini. Artinya `histologic_zone`, `segment_count`, `hotspot_display_mode`, dan `hotspot_base_intensity` **bukan informasi independen** — semuanya tabel lookup dari `injury_pattern`. Memprediksi "zona" identik dengan memprediksi `injury_pattern`.

**Bukti 2 — PRD & kode runtime sudah memperlakukannya sebagai lookup.** PRD Bagian 6.6 menyebut pemetaan segmen Couinaud dilakukan "**lookup** ... via primary key `hepatwin_id` secara **deterministik dan offline**". Kode `app/services/simulation_orchestrator.py` di `master` sudah mengambil `compound.injury_pattern` dan `compound.segment_list` langsung dari database.

**Bukti 3 — sistem memakai database tertutup.** Autocomplete hanya menampilkan 1.231 senyawa `is_simulatable = TRUE` (Keputusan Desain Final, Dokumen Kerja Internal Bagian 2). Pengguna **tidak bisa** memasukkan SMILES bebas. Artinya setiap senyawa yang bisa disimulasikan **sudah punya zona-nya di database**. Tidak ada senyawa "tak dikenal" yang perlu diprediksi zonanya saat runtime.

**Kesimpulan:** jalur zona di `fix-model` = **verifikasi lookup**, bukan model baru. Tidak ada task ML untuk zona di C1–C12.

**Satu-satunya celah ML yang sah (dan sifatnya opsional, bukan bagian C1–C12):** 824 senyawa `is_simulatable=TRUE` berstatus "Tidak Terklasifikasi" karena tidak ada monograf LiverTox. Model *bisa* dipakai mengisi kekosongan itu (*imputasi*), dilatih dari 407 senyawa yang punya label. Tapi ini berisiko: keluarannya adalah **tebakan model** yang akan tampil di alat edukasi medis seolah-olah fakta terkurasi. Kalau tim mau menempuh ini, wajib: (a) ditandai eksplisit di UI sebagai "prediksi, bukan kurasi", (b) divalidasi Farmasi, (c) dikerjakan sebagai task terpisah **setelah** C1–C12 selesai. Lihat gerbang **G3** di §7.

### 4.2 Tox21 tidak ada di database ini

Ada anggapan bahwa data zona berasal dari "berbagai artikel dan Tox21". Hasil pemeriksaan seluruh 42 kolom: **string "Tox21" tidak muncul di mana pun.**

Sumber sebenarnya:

| Kolom | Isi |
|---|---|
| `data_source_dili` | `FDA DILIrank 2.0 [14]` — 1.336 baris (100%) |
| `data_source_injury` | `LiverTox [22]` — 806 baris; `Tidak ada monograf LiverTox` — 530 baris |
| `data_source_descriptor` | `PubChem PUG REST [13]` — 1.231; `Tidak tersedia` — 105 |

Jadi: **label risiko 100% dari DILIrank, pola cedera 100% dari LiverTox, deskriptor dari PubChem.** Tidak ada Tox21, tidak ada "berbagai artikel". Ini perlu diluruskan sebelum masuk ke proposal/presentasi supaya tidak jadi klaim yang tidak bisa dipertahankan di Jury Challenge.

*(Catatan: Tox21 memang pernah diuji di branch `upscale` sebagai auxiliary task — hasilnya netral, tidak signifikan. Itu eksperimen terpisah, tidak masuk database ini.)*

### 4.3 "Korpus training 1.231" tidak bisa diambil harfiah

Dokumen Kerja Internal C5 dan PRD menyebut korpus training GATNN-DNN = **1.231 senyawa** (`is_simulatable = TRUE`). Masalahnya: **336 dari 1.231 itu berlabel `Ambiguous-DILI-concern`** — kategori yang menurut FDA sendiri tidak konklusif. Senyawa ini **tidak punya label biner** yang bisa dipelajari model. Memaksakannya masuk berarti mengarang label yang tidak ada dasarnya.

Rincian 1.231 senyawa `is_simulatable = TRUE`:

| `dili_concern` | n | Bisa dilatih? |
|---|---|---|
| vNo-DILI-concern | 357 | ✅ → label 0 |
| vLess-DILI-concern | 332 | ✅ → label 1 |
| vMost-DILI-concern | 206 | ✅ → label 1 |
| **Ambiguous-DILI-concern** | **336** | ❌ tidak ada label biner |

**Hasil simulasi pipeline (dieksekusi dengan RDKit, bukan estimasi):**

| Tahap | n |
|---|---|
| `is_simulatable = TRUE` (punya SMILES) | 1.231 |
| Buang `Ambiguous-DILI-concern` | 895 |
| Gagal parse RDKit | 0 |
| Setelah standardisasi + dedup InChIKey | **870** |
| — tabrakan dedup (garam vs basa bebas menyatu) | 25 |
| — InChIKey dengan **label bertentangan** setelah menyatu | **2** ⚠️ |

**Dataset training final ≈ 870 senyawa** (528 positif / 342 negatif). Angka ini sangat dekat dengan Arm A `upscale` (839) — jadi performa yang diharapkan sebanding.

**Cara menyampaikannya yang jujur:** "korpus 1.231" itu benar sebagai **lingkup senyawa yang dapat disimulasikan**, tapi **korpus berlabel untuk training = 870**. Dua angka berbeda dengan arti berbeda; jangan disamakan di dokumen mana pun. Lihat gerbang **G1** di §7.

### 4.4 SHAP harus tingkat ATOM, bukan sekadar nama gugus

Ini perubahan terbesar dari `upscale`. PRD menuntut jauh lebih detail dari yang sudah ada:

> PRD §Interpretabilitas: *"Sistem menghitung nilai Shapley untuk **setiap atom** pada graf molekul dan memvisualisasikan gugus kimia pemicu (toxicophore) melalui penyorotan warna merah/jingga pada **diagram 2D molekul**."*
>
> PRD FR-06: *"panel visualisasi 2D molekul dengan penyorotan warna pada **atom/gugus** dengan kontribusi SHAP tertinggi."*

Perbandingan:

| | `upscale` (lama) | Yang dituntut PRD |
|---|---|---|
| Objek SHAP | 9 flag SMARTS (biner ada/tidak) | **Tiap atom** di molekul |
| Keluaran | `List[str]` nama gugus | Indeks atom + nilai Shapley + nama gugus |
| Konsumsi frontend | Teks saja | Highlight warna di gambar molekul 2D |

Skema API `master` saat ini (`app/models/schemas.py`) juga masih `explainability_shap: List[str]` — hanya menampung nama, belum bisa menampung atribusi per-atom. **Kontrak API perlu diperluas**, dan itu wajib dikoordinasikan dengan Faris (C10 memang menyebut "koordinasi dengan Faris (kontrak API)").

---

### 4.5 Skor DILI dan tampilan zona bisa saling bertentangan di layar

Karena `dili_score` datang dari **model** (dilatih pada `dili_concern`) sedangkan zona datang dari **lookup LiverTox**, keduanya bisa tidak sinkron. Dua pola kontradiksi nyata di database:

| Pola | n | Yang muncul di layar |
|---|---|---|
| `vNo-DILI-concern` **tapi** punya zona spesifik | **24** | Skor rendah/hijau, tapi segmen tertentu ter-*highlight* `focal` + intensitas `high` — contoh: Brivaracetam, Betrixaban, Avanafil |
| `vMost-DILI-concern` **tapi** zona tidak diketahui | **86** | Skor tinggi/merah, tapi hotspot `diffuse` + intensitas `dim` (8 segmen menyala redup) — contoh: Acetazolamide, Amineptine, Alclofenac |

Pola pertama berpotensi terbaca pengguna sebagai *"obat ini aman, tapi kok lobus kanannya ditandai rusak?"*. Pola kedua sebagai *"risikonya tinggi, tapi kok visualnya paling redup?"*.

Ini **bukan bug** — kedua sumber memang mengukur hal berbeda (`dili_concern` = tingkat kekhawatiran FDA; `injury_pattern` = pola cedera yang dilaporkan LiverTox bila cedera terjadi). Tapi lapisan fusi perlu memutuskan bagaimana menampilkannya supaya tidak menyesatkan — misalnya intensitas hotspot diikat ke `dili_score`, bukan ke `hotspot_base_intensity` statis dari database.

**Ini persoalan Alur F (fusi), PIC Faris — bukan lingkup C1–C12.** Tapi wajib diangkat karena keluaran Mesin AI (`dili_score`) yang jadi salah satu inputnya. Lihat gerbang **G7** di §7.

---

## 5. Kondisi Kode Saat Ini

### 5.1 Yang sudah ADA dan BENAR di `master` (jangan dibongkar)

Faris sudah membangun lapisan runtime:

| File | Fungsi |
|---|---|
| `app/core/database.py` | Koneksi Supabase/SQLAlchemy |
| `app/repositories/compound_repository.py` | Query senyawa by `hepatwin_id` |
| `app/services/lookup_service.py` | Resolver senyawa offline |
| `app/services/pbpk_engine.py` | Solver ODE PBPK (**Alur D — bukan lingkup kita**) |
| `app/api/endpoints/compounds.py` | Endpoint autocomplete |
| `app/core/validators/compound_validator.py` | Validasi input |
| `tests/security/test_is_simulatable_enforcement.py` | Uji `is_simulatable` ditegakkan |
| `app/services/simulation_orchestrator.py` | Fusi + lookup zona (sudah benar untuk zona) |

### 5.2 Yang HARUS DIGANTI di `master`

`app/services/ai_engine.py` — masih versi lama dengan lima cacat yang sudah teridentifikasi dan sudah diperbaiki di `upscale`:

| # | Cacat | Dampak |
|---|---|---|
| 1 | `GCNConv`, bukan `GATv2Conv` | Bukan arsitektur GATNN yang diminta C4 & PRD |
| 2 | `nn.Sigmoid()` di dalam `forward()` | Training tidak stabil; menghalangi kalibrasi |
| 3 | Node feature: 4 nilai riil di-*pad* nol sampai 9 | Membuang informasi kimia |
| 4 | `predict_dili_risk()` `return 0.5` diam-diam saat model gagal dimuat | **Cacat integritas** — API mengembalikan "prediksi" padahal tidak ada model |
| 5 | SHAP loop satu-per-satu di Python | Ratusan forward pass serial → melanggar anggaran latensi ≤5 detik (PRD UC-02) |
| 6 | `SMARTS_PATTERNS` versi lama (`N(=O)=O`, `c1ccccc1O`) | Pola nitro & fenol salah secara kimia komputasi |

### 5.3 Yang bisa DIPAKAI ULANG dari `upscale`

Salin dari branch `upscale` ke `fix-model`, sebagian besar tanpa perubahan:

| File | Status |
|---|---|
| `ml/src/hepatwin_ml/features/graph.py` | ✅ pakai apa adanya (34-dim node, 6-dim edge) |
| `ml/src/hepatwin_ml/features/fingerprints.py` | ✅ pakai apa adanya (MACCS 167 + ECFP4 1024 + SMARTS 9 = 1.200) |
| `ml/src/hepatwin_ml/features/smarts.py` | ✅ pakai apa adanya (9 pola, nitro & fenol sudah diperbaiki) |
| `ml/src/hepatwin_ml/models/gatnn_dnn.py` | ✅ pakai apa adanya |
| `ml/src/hepatwin_ml/models/baselines.py` | ✅ pakai apa adanya (5 baseline) |
| `ml/src/hepatwin_ml/data/splits.py` | ✅ pakai apa adanya |
| `ml/src/hepatwin_ml/data/holdout.py` | ✅ pakai apa adanya |
| `ml/src/hepatwin_ml/{train,evaluate,calibrate}.py` | ✅ pakai apa adanya |
| `ml/src/hepatwin_ml/{nested_cv,significance}.py` | ⚪ opsional — hyperparameter sudah final, tidak perlu dijalankan lagi |
| `ml/src/hepatwin_ml/data/resolve_smiles.py` | ❌ **BUANG** — tidak ada resolusi PubChem lagi |
| `ml/src/hepatwin_ml/data/harmonize_labels.py` | 🔧 sesuaikan ke kolom `dili_concern` Supabase |
| `ml/src/hepatwin_ml/data/standardize.py` | 🔴 **WAJIB DIUBAH** — lihat §5.4 |
| `ml/src/hepatwin_ml/explain.py` | 🔴 **DITULIS ULANG** — SHAP tingkat atom (§4.4) |

### 5.4 🔴 Perubahan wajib pada `standardize.py`

Versi `upscale` memakai `check_eligibility` yang **menolak** SMILES multi-fragmen (melempar `MixtureError`). Itu aman dulu karena PubChem umumnya mengembalikan bentuk induk.

**Sekarang tidak aman:** database menyimpan bentuk garam apa adanya. **566 dari 1.231 SMILES (46%) mengandung titik (`.`)** — contoh: `Abacavir sulfate`, `Acamprosate calcium`, `Acebutolol hydrochloride`. Kalau perilaku lama dipertahankan, **hampir separuh database akan ditolak.**

**Perbaikan:** ganti perilaku *menolak* menjadi *mengambil fragmen terbesar* (`LargestFragmentChooser`), lalu netralisasi muatan. Sudah diverifikasi: dengan perbaikan ini, 895 → 870 senyawa, 0 gagal parse.

**Efek samping yang harus ditangani:** menyatukan garam & basa bebas memunculkan **25 tabrakan InChIKey**, dan **2 di antaranya punya label DILI yang bertentangan**. Perlu aturan resolusi eksplisit (gerbang **G2**, §7).

---

## 6. Batas Lingkup (Scope Guard)

Agent **tidak boleh** mengerjakan hal berikut meskipun terlihat relevan. Kalau muncul dorongan ke arah ini, catat di `ml/reports/backlog.md` lalu lanjutkan:

- Menyentuh `app/services/pbpk_engine.py` (Alur D, PIC Faris)
- Mengubah logika autocomplete / `compound_repository.py` / `lookup_service.py` (Alur B & D)
- Mengubah frontend, aset 3D, atau React Three Fiber (Alur E)
- Melatih model untuk memprediksi zona/`injury_pattern` (§4.1 — bukan bagian C1–C12)
- Menghidupkan lagi Arm B (DILIrank + LiverTox digabung) — sudah terbukti signifikan lebih buruk (p<0,0001)
- Integrasi FAERS, Tox21, atau DDInter ke training
- Mengulang nested CV / pencarian hyperparameter (§3 — sudah final)
- Continuous learning / auto-retraining (C9 secara eksplisit melarang: model **statis**)
- Mengubah 105 senyawa `is_simulatable = FALSE` agar ikut diproses (Keputusan Desain Final)

---

## 7. Gerbang Keputusan Manusia

Agent **tidak boleh menebak** jawaban gerbang berikut. Bila belum ada keputusan, implementasikan opsi default, tandai `[KEPUTUSAN AI — PENDING REVIEW]` di kode & laporan, lalu lanjutkan.

| ID | Pertanyaan | Ke siapa | Default sementara | Memblokir |
|---|---|---|---|---|
| **G1** | Korpus training = 870 berlabel (buang Ambiguous) atau tetap klaim 1.231? | Ketua Tim | 870 berlabel; 1.231 tetap dipakai untuk menyebut *lingkup simulatable* | C5 — tidak memblokir, tapi wajib diluruskan sebelum proposal final |
| **G2** | 2 InChIKey berlabel bertentangan setelah dedup garam↔basa — mana yang menang? | Farmasi | Ambil label **paling konservatif** (positif menang) + catat di laporan | C5 |
| **G3** | Apakah tim mau model imputasi `injury_pattern` untuk 824 senyawa tak terklasifikasi? | Ketua Tim + Farmasi | **Tidak** — di luar C1–C12 | Tidak memblokir apa pun |
| **G4** | Nama & interpretasi klinis 9 pola SMARTS (dipakai di panel SHAP yang dilihat pengguna) | Farmasi | Pakai daftar `upscale` apa adanya, ditandai belum tervalidasi | C8 — tidak memblokir, tapi wajib sebelum rilis |
| **G5** | Ambang `risk_level` (low/medium/high) untuk warna hotspot 3D | Farmasi | Ambang yang sudah ada di `simulation_orchestrator.py` | Tidak memblokir |
| **G6** | Skema kontrak API SHAP tingkat atom (field baru di `SimulationResponse`) | Ketua Tim + Faris | Usulan di `EXECUTION_PLAN_FIX_MODEL.md` C10 | C10 |
| **G7** | Kontradiksi skor↔zona (§4.5): intensitas hotspot diikat ke `dili_score` atau ke `hotspot_base_intensity` statis? | Ketua Tim + Faris + Farmasi | Tidak diubah dari perilaku `master` saat ini | Tidak memblokir C1–C12 (isu Alur F) |

---

## 8. Definition of Done (Ringkasan Tingkat Proyek)

Detail per task ada di `EXECUTION_PLAN_FIX_MODEL.md`. Ringkasnya, branch `fix-model` selesai bila:

- [ ] Branch `fix-model` ada, bercabang dari `master`, `master` tidak tersentuh
- [ ] Dataset training terbangun **dari Supabase**, nol panggilan PubChem, jumlah senyawa terdokumentasi per tahap penyaringan
- [ ] `model_gatnn_dnn.pt` terlatih dengan hyperparameter §3, tersimpan, bukan bobot acak
- [ ] Laporan evaluasi lengkap + pembanding baseline (termasuk XGBoost, sesuai C7)
- [ ] Kalibrasi probabilitas terpasang, ECE & Brier dilaporkan sebelum/sesudah
- [ ] SHAP tingkat atom berfungsi, terverifikasi masuk akal secara kimia pada parasetamol & ibuprofen (C8)
- [ ] `app/services/ai_engine.py` diganti versi GATNN-DNN, **tidak ada lagi `return 0.5` diam-diam**
- [ ] Endpoint inferensi berfungsi, latensi end-to-end < 5 detik (PRD UC-02)
- [ ] Unit test lulus untuk senyawa valid, SMILES invalid, dan edge case (C11)
- [ ] Dokumentasi arsitektur & keputusan desain siap audit juri (C12)
- [ ] Seluruh keterbatasan tercatat jujur, termasuk yang tidak sesuai ekspektasi

---

## 9. Prinsip Kerja (Wajib Dipatuhi Agent)

1. **Jangan mengarang angka.** Setiap jumlah senyawa, metrik, atau statistik harus berasal dari eksekusi kode nyata. Dilarang menulis estimasi ke laporan seolah-olah hasil.
2. **Kegagalan adalah keluaran yang sah.** Kalau performa lebih rendah dari harapan, catat apa adanya. Jangan menyetel ulang skema demi angka yang lebih bagus.
3. **Bedakan keputusan tim vs keputusan AI.** Setiap keputusan yang diambil agent sendiri wajib ditandai `[KEPUTUSAN AI — PENDING REVIEW]`.
4. **Satu task = satu commit**, format `C<n>: <ringkasan>`.
5. **Berhenti di gerbang.** Jangan menebak jawaban G1–G6.
6. **Jangan melebarkan cakupan** (§6).
7. **`master` baca-saja** selama pengerjaan. Merge ke `master` adalah keputusan terpisah Ketua Tim.
8. **Jangan pernah commit kredensial.** `.env` wajib ada di `.gitignore`. Kunci Supabase (terutama `SUPABASE_SERVICE_ROLE_KEY`) tidak boleh masuk kode, laporan, notebook, atau pesan commit.

---

## 10. Referensi

- Wibowo, A.S., Chong, K.T., & Tayara, H. (2025). Enhancing DILI toxicity prediction through integrated graph attention (GATNN) and dense neural networks (DNN). *Toxicology, 514*, 154108. — arsitektur rujukan C4
- FDA LTKB. *Drug Induced Liver Injury Rank (DILIrank 2.0) Dataset.* — sumber `dili_concern`
- NIDDK/NLM. *LiverTox: Clinical and Research Information on Drug-Induced Liver Injury.* — sumber `injury_pattern`
- Lundberg, S.M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS 30.* — dasar SHAP (C8)
- Dokumen internal: `HepaTwin_PRD.md`, `Dokumen_Kerja_Internal.docx` (Alur Kerja C), `Panduan_Training_GATNN-DNN_vs_Konvensional.md`
- Artefak branch `upscale`: `ml/reports/22_final_holdout_eval.json` (hyperparameter final), `ml/reports/14_final_comparison.md`, `ml/reports/limitations.md`
