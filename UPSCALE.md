# UPSCALE.md — Spesifikasi Perubahan Machine Learning (Mesin B)

**Proyek:** HepaTwin — GEMASTIK 2026
**Repo:** `hepatwin-backend-py` (repo yang sudah ada — tidak membuat repo baru)
**Branch target:** `upscale`, dibuat dari `master`. Branch `master` tidak disentuh sampai ada keputusan eksplisit untuk merge.
**Cakupan dokumen:** Mesin B (AI/ML) saja.
**Versi:** 2.0 — perubahan arah mengikuti keputusan ketua tim (lihat §0.1)
**Status:** Draft untuk direview ketua tim + anggota Farmasi

---

## 0. Ringkasan Eksekutif

### 0.1 Perubahan arah dari v1.0

Dokumen ini **tidak lagi terikat pada `HepaTwin_PRD.md`**. PRD tersebut ditulis untuk skema klaim yang lebih konservatif (skema dua-tahap InterDILI, external test Xu et al., dedup lintas-studi). Upscale ini adalah inovasi lanjutan yang mengikuti arah teknis di **`Pengembangan Digital Twin Liver.docx`** dan arahan langsung ketua tim. Dua perubahan inti dari v1.0:

1. **Tidak ada external test dari studi independen.** Dikonfirmasi konsisten dengan arsitektur rujukan (§1).
2. **Skema dataset gabungan = DILIrank 2.0 + LiverTox.** FAERS dan Tox21 tetap dipertimbangkan, tapi dengan peran yang berbeda dari "baris tambahan di tabel yang sama" (§3.4).

Bagian PRD lama yang masih relevan (disclaimer produk, batas scope Mode Triase, dsb.) tetap berlaku sebagai referensi produk — hanya bagian metodologi ML yang digantikan dokumen ini.

### 0.2 Ringkasan teknis

1. **Arsitektur GATNN-DNN** mengikuti Wibowo, Chong, & Tayara (2025), *Toxicology* 514:154108.
2. **Dua cabang eksperimen dataset**:
   - **Arm A** — DILIrank 2.0 saja
   - **Arm B** — DILIrank 2.0 + LiverTox (skema gabungan yang **sama silsilahnya** dengan dataset yang direproduksi Wibowo et al.)
3. **Validasi internal (split/CV), tanpa external test lintas-studi** — mengikuti praktik nyata Wibowo et al., bukan skema InterDILI/PRD lama.
4. **Kalibrasi probabilitas** — tetap wajib, karena skor menggerakkan visual 3D.

---

## 1. Dasar Metodologis: Bagaimana Wibowo et al. (2025) Sebenarnya Divalidasi

Ini bagian paling penting di revisi ini, karena ini yang mengesahkan keputusan "tanpa external test".

### 1.1 Silsilah dataset

Wibowo et al. (2025) tidak membangun dataset baru. Pernyataan langsung dari paper: <cite index="53-1">"Kami mengusulkan model yang dimodifikasi menggunakan dataset yang reliable dari studi sebelumnya. Kami mereproduksi model terbaik sebelumnya dan menggabungkannya dengan graph attention neural network."</cite>

"Studi sebelumnya" yang dimaksud adalah Yang, Zhang, & Li (2024), *Toxicology* 502:153736, yang membangun <cite index="56-1">dataset berkualitas tinggi berisi 1.573 senyawa</cite>, dengan sumber: <cite index="56-1">Liver Toxicity Knowledge Base (LTKB) milik NCTR/FDA, serta LiverTox yang dibangun NIDDK — baik DILIrank maupun DILIst sama-sama diturunkan dari LTKB.</cite>

**Konsekuensi:** rantai rujukan model kalian sendiri (Wibowo → Yang) sudah memakai skema gabungan **DILIrank + LiverTox**. Ini bukan ide baru yang perlu dipertanyakan validitasnya — ini persis basis dataset dari arsitektur yang kalian pilih.

### 1.2 Skema evaluasi

