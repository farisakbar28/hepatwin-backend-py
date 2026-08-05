# EXECUTION_PLAN_FIX_MODEL.md — Rencana Eksekusi Agent (C1–C12)

**Repo:** `hepatwin-backend-py`
**Branch:** `fix-model`, dibuat dari `master`
**Dokumen induk:** `PROJECT_FIX_MODEL.md` — **WAJIB dibaca lebih dulu**
**Alur Kerja:** C — Backend AI GATNN-DNN & Explainability SHAP
**Versi:** 1.0

---

## Aturan Main untuk Agent

Baca sepenuhnya sebelum mengeksekusi task mana pun.

1. **Baca `PROJECT_FIX_MODEL.md` dulu.** Ada 4 temuan data (§4) yang akan membuat agent salah arah kalau dilewat — terutama: zona bukan task ML, korpus training 870 bukan 1.231, SMILES 46% berupa garam, dan SHAP harus tingkat atom.
2. **Kerjakan berurutan** sesuai dependensi. C1 → C2 → C3 → C4 → C5 → C6 → {C7, C8, C9} → C10 → C11 → C12.
3. **Satu task = satu commit**, format `C<n>: <ringkasan>`.
4. **Jangan mengarang angka.** Semua metrik dari eksekusi nyata.
5. **Kegagalan itu keluaran yang sah.** Catat apa adanya.
6. **Berhenti di gerbang 🔴.** Jangan menebak G1–G6 (`PROJECT_FIX_MODEL.md` §7).
7. **Jangan melebarkan cakupan** (`PROJECT_FIX_MODEL.md` §6).
8. **`master` baca-saja.** Jangan commit ke `master`, jangan merge.
9. **Jangan pernah commit `.env` atau kunci Supabase apa pun.**
10. **Windows path:** pakai forward slash atau prefix `r"..."`.

---

## Peta Task

| Kode | Task | Gerbang | Perkiraan |
|---|---|---|---|
| **C0** | *(pra-syarat)* Bootstrap branch + port `ml/` dari `upscale` | — | 1–2 jam |
| **C1** | Setup environment riset & pelatihan | — | 1 jam |
| **C2** | Ekstraksi fitur molekul (ECFP4) dari SMILES Supabase | — | 3–4 jam |
| **C3** | Konstruksi graf molekul untuk GATNN | — | 2 jam |
| **C4** | Dokumentasi desain arsitektur GATNN-DNN | — | 2 jam |
| **C5** | Split dataset train/val/test | 🔴 G1, G2 | 2–3 jam |
| **C6** | Pelatihan model & checkpointing | — | 2–4 jam |
| **C7** | Evaluasi metrik + pembanding baseline | — | 3 jam |
| **C8** | Explainability SHAP tingkat atom | 🔴 G4 | 5–7 jam |
| **C9** | Pembekuan model untuk deployment (statis) | — | 1–2 jam |
| **C10** | Wrapping model sebagai layanan inferensi | 🔴 G6 | 4–5 jam |
| **C11** | Unit test endpoint inferensi | — | 2–3 jam |
| **C12** | Dokumentasi arsitektur & keputusan desain | — | 2–3 jam |

**Jalur yang tidak terblokir dan bisa langsung dikerjakan:** C0 → C1 → C2 → C3 → C4 → C6 → C7. Gerbang manusia menggigit di C5 (G1/G2), C8 (G4), dan C10 (G6) — semuanya punya nilai default sehingga agent tetap bisa lanjut sambil menandai status pending.

---

## C0 — Bootstrap Branch & Port Kode dari `upscale`

*(Bukan bagian resmi C1–C12, tapi wajib dikerjakan lebih dulu.)*

**Tujuan:** siapkan branch `fix-model` berisi lapisan runtime `master` **dan** pipeline ML `upscale`, tanpa merusak salah satunya.

**Langkah:**
1. `git checkout master && git pull` → pastikan mulai dari `master` terbaru (yang sudah berisi integrasi Supabase Faris).
2. `git checkout -b fix-model`
3. Salin direktori `ml/` dari branch `upscale`:
   ```
   git checkout upscale -- ml/
   ```
4. **Hapus** file yang sudah tidak relevan:
   - `ml/src/hepatwin_ml/data/resolve_smiles.py` (tidak ada resolusi PubChem lagi)
   - `ml/src/hepatwin_ml/data/build_livertox.py` (tidak ada Arm B)
   - `ml/src/hepatwin_ml/data/build_dataset.py` (akan diganti loader Supabase di C2)
   - `ml/data/raw/`, `ml/data/interim/`, `ml/data/processed/` (dataset lama, tidak dipakai)
   - `ml/src/hepatwin_ml/stretch/` (Tox21/FAERS, di luar cakupan)
5. **Pertahankan** `ml/reports/` dari `upscale` — pindahkan ke `ml/reports/_upscale_archive/` sebagai arsip riwayat (berguna untuk audit juri: menunjukkan hyperparameter berasal dari nested CV yang nyata).
6. Salin `PROJECT_FIX_MODEL.md` dan `EXECUTION_PLAN_FIX_MODEL.md` ke root repo.
7. Pastikan `.gitignore` root memuat: `.env`, `ml/data/`, `ml/models/*.pt`, `__pycache__/`, `.venv/`.
8. Commit: `C0: bootstrap branch fix-model, port pipeline ml/ dari upscale`

