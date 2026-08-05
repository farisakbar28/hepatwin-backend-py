# C4 — Desain Arsitektur Hybrid GATNN-DNN

Dokumen ini bisa dibaca berdiri sendiri oleh juri teknis tanpa perlu membaca
kode. Arsitektur **tidak berubah** dari branch `upscale`
(`ml/src/hepatwin_ml/models/gatnn_dnn.py`) — task ini murni dokumentasi dan
verifikasi kesesuaian kode terhadap spesifikasi `PROJECT_FIX_MODEL.md` §3,
bukan implementasi baru.

## 1. Diagram arsitektur dua cabang

```
                         SMILES (smiles_standardized, hasil C2)
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 │                                              │
        Graf molekul (C3)                             Fingerprint (1200-dim)
   node [n_atom,34] + edge [n_bond*2,6]           MACCS(167)+ECFP4(1024)+SMARTS(9)
                 │                                              │
     ┌───────────▼───────────┐                      ┌───────────▼───────────┐
     │   CABANG GRAF (GAT)    │                      │    CABANG DNN         │
     │  GATv2Conv(34→64×4h)   │                      │  Linear(1200→512)     │
     │  edge_dim=6, heads=4   │                      │  ReLU + Dropout       │
     │  ELU                   │                      │  Linear(512→128)      │
     │  GATv2Conv(256→64×4h)  │                      │  ReLU + Dropout       │
     │  edge_dim=6, heads=4   │                      │                       │
     │  ELU                   │                      │  out: [batch,128]     │
     │  global_mean_pool      │                      └───────────┬───────────┘
     │  out: [batch,256]      │                                  │
     └───────────┬────────────┘                                  │
                 │                                                │
                 └──────────────────┬─────────────────────────────┘
                                     │  concat → [batch, 384]
                          Linear(384→128) → ReLU → Dropout
                              Linear(128→1)
                                     │
                              LOGIT [batch]  (bukan probabilitas)
                                     │
                    (training)                    (inferensi, setelah C7)
                 BCEWithLogitsLoss                 sigmoid(logit) → kalibrator
                 pos_weight dari train fold           → dili_score ∈ [0,1]
```

**Dimensi terverifikasi lewat eksekusi** (`ml/tests/test_features.py`,
`ml/tests/test_gatnn_dnn.py`): node 34, edge 6, fingerprint 1200, cabang graf
`hidden=64 × heads=4 = 256`, cabang DNN `128`, gabungan `384`.

## 2. Justifikasi tiap komponen