Karena Wibowo mereproduksi dataset Yang secara utuh (bukan mengambil dataset independen baru untuk diuji silang), performa yang dilaporkan — <cite index="24-1">presisi 75,14%, sensitivitas 85,2%, MCC 0,399, AUC 0,757, F1 82,5%</cite> — adalah hasil **evaluasi internal** pada dataset gabungan itu sendiri (split atau cross-validation), **bukan** pengujian pada dataset yang dikurasi kelompok riset lain.

Ini konsisten dengan keputusan ketua tim: **tidak memakai external test.** HepaTwin mengikuti pola yang sama.

**Yang tetap wajib secara metodologi (ini bukan "external test", ini kebersihan ML dasar):**
- Data yang dipakai untuk melatih tidak boleh menjadi data yang dipakai untuk mengukur performa akhir
- Karena itu: **held-out split / k-fold CV di dalam dataset gabungan itu sendiri** tetap dilakukan — persis seperti yang Yang & Wibowo lakukan. Ini bukan dataset kedua dari luar; ini partisi dari dataset yang sama.

### 1.3 Apa yang berubah dari v1.0

| | v1.0 (terikat PRD) | v2.0 (mengikuti Wibowo, keputusan ketua tim) |
|---|---|---|
| Validasi eksternal | Xu et al. (2015), lintas-studi | **Tidak ada** — split/CV internal |
| Arm B | DILIst atau ablasi label | **DILIrank 2.0 + LiverTox** |
| Precedent | InterDILI (skema 4-dataset) | **Yang et al. (2024) / Wibowo et al. (2025)** — silsilah langsung model kalian |
| Status Xu/Greene/Liew | Kandidat Arm B | **Tetap tidak dipakai** (keputusan ketua tim sebelumnya, tidak berubah) |

---

## 2. Keputusan Tim yang Mengikat

| # | Keputusan | Sumber | Konsekuensi |
|---|---|---|---|
| K1 | Arsitektur = **GATNN**, mengacu Wibowo et al. (2025) | Ketua tim | `GCNConv` di `app/services/ai_engine.py` (versi `master`) diganti `GATConv`/`GATv2Conv` di branch `upscale` |
| K2 | Xu et al., Greene et al., Liew et al. **tidak dipakai** | Ketua tim | Tidak berubah dari v1.0 |
| K3 | **Tanpa external test** dari studi independen | Ketua tim, dikonfirmasi §1 | Validasi = split/CV internal pada dataset gabungan |
| K4 | Arm B = **DILIrank 2.0 + FAERS + Tox21 + LiverTox** | Ketua tim | Diimplementasikan bertingkat — lihat §3.4 untuk pembagian peran tiap sumber |
| K5 | Nama/pemetaan SMARTS wajib divalidasi Farmasi | Konsisten sejak v1.0 | Blocker untuk rilis explainability |
| K6 | Angka performa aktual dilaporkan apa adanya | Konsisten sejak v1.0 | Tidak ada cherry-picking |

---

## 3. Spesifikasi Dataset

### 3.1 DILIrank 2.0 (basis, tidak berubah dari v1.0)

| Kelas | Jumlah |
|---|---|
| vMost-DILI-concern | 217 |
| vLess-DILI-concern | 351 |
| vNo-DILI-concern | 414 |
| Ambiguous-DILI-concern | 354 |
| **Total** | **1.336** |

Kolom asli: `LTKBID, CompoundName, SeverityClass, LabelSection, vDILI-Concern, Comment`. Tidak ada SMILES — resolusi PubChem tetap prasyarat (TU.2, tidak berubah).

### 3.2 Arm A — DILIrank 2.0 saja (baseline)

Sama seperti v1.0: `vMost + vLess = 1`, `vNo = 0`, `Ambiguous` dibuang. ⚠️ Skema vLess tetap menunggu konfirmasi Farmasi (B2) — lihat §7.

### 3.3 Arm B — DILIrank 2.0 + LiverTox (FINAL, mengikuti silsilah Wibowo)

