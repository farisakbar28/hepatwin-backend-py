# C12_dokumentasi_model.md — Dokumentasi Arsitektur & Keputusan Desain Model

Dokumen ini merangkum C1–C11 (branch `fix-model`, Alur Kerja C — Backend AI
GATNN-DNN & Explainability SHAP). Ditulis untuk bisa dibaca berdiri sendiri
oleh juri teknis tanpa perlu membaca kode. Setiap angka di bawah dapat
ditelusuri ke artefak `ml/reports/` yang disebutkan.

## 1. Arsitektur final + justifikasi

Rincian lengkap: `ml/reports/C4_arsitektur.md`.

Model hybrid dua-cabang: **cabang graf** (`GATv2Conv` ×2, `heads=4`,
`edge_dim=6`, ELU, `global_mean_pool` → 256-dim) + **cabang DNN** (fingerprint
MACCS+ECFP4+SMARTS 1200-dim → `Linear(1200→512→128)` → 128-dim) →
`concat` (384-dim) → `Linear(384→128→1)` → **logit**.

Perbedaan kunci dari versi `master` lama (`app/services/ai_engine.py`
sebelum C10): `GATv2Conv` (bukan `GCNConv` — punya mekanisme atensi),
34-dim node feature penuh (bukan 4 nilai di-pad nol jadi 9), keluaran logit
murni (bukan `Sigmoid()` di dalam `forward()`, yang menghalangi kalibrasi).

## 2. Hyperparameter + asal-usul

`lr=0.0005, hidden=64, dropout=0.2` — **tidak dicari ulang** di `fix-model`,
dipakai langsung dari nested cross-validation 10-fold di branch `upscale`
(`ml/reports/_upscale_archive/22_final_holdout_eval.json`). Detail proses
pencarian ada di arsip tersebut, bukan di `fix-model` — `fix-model` murni
memakai ulang hasilnya (`ml/reports/C4_arsitektur.md` §4).

Optimizer `AdamW(weight_decay=1e-4)`, `BCEWithLogitsLoss(pos_weight` dari
train fold saja`)`, `ReduceLROnPlateau(factor=0.5, patience=10)`, early
stopping `patience=30` monitor `val_auc`, `batch_size=32`, `max_epochs=300`.

## 3. Sumber & konstruksi dataset

Rincian lengkap: `ml/reports/C2_featurization.md`, `ml/reports/C5_split.md`.

**🔴 Dua angka korpus berbeda arti — tidak boleh disamakan (Gerbang G1):**

| Angka | Arti |
|---|---|
| **1.231** | Lingkup senyawa `is_simulatable = TRUE` di Supabase — dipakai featurisasi (C2) dan inferensi runtime. Semua senyawa ini bisa dipilih pengguna di autocomplete. |
| **870** | Korpus BERLABEL yang benar-benar dipakai training (C5) — setelah buang `Ambiguous-DILI-concern` (336 senyawa) dan dedup InChIKey (25 tabrakan garam↔basa, 2 di antaranya label bertentangan). |

Sumber data: **100% dari Supabase** (`hepatwin_compounds`), nol panggilan
PubChem/API eksternal di seluruh pipeline `ml/` — diverifikasi C2. Label DILI
dari `dili_concern` (identik FDA DILIrank 2.0). Pola cedera dari
`injury_pattern` (identik LiverTox) — **bukan** hasil model, lihat §6.

Split: hold-out test **scaffold-disjoint** 20% (174 senyawa, dikunci sejak
C5, dibuka sekali di C7), train/val scaffold-kfold dari sisanya (train=580,
val=116). Overlap InChIKey & scaffold antar-subset = 0 di semua pasangan,
diverifikasi via eksekusi (`ml/tests/test_run_split.py`).

## 4. Hasil evaluasi + perbandingan baseline

Rincian lengkap: `ml/reports/C7_evaluasi.md`.