**Acceptance criteria:**
- [ ] Branch `fix-model` bercabang dari commit terbaru `master`
- [ ] `git diff master fix-model -- app/` **kosong** pada commit ini (belum menyentuh runtime)
- [ ] `ml/src/hepatwin_ml/models/gatnn_dnn.py` ada dan bisa di-`import`
- [ ] File yang dihapus di langkah 4 memang sudah tidak ada
- [ ] `.env` tidak ter-*track* git (`git check-ignore .env` mengembalikan hasil)

---

## C1 — Setup Environment Riset & Pelatihan Model

**DoD resmi (Dokumen Kerja Internal):** *Environment pelatihan berjalan stabil, reproducible, dan terdokumentasi pada requirements/environment file.*

**Langkah:**
1. Buat environment **terpisah** dari runtime FastAPI (sesuai instruksi C1: "agar tidak bertabrakan dengan dependency backend"):
   ```
   python -m venv .venv-ml
   ```
2. Susun `ml/requirements.txt`:
   ```
   torch>=2.3.1
   torch-geometric>=2.5.3
   rdkit>=2023.9.5
   pandas>=2.2.0
   numpy>=1.26.4
   scikit-learn>=1.4.0
   lightgbm>=4.0
   xgboost>=2.0
   shap>=0.45.1
   matplotlib>=3.8.0
   pyyaml>=6.0
   tqdm>=4.66.0
   pytest>=8.0.0
   psycopg2-binary>=2.9.9
   python-dotenv>=1.0.0
   ```
3. Kunci versi hasil instalasi ke `ml/requirements.lock.txt` (`pip freeze`) untuk reproduktibilitas.
4. Tulis `ml/README.md`: cara membuat environment, cara menjalankan pipeline, dan **peringatan bahwa `.env` tidak boleh di-commit**.
5. Verifikasi: `python -c "import torch, torch_geometric, rdkit, shap, lightgbm, xgboost"`

**Acceptance criteria:**
- [ ] `pip install -r ml/requirements.txt` berhasil di environment bersih
- [ ] Impor seluruh pustaka kunci tidak error
- [ ] `ml/requirements.lock.txt` ada
- [ ] Environment ML terpisah dari environment `app/` (dibuktikan: dua file requirements berbeda)

---

## C2 — Pipeline Ekstraksi Fitur Molekul (ECFP4) dari Supabase

**DoD resmi:** *Seluruh 1.231 senyawa `is_simulatable = TRUE` memiliki fingerprint ECFP4 yang valid; 105 biologik tanpa SMILES tidak masuk pipeline.*

> ⚠️ **Perhatikan bedanya:** DoD C2 bicara soal **fingerprint untuk 1.231 senyawa** (semua yang simulatable, termasuk Ambiguous — karena fingerprint dibutuhkan saat *inferensi* juga). Ini **berbeda** dari korpus *training* berlabel (≈870, lihat C5). Keduanya benar dan tidak bertabrakan: 1.231 = cakupan featurization, 870 = cakupan training.

**File baru:** `ml/src/hepatwin_ml/data/load_supabase.py`

**Langkah:**

*Bagian A — loader database (menggantikan resolusi PubChem):*
1. Baca kredensial dari `.env` lewat `python-dotenv` — **jangan hardcode**. Pakai `DATABASE_URL` (koneksi Postgres langsung) atau `SUPABASE_URL` + `SUPABASE_ANON_KEY`.
   - **Gunakan `SUPABASE_ANON_KEY`, bukan `SUPABASE_SERVICE_ROLE_KEY`.** Pipeline training hanya perlu baca; service role key melewati Row Level Security dan tidak boleh dipakai di skrip riset.
2. Query tabel `hepatwin_compounds`, ambil kolom: `hepatwin_id, compound_name, canonical_smiles, isomeric_smiles, inchikey, dili_concern, is_simulatable, injury_pattern, segment_list`.
3. Filter `is_simulatable = TRUE` → harus mengembalikan **1.231 baris**. Kalau tidak, hentikan dan laporkan selisihnya.
4. **Cache hasil query** ke `ml/data/interim/compounds_snapshot.parquet` beserta timestamp — supaya pipeline reproducible dan tidak bergantung ketersediaan jaringan saat re-run. Catat juga jumlah baris di laporan sebagai "snapshot pada tanggal X".

*Bagian B — standardisasi (🔴 PERUBAHAN WAJIB dari `upscale`):*

5. Ubah `ml/src/hepatwin_ml/data/standardize.py`: hilangkan perilaku **menolak** SMILES multi-fragmen (`MixtureError`). Ganti jadi **mengambil fragmen terbesar**:
   ```
   Cleanup → LargestFragmentChooser → Uncharger → hapus isotop → InChIKey
   ```
   **Alasan:** 566 dari 1.231 SMILES (46%) berupa garam multi-fragmen (`Abacavir sulfate`, `Acamprosate calcium`, dst.). Perilaku lama akan menolak hampir separuh database.
6. Hasilkan `smiles_standardized` + `inchikey_std` untuk tiap baris.

*Bagian C — fingerprint ECFP4:*

7. Pakai ulang `ml/src/hepatwin_ml/features/fingerprints.py` dari `upscale` apa adanya. Vektor DNN = **1.200 dimensi**: MACCS (167) + ECFP4 Morgan radius 2 folded (1024) + blok SMARTS (9).
8. Validasi: setiap senyawa `is_simulatable = TRUE` menghasilkan fingerprint tanpa error.

**Keluaran:** `ml/data/processed/features_all.parquet`

**Laporan wajib:** `ml/reports/C2_featurization.md` berisi tabel corong:

| Tahap | n |
|---|---|
| Total baris di `hepatwin_compounds` | ? |
| `is_simulatable = TRUE` | ? *(ekspektasi 1231)* |
| Berhasil parse RDKit | ? |
| Multi-fragmen (mengandung `.`) | ? *(ekspektasi ~566)* |
| Lolos standardisasi | ? |
| Fingerprint ECFP4 valid | ? |

**Acceptance criteria:**
- [ ] Nol panggilan PubChem/HTTP eksternal di seluruh pipeline (diverifikasi: tidak ada `import requests`/`pubchempy` di jalur data)
- [ ] 1.231 senyawa `is_simulatable = TRUE` semuanya punya fingerprint valid — bila ada yang gagal, laporkan daftarnya, jangan diam-diam dibuang
- [ ] 105 senyawa `is_simulatable = FALSE` **tidak** masuk pipeline (dibuktikan lewat test)
- [ ] Dimensi fingerprint terverifikasi = 1.200
- [ ] `.env` tidak muncul di `git status`

---

## C3 — Konstruksi Graf Molekul untuk Input GATNN

**DoD resmi:** *Pipeline konversi SMILES → graf berjalan otomatis dan konsisten, baik pada pelatihan maupun inferensi senyawa `is_simulatable = TRUE`.*

**Langkah:**
1. Pakai ulang `ml/src/hepatwin_ml/features/graph.py` dari `upscale` **apa adanya**. Skema sudah final:
   - **Node: 34 dimensi** — jenis atom one-hot (10: C,N,O,S,F,Cl,Br,I,P,other), degree (6), muatan formal (5), jumlah H (5), hibridisasi (6), aromatik (1), dalam cincin (1)
   - **Edge: 6 dimensi** — jenis ikatan one-hot (4: single/double/triple/aromatic), terkonjugasi (1), dalam cincin (1)
2. Pastikan graf dibangun dari **`smiles_standardized`** (hasil C2), bukan `canonical_smiles` mentah — supaya training dan inferensi memakai representasi yang identik.
3. **Konsistensi training↔inferensi adalah inti DoD C3.** Buat satu fungsi tunggal yang dipakai kedua jalur, jangan ada dua implementasi terpisah yang berpotensi menyimpang.
4. Tangani edge case: molekul tanpa ikatan (mis. ion tunggal) tidak boleh membuat crash — kembalikan graf dengan `edge_index` kosong berbentuk `[2, 0]`.

**Acceptance criteria:**
- [ ] `pytest ml/tests/test_features.py` hijau
- [ ] Dimensi terverifikasi: node `[n_atoms, 34]`, `edge_index [2, n_bonds*2]`, `edge_attr [n_bonds*2, 6]`
- [ ] Featurisasi parasetamol menghasilkan jumlah atom & ikatan yang benar (cek manual)
- [ ] Fungsi yang sama dipakai di jalur training dan jalur inferensi (dibuktikan: satu titik impor)

---

## C4 — Desain Arsitektur Hybrid GATNN-DNN (Dokumentasi)

**DoD resmi:** *Rancangan arsitektur final (diagram dan justifikasi setiap komponen) terdokumentasi sebagai bahan audit teknis dan Jury Challenge.*

> Ini task **dokumentasi**, bukan koding. Arsitektur sudah ada (`gatnn_dnn.py` dari `upscale`).

**Langkah:**
1. Verifikasi `ml/src/hepatwin_ml/models/gatnn_dnn.py` sesuai spesifikasi `PROJECT_FIX_MODEL.md` §3.
2. Tulis `ml/reports/C4_arsitektur.md` berisi:
   - Diagram arsitektur dua cabang (graf + fingerprint → fusion → logit)
   - **Justifikasi tiap komponen**, bukan sekadar deskripsi:
     | Komponen | Justifikasi |
     |---|---|
     | `GATv2Conv` (bukan `GATConv`/`GCNConv`) | Mekanisme atensi dinamis lebih ekspresif; `GCNConv` versi `master` lama tidak punya atensi sama sekali padahal arsitektur yang diminta adalah **Graph Attention** |
     | `edge_dim=6` | Informasi jenis ikatan (rangkap/aromatik/cincin) relevan secara kimia untuk toksisitas; `GCNConv` tidak bisa memakainya |
     | Cabang DNN + ECFP4 | Mengikuti Wibowo dkk. (2025) — fingerprint menangkap substruktur global yang sulit ditangkap graf lokal |
     | Keluaran **logit** | `BCEWithLogitsLoss` numerik lebih stabil; sigmoid di dalam `forward()` (versi lama) menghalangi kalibrasi |
     | Blok SMARTS 9 dim di fingerprint | Prasyarat explainability — SHAP hanya bermakna bila fitur yang dijelaskan benar-benar memengaruhi prediksi |
   - Fungsi loss, metrik evaluasi, strategi regularisasi
   - **Asal-usul hyperparameter**: hasil nested CV 10-fold di branch `upscale`, rujuk `ml/reports/_upscale_archive/22_final_holdout_eval.json`. Ini penting untuk Jury Challenge — menunjukkan hyperparameter dipilih lewat proses tervalidasi, bukan tebakan.

**Acceptance criteria:**
- [ ] `ml/reports/C4_arsitektur.md` ada, memuat diagram + justifikasi per komponen
- [ ] Setiap angka hyperparameter dapat ditelusuri ke artefak `_upscale_archive/`
- [ ] Dokumen bisa dibaca berdiri sendiri oleh juri teknis tanpa perlu membaca kode

---