**Sumber data:** NIH/NIDDK **Master List of LiverTox Drugs** — <cite index="68-1">spreadsheet Excel resmi berisi seluruh obat di LiverTox dengan metadata termasuk Likelihood Score, diperbarui tahunan, tidak berhak cipta, dapat dipakai bebas untuk analisis data maupun publikasi</cite>. Ini bukan scraping monograf — file terstruktur, jauh lebih murah dari perkiraan v1.0.

**Skema skor:** <cite index="67-1">skala 5 poin: A = well known cause, B = highly likely cause, C = probable cause, D = possible cause, E = unlikely cause, E* = suspected but unproven, X = unknown</cite>.

**Skema binerisasi — mengikuti presedan literatur yang sudah memakai kombinasi persis ini:**

<cite index="59-1">Studi yang menggabungkan DILIrank dan LiverTox untuk training memperlakukan skor "A" atau "B" sebagai DILI-positif, dan skor "E" atau "E*" sebagai DILI-negatif</cite>, sementara C, D, dan X dibuang (analog dengan Ambiguous di DILIrank).

| Skor LiverTox | `label_binary` |
|---|---|
| A, B | 1 |
| C, D, X | dibuang |
| E, E* | 0 |

**Konstruksi Arm B:**
1. Resolusi nama obat LiverTox → SMILES (pakai ulang cache PubChem dari TU.2)
2. Standardisasi RDKit + InChIKey (pakai ulang pipeline TU.2)
3. Gabung dengan DILIrank 2.0 via `inchikey`
4. **Aturan konflik label** (senyawa yang ada di kedua sumber dengan label berbeda): DILIrank menang, karena lebih baru dan lebih ketat kurasinya (label FDA + verifikasi kausalitas vs. hitungan laporan kasus). Aturan ini konsisten dengan praktik umum di literatur DILI-ML.
5. **Simpan `source_dataset` per baris** — wajib bisa diaudit mana yang dari DILIrank, mana yang dari LiverTox, mana yang muncul di keduanya.

**Perkiraan ukuran:** presedan Yang et al. mencapai 1.573 senyawa dari kombinasi serupa (berbasis DILIrank 1.0). Dengan DILIrank 2.0 (lebih besar) sebagai basis, realistis Arm B berukuran **± 1.600–1.900 senyawa** sebelum penyaringan resolusi SMILES — angka pasti adalah output TU.12, bukan asumsi.

### 3.4 FAERS dan Tox21 — peran bertingkat, bukan baris tambahan

Ketua tim ingin ketiganya (FAERS, Tox21, LiverTox) digabung. LiverTox sudah terjawab di §3.3 — itu jalan lurus karena unit datanya sama (per-obat, berlabel hepatotoksisitas). **FAERS dan Tox21 unit datanya berbeda secara struktural**, dan literatur menunjukkan integrasinya memang mungkin — tapi lewat cara yang berbeda dari "tambah baris di tabel yang sama".

**Bukti bahwa ini pernah dilakukan orang lain, sebagai referensi jujur:** <cite index="51-1">satu studi (TGFS-Net, 2026) mengintegrasikan data multimodal dari FAERS, Open TG-GATEs, dan Tox21 lewat Transformer encoder untuk SMILES yang dilatih bersamaan dengan graph neural network beratensi substruktur terpisah</cite> — dua encoder paralel yang disatukan, bukan GATNN-DNN sederhana seperti Wibowo.

**Keputusan untuk HepaTwin:**

| Sumber | Peran di Mesin B | Fase |
|---|---|---|
| **LiverTox** | Baris tambahan di training set, digabung langsung dengan DILIrank (§3.3) | **Wajib, Arm B utama** |
| **Tox21** | Multi-task auxiliary head opsional — model dilatih juga memprediksi 12 label assay Tox21 sebagai tugas tambahan, dengan harapan representasi graf yang dipelajari jadi lebih kaya (transfer learning ringan) | **Stretch goal, TU.16, tidak memblokir Arm B** |
| **FAERS** | Fitur skor tambahan per senyawa (reporting odds ratio hepatotoksisitas), dilekatkan ke vektor DNN sebagai 1 kolom ekstra, dihitung lewat analisis disproporsionalitas sederhana | **Stretch goal, TU.17, tidak memblokir Arm B** |