| Model | AUC-ROC (test, n=174) | MCC |
|---|---|---|
| Random Forest | **0.7555** | 0.4134 |
| LightGBM | 0.7551 | 0.3250 |
| GATNN-DNN | 0.7252 | 0.0000* |
| XGBoost | 0.7213 | 0.3032 |
| Logistic Regression | 0.7125 | 0.2888 |

**GATNN-DNN TIDAK mengungguli Random Forest/LightGBM pada test set ini** —
dilaporkan apa adanya, tidak ada tuning tambahan setelah test set dibuka
(Aturan Main #2: kegagalan adalah keluaran yang sah). Seluruh AUC dalam
rentang wajar 0.63–0.75 untuk DILI pada dataset seukuran ini — tidak ada
indikasi kebocoran data (ambang audit >0.90 tidak terlampaui, diverifikasi
lewat assert otomatis, bukan dibaca manual).

*MCC=0 untuk GATNN-DNN pada threshold 0.5 adalah gejala kalibrator Platt
yang degenerate — lihat §6.

Kalibrasi: Platt scaling (VAL 116 sampel, <200 → otomatis bukan isotonic).
ECE membaik (0.1067→0.1015) tapi Brier memburuk sedikit (0.2003→0.2109) —
keduanya dilaporkan, bukan hanya yang membaik.

## 5. Metode explainability + keterbatasan

Rincian lengkap: `ml/reports/C8_shap.md`.

Dua tingkat atribusi:
- **Gugus (SMARTS, 9 pola):** nilai Shapley EKSAK (2^9=512 koalisi) — bukan
  approksimasi.
- **Atom (baru):** occlusion/masking per-atom, di-batch satu forward pass.
  🔴 Field `method="masking_attribution"`, **bukan** "SHAP" — bukan nilai
  Shapley sebenarnya (tidak menangkap interaksi antar-atom).

Latensi: p95=1376ms pada 50 molekul acak (ambang C8: <2000ms) → LULUS.
Uji kimiawi: parasetamol → gugus amida terdeteksi (sesuai mekanisme NAPQI);
ibuprofen → kontribusi gugus jauh lebih kecil (konsisten risiko lebih rendah).

## 6. Kebijakan model statis

Rincian lengkap: `ml/reports/C9_kebijakan_model_statis.md`.

Model dilatih offline (C6), dibekukan sebagai snapshot statis di
`app/models/`. Tidak ada continuous learning/auto-retraining di runtime —
diverifikasi lewat pencarian AST di seluruh `app/` (nol `.backward()`/
`optimizer.step()`/`torch.save()`, `tests/unit/test_static_model_policy.py`).

## 7. Status gerbang keputusan manusia (G1–G7)

| Gerbang | Status | Keterangan |
|---|---|---|
| G1 (870 vs 1231) | 🔴 PENDING REVIEW Ketua Tim | Default: dua angka dilaporkan terpisah (§3) |
| G2 (2 InChIKey label bertentangan) | 🔴 PENDING REVIEW Farmasi | Default: label positif menang (konservatif). Daftar di `C5_split.md` |
| G3 (imputasi `injury_pattern`) | Tidak dikerjakan (sesuai default) | Di luar cakupan C1–C12 by design |
| G4 (nama & interpretasi 9 pola SMARTS) | 🔴 PENDING REVIEW Farmasi | Daftar `upscale` dipakai apa adanya, ditandai belum tervalidasi |
| G5 (ambang `risk_level` warna 3D) | Tidak diubah | Ambang existing `simulation_orchestrator.py` dipertahankan |
| G6 (skema `shap_detail` dkk.) | 🔴 PENDING REVIEW Ketua Tim + Faris | Field baru Optional (backward-compat), sudah diwire ke `simulation_orchestrator.py` — lihat commit C10 |
| G7 (kontradiksi skor↔zona) | Tidak disentuh | Isu Alur F, di luar cakupan C1–C12 |

Rincian keterbatasan lengkap (termasuk yang tidak menguntungkan): lihat
`ml/reports/C12_limitations.md`.