## C5 — Split Dataset Training/Validasi/Testing 🔴 G1, G2

**DoD resmi:** *Subset data terpisah jelas dan digunakan secara konsisten sepanjang pelatihan serta evaluasi model.*

**Langkah:**

1. **Bangun korpus berlabel** dari hasil C2:
   - Buang `Ambiguous-DILI-concern` → tidak punya label biner
   - Binerisasi: `vMost-DILI-concern` + `vLess-DILI-concern` → **1**; `vNo-DILI-concern` → **0**
   - Dedup berdasarkan `inchikey_std`

   **Angka yang diharapkan** (sudah diverifikasi dengan RDKit, laporkan angka aktual dan bandingkan):

   | Tahap | n |
   |---|---|
   | `is_simulatable = TRUE` | 1.231 |
   | Buang Ambiguous | 895 |
   | Setelah standardisasi + dedup InChIKey | **≈870** |
   | Tabrakan dedup (garam↔basa menyatu) | ≈25 |
   | Label positif / negatif | ≈528 / 342 |

2. 🔴 **Gerbang G2 — 2 InChIKey berlabel bertentangan** setelah garam & basa bebas menyatu. Default sementara: **label positif menang** (paling konservatif untuk alat keselamatan obat). Tandai `[KEPUTUSAN AI — PENDING REVIEW FARMASI]`, catat daftar senyawanya di laporan.

3. 🔴 **Gerbang G1 — angka korpus.** Laporkan **dua angka terpisah** dan jangan menyamakannya:
   - **1.231** = lingkup senyawa yang dapat disimulasikan (dipakai C2, inferensi)
   - **≈870** = korpus berlabel untuk training
   Tandai `[KEPUTUSAN AI — PENDING REVIEW KETUA TIM]`.

4. **Skema split** — pakai ulang `ml/src/hepatwin_ml/data/{splits,holdout}.py` dari `upscale`:
   - **Test set (hold-out):** 15–20%, **scaffold-disjoint** (Bemis-Murcko), dikunci sejak dibuat, tidak disentuh sampai C7
   - **Train/Validation:** sisanya, dibagi dengan **scaffold split** (bukan random murni)
   - Simpan daftar InChIKey tiap subset ke `ml/data/interim/split_manifest.json` sebagai segel reproduktibilitas

   > **Catatan terhadap teks DoD C5** yang menyebut split "secara stratifikasi berdasarkan label risiko": stratifikasi label tetap **diusahakan**, tapi bila bertabrakan dengan scaffold-disjoint, **scaffold-disjoint diprioritaskan**. Alasan: stratifikasi murni pada data molekul membuat senyawa berkerangka kimia sangat mirip tersebar di train dan test → kebocoran data terselubung, dan angka performa jadi optimistis palsu. Ini penyimpangan yang disengaja dari teks DoD dan **wajib dicatat eksplisit di laporan**, bukan dilakukan diam-diam.

5. Verifikasi anti-kebocoran: assert tidak ada `inchikey_std` maupun scaffold yang muncul di dua subset.

**Keluaran:** `ml/data/processed/{train,val,test}.parquet` + `split_manifest.json`

**Laporan:** `ml/reports/C5_split.md` — tabel corong lengkap, ukuran tiap subset, proporsi kelas, daftar 2 konflik label G2.

**Acceptance criteria:**
- [ ] `pytest ml/tests/test_splits.py` dan `test_holdout.py` hijau
- [ ] Bukti eksplisit: overlap InChIKey antar-subset = **0**
- [ ] Bukti eksplisit: overlap scaffold antar-subset = **0**
- [ ] Angka aktual dilaporkan dan dibandingkan dengan ekspektasi di atas; selisih besar → selidiki sebelum lanjut
- [ ] Dua angka korpus (1.231 vs ≈870) dibedakan jelas di laporan

---

## C6 — Pelatihan Model & Checkpointing

**DoD resmi:** *Checkpoint `model_gatnn_dnn.pt` tersimpan dan siap dievaluasi maupun dideploy.*

**Langkah:**
1. Pakai ulang `ml/src/hepatwin_ml/train.py` dari `upscale`.
2. **Hyperparameter — pakai langsung, JANGAN dicari ulang** (`PROJECT_FIX_MODEL.md` §3):
   ```yaml
   lr: 0.0005
   hidden: 64
   dropout: 0.2
   optimizer: AdamW
   weight_decay: 1e-4
   batch_size: 32
   max_epochs: 300
   early_stopping: patience=30, monitor=val_auc
   scheduler: ReduceLROnPlateau(factor=0.5, patience=10)
   loss: BCEWithLogitsLoss(pos_weight=<dihitung dari train fold SAJA>)
   ```
   > `pos_weight` **wajib** dihitung dari train split saja. Menghitungnya dari seluruh dataset adalah kebocoran data.
3. Pantau loss tiap epoch, simpan log ke `ml/reports/C6_train_log/`.
4. Simpan checkpoint **terbaik berdasarkan `val_auc`**, bukan checkpoint epoch terakhir.
5. Latih dengan **5 seed** `[42,43,44,45,46]`; laporkan mean ± std. Pilih **satu** model untuk produksi (seed=42, tetapkan di awal — bukan pilih yang kebetulan terbaik setelah melihat hasil, itu bentuk cherry-picking).
6. Simpan ke `ml/models/model_gatnn_dnn.pt` beserta metadata JSON: hyperparameter, seed, n_train, tanggal, hash split manifest.