Alasan keduanya distretch, bukan diblok total maupun dipaksa masuk Arm B inti: Tox21 mayoritas isinya bahan kimia industri (bukan obat) dan labelnya assay biologis, bukan DILI — memasukkannya sebagai baris berlabel DILI akan mencemari target. FAERS tidak punya label per-obat sama sekali; label harus **diturunkan** lewat pemodelan statistik tersendiri sebelum bisa dipakai, dan itu pekerjaan terpisah dari pipeline dataset.

Ini tetap "menggunakan" ketiga sumber sesuai arahan ketua tim — hanya dengan peran yang jujur sesuai bentuk datanya masing-masing, bukan dipaksa jadi bentuk yang sama.

---

## 4. Skema Evaluasi (Revisi — Tanpa External Test)

### 4.1 Prinsip

Dua tingkat evaluasi, keduanya **internal** terhadap dataset gabungan (Arm A atau Arm B), mengikuti pola Wibowo/Yang:

| Tingkat | Split | Fungsi |
|---|---|---|
| L1 | 5-fold CV, random split | Pembanding langsung terhadap angka Wibowo (0,757) — kondisi paling sebanding |
| L2 | 5-fold CV, **scaffold split** (Bemis–Murcko) | Ukuran generalisasi ke kerangka kimia baru — Wibowo tidak melaporkan ini, jadi ini **nilai tambah** HepaTwin dibanding paper rujukannya |

~~L3 — temporal hold-out~~ **dihapus dari wajib.** Alasan penghapusan: skema ini dirancang v1.0 untuk menggantikan external test yang disyaratkan PRD lama; karena K3 menghapus syarat itu sepenuhnya, temporal split jadi opsional, bukan wajib. Boleh tetap dijalankan sebagai tambahan informatif (§4.3), tapi tidak masuk kriteria selesai.

### 4.2 Metrik wajib

Sama seperti v1.0: `AUC-ROC, AUC-PR, Accuracy, Sensitivity, Specificity, Precision, F1, MCC, Brier score, ECE`, dilaporkan mean ± std lintas 5 seed.

### 4.3 Temporal split — opsional, bukan gerbang

Bila waktu memungkinkan, jalankan juga split berbasis tahun persetujuan (obat baru 2010–2021 sebagai hold-out) sebagai **analisis tambahan**, bukan syarat kelulusan. Ini nilai plus presentasi ("kami juga menguji generalisasi temporal, di luar apa yang dilaporkan paper rujukan"), tapi kegagalan di sini tidak menggagalkan proyek.

### 4.4 Baseline pembanding (tidak berubah)

Random Forest (ECFP4) dan MLP (MACCS + deskriptor), dilatih pada split yang sama, dilaporkan di tabel yang sama.

---

## 5. Spesifikasi Model: GATNN-DNN (tidak berubah dari v1.0)

Referensi: Wibowo, Chong, & Tayara (2025), *Toxicology* 514:154108. Kode publik: `github.com/asw1982/GATNN_DNN_DILI_Toxicity`.

Performa rujukan: <cite index="24-1">presisi 75,14%, sensitivitas 85,2%, MCC 0,399, AUC 0,757, F1 82,5%</cite> — dicapai pada evaluasi internal dataset 1.573 senyawa (§1.2), **bukan** pada external test.

### 5.1 Arsitektur dua cabang

```
                SMILES
                   |
        +----------+----------+
        |                     |
   [Cabang Graf]        [Cabang DNN]
   mol → graf           fingerprint vector
        |                     |
   GATConv(34→64, heads=4)   Linear(1200→512) + ReLU + Dropout(0.3)
   ELU + Dropout(0.2)        Linear(512→128)  + ReLU + Dropout(0.3)
   GATConv(256→64, heads=4)         |
   ELU                              |
   global_mean_pool → 256           |
        |                           |
        +------------+--------------+
                     |
              concat → 384
                     |
           Linear(384→128) + ReLU + Dropout(0.3)
           Linear(128→1)
                     |
              logit (BUKAN sigmoid)
```