| Komponen | Justifikasi |
|---|---|
| `GATv2Conv` (bukan `GATConv`/`GCNConv`) | Mekanisme atensi dinamis (Brody et al., GATv2) lebih ekspresif daripada atensi statis `GATConv` atau tanpa-atensi `GCNConv`. Versi `master` lama (`app/services/ai_engine.py` pra-C10) memakai `GCNConv` — bukan Graph **Attention** sama sekali, padahal arsitektur yang diminta C4/PRD eksplisit "GATNN". |
| `edge_dim=6` pada kedua layer GAT | Informasi jenis ikatan (rangkap/aromatik/dalam-cincin) relevan secara kimia untuk toksisitas (mis. cincin aromatik terhalogenasi vs alifatik jenuh). `GCNConv` versi lama tidak punya mekanisme untuk memakai fitur edge sama sekali — informasi ini hilang total pada arsitektur lama. |
| `heads=4`, `concat=True` | Multi-head attention menangkap pola atensi berbeda secara paralel (mis. satu head fokus elektronegativitas, head lain topologi cincin) tanpa perlu memilih satu skema secara manual. `concat=True` mempertahankan seluruh informasi head (256-dim) alih-alih merata-ratakannya. |
| Dua layer `GATv2Conv` (bukan 1 atau 3+) | Dua hop pesan cukup untuk menjangkau substruktur toxicophore lokal (cincin + substituen langsung) tanpa over-smoothing yang umum terjadi pada GNN dalam pada graf molekul berukuran kecil-sedang (~5–100 atom pasca-filter heavy-atom `standardize.py`). |
| Aktivasi ELU | Dipilih (bukan ReLU) mengikuti Wibowo dkk. (2025) — ELU tidak memiliki masalah "dying neuron" pada nilai negatif dan menghasilkan gradien lebih halus untuk graf ber-atensi. |
| `global_mean_pool` (bukan sum/max) | Rata-rata atas node membuat representasi graf tidak bias terhadap ukuran molekul (senyawa besar tidak otomatis mendominasi skala embedding) — penting karena korpus mencakup rentang ukuran luas (5–100 atom berat). |
| Cabang DNN + fingerprint (MACCS+ECFP4+SMARTS) | Mengikuti Wibowo dkk. (2025): fingerprint menangkap substruktur global/frekuensi bit yang sulit ditangkap representasi graf lokal 2-hop. ECFP4 radius-2 menangkap lingkungan atom lebih luas dari yang dijangkau 2 layer GAT untuk atom di pusat molekul besar. |
| Blok SMARTS 9-dim di indeks terakhir fingerprint | Prasyarat explainability C8 tingkat gugus: SHAP hanya bermakna bila fitur yang dijelaskan benar-benar memengaruhi prediksi model, bukan dihitung terpisah dari fitur training. `SMARTS_SLICE` di `features/smarts.py` menunjuk balik ke blok ini agar C8 tidak ambigu. |
| Fusion `Linear(384→128)→ReLU→Dropout→Linear(128→1)` | Non-linear combiner ringkas antara dua representasi cabang; 128-dim intermediate cukup untuk mempelajari interaksi lintas-cabang tanpa menambah parameter berlebihan pada dataset ≈870 senyawa (risiko overfitting dengan head lebih besar). |
| Keluaran **logit** (bukan probabilitas via `Sigmoid` di `forward()`) | `BCEWithLogitsLoss` secara numerik lebih stabil (log-sum-exp trick internal) daripada `BCELoss` + `Sigmoid` terpisah. Versi `master` lama menaruh `nn.Sigmoid()` di dalam `forward()` — ini **menghalangi kalibrasi post-hoc** (C7) karena model sudah "mengunci" bentuk probabilitasnya sendiri saat training, sebelum tahu skor itu perlu dikalibrasi ulang lewat isotonic/Platt scaling. |
| `Dropout` di GAT branch, DNN branch, dan head fusion | Regularisasi konsisten di seluruh jalur forward — penting untuk dataset berukuran kecil (≈870 senyawa) di mana risiko overfitting deep model signifikan (dicatat eksplisit sebagai keterbatasan di C12). |

## 3. Fungsi loss, metrik evaluasi, strategi regularisasi

| Aspek | Nilai | Alasan |
|---|---|---|
| Loss | `BCEWithLogitsLoss(pos_weight=...)` | Klasifikasi biner + kelas tidak seimbang (≈528 positif / 342 negatif di korpus training, lihat C5). `pos_weight` **wajib dihitung dari train fold saja** (bukan seluruh dataset) untuk mencegah kebocoran informasi label val/test ke bobot loss. |
| Optimizer | `AdamW(lr=0.0005, weight_decay=1e-4)` | AdamW memisahkan weight decay dari update momentum (Loshchilov & Hutter, 2019) — regularisasi L2 yang lebih konsisten dibanding Adam+L2 klasik. |
| Scheduler | `ReduceLROnPlateau(mode="max", factor=0.5, patience=10)` monitor `val_auc` | Menurunkan learning rate saat AUC validasi stagnan 10 epoch — mencegah overshooting saat mendekati optimum lokal tanpa jadwal manual yang perlu ditebak di muka. |
| Early stopping | `patience=30`, monitor `val_auc`, checkpoint terbaik disimpan (bukan epoch terakhir) | Mencegah overfitting pada dataset kecil; `val_auc` dipilih (bukan val_loss) karena AUC adalah metrik keputusan utama proyek (ranking risiko), tidak sensitif terhadap kalibrasi skala loss. |
| Metrik evaluasi (C7) | accuracy, AUC-ROC, AUC-PR, precision, recall/sensitivity, specificity, F1, MCC, confusion matrix, Brier, ECE | AUC-ROC/AUC-PR untuk ranking; Brier/ECE untuk kualitas kalibrasi probabilitas (`dili_score` menggerakkan intensitas warna hotspot 3D, bukan sekadar ranking — kalibrasi bukan sekadar nice-to-have). MCC dipilih di samping F1 karena lebih robust terhadap ketidakseimbangan kelas sedang yang ada di korpus ini. |
| Regularisasi | Dropout (seragam per nilai `dropout` konstruktor) + `weight_decay=1e-4` (AdamW) + early stopping + scaffold-disjoint hold-out (C5) | Kombinasi eksplisit vs implisit: dropout+weight_decay menahan model dari overfit ke fitur individual, scaffold-disjoint split (bukan random split) menahan model dari overfit ke *kerangka kimia* yang sama muncul di train dan test. |