**Acceptance criteria:**
- [ ] Training selesai tanpa error, loss turun (bila datar → ada bug, selidiki)
- [ ] `ml/models/model_gatnn_dnn.pt` ada dan bisa dimuat ulang
- [ ] Menjalankan ulang dengan seed sama → metrik identik (determinisme terverifikasi)
- [ ] Metadata JSON lengkap dan konsisten dengan `split_manifest.json`
- [ ] Checkpoint dipilih berdasar `val_auc`, dibuktikan lewat log

---

## C7 — Evaluasi Metrik Model

**DoD resmi:** *Laporan evaluasi kuantitatif model tersedia dan terdokumentasi untuk mendukung proses validasi (ASME V&V 40).*

**Langkah:**
1. Evaluasi pada **test set (hold-out)** yang dikunci sejak C5 — **satu kali saja**. Setelah dibuka, tidak boleh dipakai lagi untuk tuning.
2. Metrik wajib (DoD C7 menyebut sebagian; sisanya dari standar proyek):
   `accuracy, AUC-ROC, AUC-PR, precision, recall/sensitivity, specificity, F1, MCC, confusion matrix, Brier score, ECE`
3. **Baseline pembanding** — DoD C7 secara eksplisit meminta "mis. ECFP4 + XGBoost". Pakai ulang `ml/src/hepatwin_ml/models/baselines.py` dari `upscale`, latih pada split **yang sama persis**:
   | Baseline | Hyperparameter final dari `upscale` |
   |---|---|
   | XGBoost | `max_depth=5, learning_rate=0.1` |
   | Random Forest | `n_estimators=500, max_depth=None, class_weight=balanced` |
   | LightGBM | `num_leaves=15, learning_rate=0.1` |
   | Logistic Regression | `C=0.1, penalty=l2, class_weight=balanced` |
4. **Kalibrasi probabilitas** (`ml/src/hepatwin_ml/calibrate.py`): isotonic regression bila set kalibrasi ≥200 sampel, selain itu Platt. Laporkan Brier & ECE **sebelum vs sesudah**. Ini wajib karena `dili_score` menggerakkan intensitas warna hotspot 3D — bukan sekadar ranking.
5. Simpan kalibrator bersama bobot model.

**Konteks pembanding untuk laporan** (dari branch `upscale`, hold-out 167 senyawa):
| Model | AUC hold-out |
|---|---|
| GATNN-DNN | 0,682 |
| Random Forest | 0,691 |
| LightGBM | 0,691 |
| XGBoost | 0,667 |
| Logistic Regression | 0,637 |

> **Ekspektasi jujur:** AUC di kisaran **0,63–0,75** adalah hasil yang wajar untuk prediksi DILI pada dataset seukuran ini. 🚩 Bila AUC > 0,90, **hentikan dan audit kebocoran data** sebelum melaporkan apa pun — angka setinggi itu tidak wajar untuk masalah ini.

**Laporan:** `ml/reports/C7_evaluasi.md` — tabel metrik lengkap GATNN-DNN + 4 baseline, confusion matrix, kurva ROC & PR, kurva reliability sebelum/sesudah kalibrasi.

**Acceptance criteria:**
- [ ] Seluruh metrik terisi angka nyata, tidak ada placeholder
- [ ] Minimal XGBoost sebagai pembanding (sesuai teks DoD C7)
- [ ] ECE sesudah kalibrasi < ECE sebelum
- [ ] Test set terbukti dipakai satu kali (jelas di riwayat commit)
- [ ] Bila GATNN-DNN kalah dari baseline → **laporkan apa adanya**, jangan tuning sampai menang

---

## C8 — Integrasi Lapisan Explainability SHAP 🔴 G4

**DoD resmi:** *Output SHAP tersedia dalam format yang dapat dikonsumsi oleh frontend (Alur E).*

> 🔴 **Ini task dengan perubahan terbesar dari `upscale`.** Baca `PROJECT_FIX_MODEL.md` §4.4 dulu. PRD menuntut SHAP **tingkat atom** untuk highlight molekul 2D, sedangkan `upscale` hanya menghasilkan daftar nama gugus.

**File:** tulis ulang `ml/src/hepatwin_ml/explain.py`

**Langkah:**

1. **Dua tingkat atribusi** — implementasikan keduanya:

   **(a) Tingkat gugus (SMARTS)** — pakai ulang pendekatan `upscale`: SHAP `KernelExplainer` pada 9 flag SMARTS (`SMARTS_SLICE`). Menghasilkan nama gugus + nilai kontribusi. Ini yang mengisi `explainability_shap: List[str]` yang sudah ada di kontrak API.

   **(b) Tingkat atom** — **BARU**, dituntut PRD FR-06. Pendekatan yang disarankan (pilih salah satu, dokumentasikan alasannya):
   - **Occlusion/masking per-atom:** untuk tiap atom, matikan kontribusinya (mask fitur node → nol), ukur Δlogit. Sederhana, deterministik, cepat. **Wajib dilabeli jujur sebagai `"masking_attribution"`, bukan "SHAP"** — karena ini bukan nilai Shapley sebenarnya.
   - **`GNNExplainer` / `CaptumExplainer` dari PyTorch Geometric:** lebih dekat ke atribusi graf yang proper. PRD menyebut "Captum / SHAP" sebagai pustaka yang diterima, jadi ini sah.

   > **Aturan kejujuran:** field `method` wajib ada di keluaran dan berisi nama metode yang **benar-benar** dipakai. Menyebut hasil masking sebagai "SHAP" adalah klaim yang salah dan akan gugur di Jury Challenge.