🔴 **Model mengembalikan logit, bukan probabilitas.** `BCEWithLogitsLoss`. Sigmoid hanya di lapisan inferensi, setelah kalibrasi. Versi `master` saat ini menaruh `nn.Sigmoid()` di dalam `forward()` — dihapus di branch `upscale`.

### 5.2 Node features (34 dim) — tidak berubah

Atomic number one-hot (10), degree one-hot (6), formal charge one-hot (5), total H one-hot (5), hybridization one-hot (6), aromatic (1), in-ring (1).

### 5.3 Edge features (6 dim) — tidak berubah

Bond type one-hot (4), conjugated (1), in-ring (1). `GATv2Conv(edge_dim=6)`.

### 5.4 Cabang DNN (± 1.200 dim) — tidak berubah

MACCS (167) + ECFP4 folded (1024) + blok SMARTS (9–15, indeks terakhir, `SMARTS_SLICE`).

### 5.5 Hyperparameter awal — tidak berubah

```yaml
optimizer: AdamW
lr: 1e-3
weight_decay: 1e-4
batch_size: 32
max_epochs: 300
early_stopping: patience=30, monitor=val_auc, mode=max
scheduler: ReduceLROnPlateau(factor=0.5, patience=10)
loss: BCEWithLogitsLoss(pos_weight=<dihitung dari train fold>)
seed: [42, 43, 44, 45, 46]
```

Catatan khusus Arm B: dataset lebih besar (± 1.600–1.900 vs ± 900 di Arm A) → overfitting sedikit lebih longgar, tapi dropout & early stopping tetap dipertahankan agresif karena masih jauh dari skala dataset deep learning pada umumnya.

---

## 6. Kalibrasi Probabilitas (tidak berubah — tetap wajib)

Keluaran menggerakkan intensitas visual 3D, bukan sekadar ranking. Isotonic regression (fallback Platt bila validation < 200 sampel). Brier score + ECE + reliability diagram wajib dilaporkan sebelum/sesudah, untuk **Arm A dan Arm B masing-masing**.

Pemetaan skor → visual sama seperti v1.0 (§6 versi sebelumnya), ambang tetap menunggu validasi Farmasi.

---

## 7. Explainability (tidak berubah dari v1.0)

Perbaikan batch SHAP pada `SMARTS_SLICE`, cache per InChIKey, fallback occlusion attribution bila latensi > 3 detik. Dua pola SMARTS bermasalah (nitro, fenol) tetap perlu diperbaiki. Daftar final tetap menunggu validasi Farmasi (B5).

---

## 8. Target Performa yang Jujur (revisi)

| Skema | Band wajar | Catatan |
|---|---|---|
| Arm A, L1 (random CV) | 0,70 – 0,80 | Dataset lebih kecil (± 900) dari dataset rujukan Wibowo (1.573) |
| Arm A, L2 (scaffold CV) | 0,62 – 0,72 | |
| **Arm B, L1 (random CV)** | **0,74 – 0,80** | Paling sebanding dengan angka Wibowo (0,757) karena ukuran & komposisi dataset mendekati |
| Arm B, L2 (scaffold CV) | 0,66 – 0,75 | |

Konteks pembanding:

| Model | AUC | Skema |
|---|---|---|
| GATNN-DNN (Wibowo et al., 2025) | 0,757 | evaluasi internal, dataset 1.573 (DILIrank+LiverTox) |
| DNN + ECFP6 (Yang et al., 2024) | 0,713 | dataset sama, model lebih sederhana |
| RF + Morgan FP (Ye et al.) | 0,75 | random split 70/30 |