## 4. Asal-usul hyperparameter — nested CV 10-fold, `upscale`, bukan tebakan

Hyperparameter final (`lr=0.0005, hidden=64, dropout=0.2`) **tidak dicari
ulang** di `fix-model` — dipakai langsung dari hasil nested cross-validation
10-fold outer di branch `upscale`, direkam di
`ml/reports/_upscale_archive/22_final_holdout_eval.json` (disalin apa adanya
dari `upscale` pada task C0, bukan ditulis ulang):

```json
"gatnn_dnn": {"dropout": 0.2, "hidden": 64, "lr": 0.0005}
```

Hasil evaluasi hold-out (167 senyawa, Arm A `upscale`, **bukan** korpus
`fix-model` — lihat catatan di §5) yang dipakai sebagai konteks pembanding di
C7:

| Model | AUC hold-out | 95% CI bootstrap |
|---|---|---|
| GATNN-DNN | 0.6821 | [0.588, 0.770] |
| Random Forest | 0.6914 | [0.603, 0.777] |
| LightGBM | 0.6905 | [0.591, 0.774] |
| XGBoost | 0.6668 | [0.576, 0.749] |
| Logistic Regression | 0.6365 | [0.538, 0.725] |

DeLong test GATNN-DNN vs baseline lain: seluruh p-value > 0.05 kecuali vs
Logistic Regression (p=0.0073) — GATNN-DNN **tidak signifikan lebih baik**
dari RF/LightGBM/XGBoost pada Arm A `upscale`; ini konteks jujur yang dibawa
ke C7, bukan disembunyikan.

## 5. Catatan penting: hyperparameter dipakai ulang, dataset TIDAK

Hyperparameter di atas divalidasi pada **Arm A `upscale`** (839 senyawa: DILIrank
saja, sumber SMILES resolusi PubChem). Korpus training `fix-model` (≈870
senyawa, sumber SMILES Supabase, lihat C5) **berbeda** — ukuran mirip tapi
bukan dataset identik. `PROJECT_FIX_MODEL.md` §3 secara eksplisit meminta
hyperparameter ini dipakai langsung tanpa nested CV ulang (di luar cakupan
C1–C12, lihat §6 batas lingkup dokumen tersebut) — keputusan ini diterima
sebagai asumsi kerja proyek, bukan diverifikasi ulang di sini. Konsekuensinya
dicatat di C12 (limitations): AUC hasil training `fix-model` (C7) bisa
berbeda dari 0.6821 di atas, dan itu **bukan tanda bug** — dua dataset yang
berbeda secara sah menghasilkan angka berbeda meski hyperparameter sama.

## 6. Baseline pembanding (C7)

`ml/src/hepatwin_ml/models/baselines.py` (dipakai ulang apa adanya):

| Baseline | Hyperparameter final (`upscale`, nested CV) |
|---|---|
| Random Forest | `n_estimators=500, max_depth=None, class_weight=balanced` |
| LightGBM | `num_leaves=15, learning_rate=0.1` |
| XGBoost | `max_depth=5, learning_rate=0.1` |
| Logistic Regression | `C=0.1, penalty=l2, class_weight=balanced` |
| MLP | tersedia di `baselines.py`, tidak wajib dilaporkan C7 (DoD C7 eksplisit minta XGBoost) |

## 7. Verifikasi kode terhadap spesifikasi ini

Dijalankan sebagai bagian C4 (bukan hanya dibaca):

```
pytest ml/tests/test_gatnn_dnn.py -> lulus (bagian dari 47 test ml/ yang hijau sejak C2/C3)
```

`GraphBranch.out_dim == hidden * GAT_HEADS == 64 * 4 == 256`;
`concat_dim == 256 + 128 == 384` — diverifikasi lewat pembacaan kode
`ml/src/hepatwin_ml/models/gatnn_dnn.py` baris 45 & 84, bukan asumsi.