2. **Anggaran latensi.** PRD UC-02 menuntut total ≤5 detik untuk AI + PBPK + fusi. Jatah SHAP realistis **< 2 detik**.
   - 🔴 **Wrapper wajib mem-batch** seluruh sampel sintetis SHAP dalam satu forward pass (`Batch.from_data_list`). Versi `master` lama melakukan loop satu-per-satu di Python — ratusan forward pass serial, hampir pasti melanggar anggaran.
   - Terapkan **cache per InChIKey**. Karena database tertutup (1.231 senyawa), cache akan sangat efektif — bahkan bisa **di-precompute seluruhnya** saat build. Pertimbangkan ini bila latensi masih ketat.

3. **Format keluaran** untuk frontend:
   ```json
   {
     "method": "masking_attribution",
     "groups": [
       {"name": "Acetamide / Amide group", "value": 0.12, "atom_indices": [3,4,5]}
     ],
     "atoms": [
       {"idx": 0, "value": -0.01},
       {"idx": 3, "value": 0.08}
     ],
     "smiles_used": "<smiles_standardized>"
   }
   ```
   `atom_indices` harus merujuk ke **`smiles_standardized`** (hasil C2), bukan SMILES mentah database — kalau tidak, indeks atom akan meleset saat frontend menggambar molekul. Sertakan `smiles_used` supaya frontend menggambar dari string yang sama.

4. **Uji kelayakan kimiawi** (diminta eksplisit oleh C8): jalankan pada **parasetamol** dan **ibuprofen**, periksa hasilnya masuk akal:
   - Parasetamol: gugus amida terasetilasi seharusnya muncul sebagai kontributor (konsisten dengan mekanisme NAPQI yang disebut PRD)
   - Ibuprofen: profil risiko rendah, tidak boleh menyoroti toxicophore berbahaya secara kuat
   - 🚩 Bila hasilnya tidak masuk akal secara kimia, **laporkan sebagai temuan**, jangan dipaksa cocok dengan ekspektasi.

5. 🔴 **Gerbang G4:** nama & interpretasi klinis 9 pola SMARTS akan tampil ke pengguna. Tandai `[KEPUTUSAN AI — PENDING REVIEW FARMASI]` sampai divalidasi Anggi.

**Laporan:** `ml/reports/C8_shap.md` — metode yang dipakai + alasannya, benchmark latensi (p50/p95 pada ≥50 molekul), hasil uji parasetamol & ibuprofen, keterbatasan.

**Acceptance criteria:**
- [ ] Keluaran memuat atribusi tingkat gugus **dan** tingkat atom
- [ ] Field `method` jujur menyebut metode sebenarnya
- [ ] Latensi explainability < 2 detik (p95) pada 50 molekul uji
- [ ] `atom_indices` konsisten dengan `smiles_used` (diverifikasi lewat test)
- [ ] Molekul tanpa satu pun match SMARTS → mengembalikan list kosong, **bukan** crash, **bukan** teks karangan
- [ ] Hasil parasetamol & ibuprofen terdokumentasi

---

## C9 — Pembekuan Model untuk Deployment (Statis, Bukan Continuous Learning)

**DoD resmi:** *Kebijakan statis, bukan continuous learning diterapkan secara konsisten pada backend dan terdokumentasi.*

**Langkah:**
1. Ekspor artefak final ke lokasi yang dibaca runtime:
   - `app/models/model_gatnn_dnn.pt` (bobot)
   - `app/models/calibrator_gatnn_dnn.pkl` (kalibrator dari C7)
   - `app/models/model_gatnn_dnn_metadata.json` (versi, seed, n_train, metrik hold-out, tanggal, hash)
2. Tulis skrip `ml/scripts/export_to_app.py` yang melakukan penyalinan ini secara terkontrol — jangan salin manual.
3. **Terapkan kebijakan statis di kode runtime:**
   - `model.eval()` wajib dipanggil setelah load
   - Bungkus seluruh inferensi dalam `torch.no_grad()`
   - **Tidak ada** jalur kode apa pun yang memanggil `.backward()`, `optimizer.step()`, atau menulis ulang file bobot saat runtime
4. Tulis `ml/reports/C9_kebijakan_model_statis.md`: alasan kebijakan (mencegah *model drift* dan *data poisoning*, sesuai teks C9), cara memperbarui model secara sengaja (proses manual + review), dan pernyataan bahwa tidak ada pembelajaran otomatis.
5. Update `AI_MODEL_PATH` di `app/core/config.py` agar menunjuk artefak baru.

**Acceptance criteria:**
- [ ] Artefak model + kalibrator + metadata ada di `app/models/`
- [ ] `model.eval()` dan `torch.no_grad()` terpasang, diverifikasi lewat test
- [ ] Pencarian kode membuktikan tidak ada `.backward()`/`optimizer` di dalam `app/`
- [ ] Dokumen kebijakan ada
- [ ] Model lama (`model.pt`, bila ada) **tidak ditimpa** — beri nama file berbeda supaya bisa dibandingkan

---

## C10 — Wrapping Model sebagai Layanan Inferensi Backend 🔴 G6

**DoD resmi:** *Endpoint inferensi AI berfungsi dan terintegrasi dengan router utama backend (Alur D/F).*

**Langkah:**