**Ekspektasi utama:** Arm B seharusnya mendekati 0,757 karena kondisinya paling mirip dengan setup Wibowo (dataset gabungan sejenis, evaluasi internal). Bila Arm B jauh di bawah itu, kemungkinan ada masalah di resolusi SMILES atau harmonisasi label yang perlu diaudit — bukan otomatis dianggap kegagalan model.

🚩 Karena tidak ada lagi temporal/external hold-out sebagai pengaman, kewaspadaan leakage bergeser sepenuhnya ke **scaffold split (L2)** dan ke **kebersihan dedup InChIKey saat menggabung DILIrank+LiverTox**. Bila L1 tinggi tapi L2 jauh lebih rendah — itu sinyal overfitting terhadap kerangka kimia populer, wajib dilaporkan sebagai temuan, bukan disembunyikan.

---

## 9. Struktur Repo (revisi — branch, bukan repo baru)

**Perubahan arah:** pekerjaan ini **tidak** membuat repo terpisah. Ia berjalan di branch **`upscale`**, dibuat dari `master` milik `hepatwin-backend-py`. Konsekuensinya, struktur direktori harus **berdampingan** dengan `app/` yang sudah ada (FastAPI runtime), bukan menggantikannya atau berdiri sendiri di pohon direktori terpisah.

Prinsip pembagian:
- **`app/`** — tetap runtime FastAPI yang sudah ada. Diedit seperlunya (`ai_engine.py` ditulis ulang, `schemas.py` & `config.py` ditambah field), **tidak** dibongkar strukturnya.
- **`ml/`** — direktori baru, sejajar dengan `app/`, berisi seluruh pipeline riset: resolusi data, training, evaluasi, kalibrasi. Ini kode yang dijalankan manual/offline oleh AI/ML engineer, bukan bagian dari server yang di-deploy.
- Artefak akhir (`.pt` + kalibrator) hasil `ml/` **disalin** ke `app/models/` supaya `ai_engine.py` bisa memuatnya saat runtime — bukan dua tempat yang tidak saling terhubung.

```
hepatwin-backend-py/                    (branch: upscale)
├── app/                                 # RUNTIME — tidak dibongkar strukturnya
│   ├── main.py
│   ├── services/
│   │   ├── ai_engine.py                 # 🔴 DITULIS ULANG: GATNN-DNN, memuat artefak dari ml/
│   │   ├── pkpd_engine.py               # tidak disentuh — Mesin A, luar cakupan
│   │   └── simulation_orchestrator.py   # disesuaikan bila field response berubah (§10)
│   ├── api/                             # tidak berubah struktur
│   ├── models/
│   │   ├── schemas.py                   # field baru: model_version, model_status, dst.
│   │   └── model_arm_a.pt               # 🔴 BARU — hasil salin dari ml/models/, bukan lagi kosong
│   └── core/
│       └── config.py                    # field baru: MODEL_VERSION, CALIBRATOR_PATH
│
├── ml/                                   # 🔴 BARU — seluruh pipeline riset/training
│   ├── configs/
│   │   ├── base.yaml
│   │   ├── arm_a_dilirank.yaml
│   │   └── arm_b_merged.yaml
│   ├── data/
│   │   ├── raw/                          # .gitignore
│   │   ├── interim/                      # .gitignore
│   │   └── processed/                    # arm_a.parquet, arm_b.parquet — DI-COMMIT (kecil, penting untuk reproduksi)
│   ├── src/hepatwin_ml/
│   │   ├── data/
│   │   │   ├── resolve_smiles.py
│   │   │   ├── standardize.py
│   │   │   ├── harmonize_labels.py
│   │   │   ├── build_livertox.py         # unduh Master List, parse, binerisasi A/B vs E/E*
│   │   │   ├── build_dataset.py          # merge DILIrank+LiverTox via InChIKey
│   │   │   └── splits.py                 # random & scaffold wajib; temporal opsional
│   │   ├── features/
│   │   │   ├── graph.py
│   │   │   ├── fingerprints.py
│   │   │   └── smarts.py
│   │   ├── models/
│   │   │   ├── gatnn_dnn.py
│   │   │   └── baselines.py
│   │   ├── stretch/                      # TU.16, TU.17 — tidak memblokir apa pun
│   │   │   ├── tox21_multitask.py
│   │   │   └── faers_signal.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   ├── calibrate.py
│   │   └── explain.py
│   ├── scripts/
│   │   ├── run_arm_a.sh
│   │   ├── run_arm_b.sh
│   │   ├── compare_arms.py
│   │   └── export_to_app.py              # 🔴 BARU — salin artefak terpilih ml/models/*.pt → app/models/
│   ├── reports/                          # DI-COMMIT — bukti kerja & metrik
│   └── models/                           # .gitignore, kecuali yang di-export
│
├── data_preparation/
│   └── deduplicate_smiles.py             # OBSOLETE — logikanya digantikan ml/src/.../build_dataset.py.
│                                          # Dibiarkan ada dengan komentar penanda obsolete, tidak dihapus,
│                                          # supaya histori kenapa desainnya berubah tetap terlacak.
│
├── UPSCALE.md
├── EXECUTION_PLAN_UPSCALE.md
└── requirements.txt                       # digabung: dependency app/ + dependency ml/
```

### 9.1 Alur kerja Git

```
master ──●───────────────────────────────────── (tidak disentuh)
          \
           ●──●──●── ... ──●  branch: upscale
           TU.0            TU.15
```

- Branch `upscale` dibuat dari `master` di TU.0.
- Seluruh task TU.0–TU.17 dikerjakan sebagai commit di branch `upscale`, **bukan** langsung ke `master`.
- **Merge ke `master` bukan bagian dari execution plan ini.** Itu keputusan terpisah ketua tim setelah Definition of Done (§11) terpenuhi dan direview.
- Bila selama pengerjaan branch `master` mendapat perubahan lain (mis. dari anggota frontend), rebase/merge `master` ke `upscale` boleh dilakukan, tapi **tidak sebaliknya**.

Config Arm B tidak lagi stub:

```yaml
# configs/arm_b_merged.yaml
arm_name: "arm_b_dilirank_livertox"
datasets:
  - name: dilirank2
    path: data/raw/dilirank2.csv
    label_map: dilirank_4class_to_binary
  - name: livertox
    path: data/raw/livertox_master_list.xlsx
    label_map: livertox_AB_vs_EEstar
label_conflict_policy: dilirank_wins
split:
  internal: [random_5fold, scaffold_5fold]
  external: none
```

---

## 10. Kontrak API (tidak berubah dari v1.0)

Field `model_version`, `model_status`, `score_is_calibrated` tetap wajib. `external_auc` **diganti** menjadi `internal_cv_auc` (nama field mengikuti realita: tidak ada lagi external test).

🔴 Larangan silent fallback (`return 0.5`) tetap berlaku — ini isu integritas terpisah dari isu external test, tidak berubah oleh revisi ini.

---

## 11. Definition of Done (revisi)

**Status per 2026-07-31 (branch `upscale`, commit terakhir TU.14/TU.15).**