1. **Tulis ulang `app/services/ai_engine.py`** — ganti seluruh isinya dengan versi GATNN-DNN. Perbaiki enam cacat versi lama (`PROJECT_FIX_MODEL.md` §5.2):
   - `GCNConv` → `GATv2Conv`
   - Hapus `nn.Sigmoid()` dari `forward()`; terapkan sigmoid hanya setelah kalibrasi
   - Node features 34-dim penuh (bukan 4 di-*pad* jadi 9)
   - 🔴 **Hapus `return 0.5` diam-diam.** Bila artefak model tidak ada / gagal dimuat → `HTTPException(503)` dengan pesan eksplisit. Mengembalikan angka seolah-olah prediksi padahal tidak ada model adalah cacat integritas ilmiah, bukan sekadar bug.
   - SHAP ter-*batch* (dari C8)
   - Pakai `SMARTS_PATTERNS` versi terkoreksi

2. **Impor logika featurization dari `ml/`, jangan duplikasi.** Duplikasi kode fitur adalah sumber klasik ketidakcocokan training↔inferensi. Pilih salah satu: `ml/` dipasang sebagai paket lokal (`pip install -e ml/`), atau modul fitur dipindah ke lokasi bersama yang diimpor keduanya. Dokumentasikan pilihannya.

3. 🔴 **Gerbang G6 — perluasan kontrak API.** `SimulationResponse` saat ini punya `explainability_shap: List[str]` yang tidak bisa menampung atribusi per-atom. Usulan field baru (**wajib dikoordinasikan dengan Faris sebelum final** — C10 sendiri menyebut "koordinasi dengan Faris (kontrak API)"):

   | Field | Tipe | Isi |
   |---|---|---|
   | `explainability_shap` | `List[str]` | **Dipertahankan** — nama gugus, kompatibel dengan frontend yang sudah ada |
   | `shap_detail` | `object` | Struktur lengkap dari C8 (`method`, `groups`, `atoms`, `smiles_used`) |
   | `model_version` | `str` | mis. `"gatnn-dnn-fixmodel-v1"` |
   | `model_status` | `"trained" \| "unavailable"` | Wajib — mencegah kebingungan model asli vs tidak ada |
   | `score_is_calibrated` | `bool` | |

   Menambah field baru dan mempertahankan yang lama bersifat *backward-compatible* — frontend Faris tidak akan pecah.

4. Pastikan endpoint tetap menghormati `is_simulatable` — senyawa `FALSE` tidak boleh sampai ke pipeline AI (test keamanan yang sudah ada di `master` harus tetap hijau).

5. Perbaiki juga: exception handler global versi lama membocorkan string error mentah ke klien. Ganti dengan pesan generik + logging sisi server.

**Acceptance criteria:**
- [ ] `git diff master fix-model -- app/` menunjukkan perubahan terbatas pada `ai_engine.py`, `schemas.py`, `config.py`, exception handler — **bukan** membongkar struktur `app/`
- [ ] Test: hapus file model → endpoint balas **503**, bukan 200 dengan skor 0,5
- [ ] Tidak ada duplikasi kode featurization antara `ml/` dan `app/`
- [ ] Test keamanan `is_simulatable` yang sudah ada tetap hijau
- [ ] Tidak ada string exception mentah di response body
- [ ] Latensi end-to-end (AI + PBPK + fusi) **< 5 detik** p95 — sesuai PRD UC-02

---

## C11 — Unit Test Endpoint Inferensi AI

**DoD resmi:** *Seluruh kasus uji lulus; endpoint stabil pada skenario normal maupun edge case.*

**Langkah:**

1. **Senyawa berlabel diketahui** (diminta eksplisit oleh C11):
   - **Parasetamol** — `vMost-DILI-concern`, pola Hepatoseluler → skor tinggi, segmen V–VIII
   - **Ibuprofen** — risiko lebih rendah → skor lebih rendah dari parasetamol
   > Uji **arah relatif** (parasetamol > ibuprofen), bukan angka absolut. Menguncikan nilai absolut membuat test rapuh terhadap retraining yang sah.

2. **Edge case wajib:**
   | Kasus | Ekspektasi |
   |---|---|
   | SMILES tidak valid (`"XYZ123"`) | Ditangani rapi, bukan 500 |
   | `hepatwin_id` tidak ada | 404 |
   | Senyawa `is_simulatable = FALSE` | Ditolak, tidak masuk pipeline AI |
   | SMILES multi-fragmen (garam) | Berhasil — fragmen terbesar diambil (perbaikan C2) |
   | Molekul tanpa ikatan | Tidak crash |
   | Artefak model tidak ada | 503, bukan skor palsu |
   | Molekul tanpa match SMARTS | SHAP list kosong, bukan crash |

3. **Uji reproduktibilitas** (PRD menuntut keluaran 100% konsisten): panggil endpoint dua kali dengan input identik → `dili_score` dan vektor SHAP **identik**.

4. **Uji konsistensi training↔inferensi:** ambil beberapa senyawa dari test set C5, bandingkan skor lewat endpoint vs lewat pipeline `ml/` langsung → harus sama (dalam toleransi floating point). Ini menangkap ketidakcocokan featurization yang paling sulit dideteksi.

**Acceptance criteria:**
- [ ] Seluruh kasus di tabel edge case punya test dan lulus
- [ ] Test reproduktibilitas lulus
- [ ] Test konsistensi training↔inferensi lulus
- [ ] Test lama di `tests/` (milik `master`) tetap hijau — tidak ada regresi
- [ ] `pytest` seluruh repo hijau

---

## C12 — Dokumentasi Arsitektur & Keputusan Desain Model

**DoD resmi:** *Dokumen arsitektur dan keputusan desain siap dipresentasikan serta diaudit oleh juri teknis.*