- [x] Branch `upscale` ada, dibuat dari `master`, `master` tidak berubah (`git diff master upscale -- app/` kosong sampai TU.14)
- [x] `ml/data/processed/arm_a.parquet` — DILIrank 2.0 saja (839 senyawa)
- [x] `ml/data/processed/arm_b.parquet` — DILIrank 2.0 + LiverTox, `source_dataset` per baris, tingkat konflik label terhitung (1253 senyawa, konflik 18,6%, teraudit)
- [x] Master List LiverTox terunduh, skema A/B-vs-E/E* diterapkan sesuai §3.3
- [x] `ml/src/hepatwin_ml/models/gatnn_dnn.py` memakai GATv2Conv, mengembalikan logit
- [x] `ml/models/model_arm_a.pt` ada dan bukan bobot acak — [ ] `model_arm_b.pt` **sengaja tidak diekspor sebagai artefak produksi**: TU.13 menemukan Arm B signifikan lebih buruk dari Arm A (p<0,0001, `07_comparison.md`), dikonfirmasi user untuk TIDAK dipakai produksi. Arm B tetap terevaluasi penuh (5 seed × L1/L2) untuk transparansi, hanya tidak diekspor sebagai model final.
- [x] Kalibrator tersimpan untuk Arm A, ECE & Brier dilaporkan (`10_calibration.md`) — kalibrator Arm B tidak dibuat (konsisten dengan keputusan di atas)
- [x] `ml/reports/07_comparison.md` — Arm A vs Arm B × L1/L2 × 5 seed (mean ± std)
- [x] Baseline RF & MLP di tabel yang sama
- [x] `ml/scripts/export_to_app.py` dijalankan — artefak model & kalibrator Arm A tersalin ke `app/models/`
- [x] `app/services/ai_engine.py` memuat artefak dari `app/models/` dan menjalankan inferensi dengan model asli (bukan bobot acak)
- [x] Endpoint balas 503 saat model tidak ada (diverifikasi manual + test otomatis `tests/test_simulation_api.py`)
- [x] Latensi Mode Triase < 5 detik (diverifikasi: p95 = 0,98 detik)
- [ ] Daftar SMARTS ditandatangani Farmasi — **belum**, status `[KEPUTUSAN AI — PENDING REVIEW FARMASI]` di seluruh laporan terkait (gerbang B5, EXECUTION_PLAN_UPSCALE.md §14.1)
- [x] `ml/reports/limitations.md` memuat: dataset kecil, tidak ada external test dan alasannya (mengikuti Wibowo), Tox21/FAERS sebagai stretch belum dikerjakan (batasan waktu, bukan disembunyikan)

**Belum selesai (di luar cakupan siklus kerja ini, dicatat jujur bukan disembunyikan):**
- Validasi Farmasi untuk gerbang B2/B3/B4/B5 (lihat EXECUTION_PLAN_UPSCALE.md §14.1) — prasyarat sebelum rilis produksi sungguhan
- TU.16 (Tox21 multi-task) dan TU.17 (FAERS signal) — stretch goal, tidak dikerjakan, tidak memblokir DoD di atas

---

## 12. Di Luar Cakupan

- Prediksi pola zonal untuk Mode Triase Umum
- Model DDI/sinergi polifarmasi (Fase 2)
- PBPK multi-kompartemen, PopPK, Monte Carlo farmakogenomik
- Segmentasi nnU-Net, LiTS, 3DIRCADb
- Arsitektur di luar GATNN-DNN
- Mengubah Mesin A (PK/PD parasetamol)
- Tox21 multi-task dan FAERS signal (§3.4) **melebihi** implementasi stretch dasar — tidak ada eksplorasi arsitektur dua-encoder ala TGFS-Net dalam skala kompetisi ini

---

## 13. Referensi

- Chen, M., Suzuki, A., Thakkar, S., Yu, K., Hu, C., & Tong, W. (2016). DILIrank: the largest reference drug list ranked by the risk for developing drug-induced liver injury in humans. *Drug Discovery Today, 21*(4), 648–653.
- FDA LTKB. *Drug Induced Liver Injury Rank (DILIrank 2.0) Dataset.*
- NIDDK/NLM. *LiverTox: Clinical and Research Information on Drug-Induced Liver Injury* — Master List of LiverTox Drugs (spreadsheet resmi, diperbarui tahunan).
- Yang, Q., Zhang, S., & Li, Y. (2024). Deep learning algorithm based on molecular fingerprint for prediction of drug-induced liver injury. *Toxicology, 502*, 153736.
- Wibowo, A.S., Chong, K.T., & Tayara, H. (2025). Enhancing DILI toxicity prediction through integrated graph attention (GATNN) and dense neural networks (DNN). *Toxicology, 514*, 154108.
- Predictive Model for DILI Using DNN Based on Substructure Space (2021) — presedan binerisasi LiverTox A/B vs E/E*. *Molecules, 26*(24), 7548.