**Langkah:**

1. Tulis `ml/reports/C12_dokumentasi_model.md`, merangkum C1–C11:
   - Arsitektur final + justifikasi (rujuk C4)
   - Hyperparameter + **asal-usulnya** (nested CV di `upscale`, bukan tebakan)
   - Sumber & konstruksi dataset (rujuk C2, C5) — **dua angka korpus dibedakan jelas**
   - Hasil evaluasi + perbandingan baseline (rujuk C7)
   - Metode explainability + keterbatasannya (rujuk C8)
   - Kebijakan model statis (rujuk C9)

2. Tulis `ml/reports/C12_limitations.md` — **wajib memuat minimal:**
   - Ukuran dataset kecil (≈870 senyawa) untuk model deep learning; risiko overfitting tidak sepenuhnya hilang
   - Label DILIrank berasal dari teks label FDA + kausalitas literatur, **bukan** pengukuran laboratorium langsung
   - `Ambiguous-DILI-concern` (336 senyawa) dibuang dari training — model tidak pernah belajar dari kategori ini, tapi senyawanya **tetap bisa dipilih** pengguna di autocomplete. Konsekuensinya: untuk senyawa Ambiguous, prediksi model adalah ekstrapolasi murni. **Ini harus dinyatakan eksplisit**, bukan diabaikan.
   - Zona kerusakan adalah **lookup LiverTox deterministik, bukan prediksi model** (`PROJECT_FIX_MODEL.md` §4.1). 824 dari 1.231 senyawa tidak punya monograf LiverTox → jatuh ke *fallback* diffuse.
   - Pemetaan pola cedera → segmen Couinaud adalah **penyederhanaan pedagogis makroskopis** (zona histologis bersifat mikroskopis) — PRD sendiri mewajibkan disclaimer ini
   - Bentuk garam direduksi ke fragmen terbesar; komponen lain (mis. klavulanat pada amoksisilin-klavulanat) tidak ikut direpresentasikan
   - Status gerbang G1–G6: mana yang sudah diratifikasi, mana yang masih `[PENDING REVIEW]`
   - Metode atribusi atom yang dipakai dan mengapa (bila bukan Shapley murni, nyatakan)

3. Siapkan ringkasan siap-presentasi untuk Jury Challenge: 1 halaman berisi arsitektur, angka kunci, dan **jawaban jujur** untuk pertanyaan yang mungkin muncul ("kenapa GNN kalau baseline setara?", "kenapa AUC bukan 0,9?", "dari mana zona berasal?").

**Acceptance criteria:**
- [ ] Setiap angka dapat ditelusuri ke artefak di `ml/reports/`
- [ ] Tidak ada angka target/proyeksi yang ditulis seolah-olah hasil aktual
- [ ] `C12_limitations.md` memuat seluruh butir di atas
- [ ] Dokumen bisa dibaca berdiri sendiri oleh juri tanpa membaca kode

---

## Ringkasan Gerbang Manusia

| ID | Pertanyaan | Ke siapa | Memblokir | Default sementara |
|---|---|---|---|---|
| **G1** | Korpus training 870 berlabel vs klaim 1.231 | Ketua Tim | C5 (tidak memblokir eksekusi) | Laporkan dua angka terpisah |
| **G2** | 2 InChIKey berlabel bertentangan | Farmasi | C5 (tidak memblokir) | Label positif menang |
| **G3** | Model imputasi `injury_pattern`? | Ketua Tim + Farmasi | Tidak memblokir | **Tidak** — di luar C1–C12 |
| **G4** | Nama & interpretasi 9 pola SMARTS | Farmasi | C8 (tidak memblokir) | Pakai daftar `upscale`, tandai pending |
| **G5** | Ambang `risk_level` untuk warna 3D | Farmasi | Tidak memblokir | Ambang yang sudah ada |
| **G6** | Skema kontrak API SHAP per-atom | Ketua Tim + Faris | C10 | Usulan di C10 langkah 3 |
| **G7** | Kontradiksi skor↔zona (24 senyawa aman bertanda zona, 86 berisiko tanpa zona) | Ketua Tim + Faris | Tidak memblokir (Alur F) | Pertahankan perilaku `master` |

Seluruh gerbang punya default sehingga **tidak ada task yang benar-benar terhenti** — tapi setiap keluaran yang bergantung pada default wajib ditandai `[KEPUTUSAN AI — PENDING REVIEW]` di kode dan laporan.

---

## Definition of Done — Branch `fix-model`

- [ ] Branch `fix-model` ada, bercabang dari `master`, `master` tidak berubah
- [ ] C0–C12 selesai, masing-masing satu commit
- [ ] Nol panggilan PubChem/API eksternal di pipeline data
- [ ] `model_gatnn_dnn.pt` terlatih dengan hyperparameter tervalidasi, bukan bobot acak
- [ ] Kalibrator terpasang, ECE membaik setelah kalibrasi
- [ ] SHAP tingkat gugus **dan** atom berfungsi, latensi < 2 detik
- [ ] `ai_engine.py` diganti, tidak ada `return 0.5` diam-diam
- [ ] Latensi end-to-end < 5 detik (PRD UC-02)
- [ ] Seluruh `pytest` hijau, termasuk test lama `master`
- [ ] Dokumentasi C4, C7, C8, C9, C12 lengkap
- [ ] `C12_limitations.md` memuat seluruh keterbatasan, termasuk yang tidak menguntungkan
- [ ] `.env` tidak pernah masuk ke riwayat git
