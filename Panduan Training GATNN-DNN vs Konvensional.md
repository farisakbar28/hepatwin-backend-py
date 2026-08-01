# Panduan Teknis: Melatih & Membuktikan Superioritas GATNN-DNN atas Model Konvensional untuk Prediksi DILI

## 0. Ringkasan Realitas Ilmiah (Baca Ini Dulu)

Klaim di laporan Anda bahwa "GATNN-DNN meningkatkan akurasi secara signifikan" merujuk pada Wibowo, Chong & Tayara (2025), *Toxicology* 514:154108. Setelah saya cek langsung:

| Fakta | Detail |
|---|---|
| Metodologi asli | 10-fold cross-validation + 20% data ditahan sebagai external test set |
| Hasil model GATNN-DNN | Precision 75,14% · Sensitivity 85,2% · MCC 0,399 · **AUC 0,757** · F1 82,5% |
| Dataset gabungan | DILIrank (FDA) **digabung langsung** dengan LiverTox — label diselaraskan jadi biner, duplikat dihapus |
| Studi lanjutan (J. Cheminformatics 2025) | Model **DILIGeNN (berbasis GraphSAGE)** mengalahkan DNN-GATNN pada task identik: **AUC 0,897** |
| Studi independen lain (Nature Comm. 2025, toksikogenomik hati) | Random Forest justru **mengalahkan** LightGBM/XGBoost/HistGB dalam stabilitas & overfitting-gap pada dataset molekuler kecil |

**Implikasi untuk Anda:** GNN tidak otomatis menang melawan model pohon pada dataset sekecil DILIrank (~1.336 senyawa). Ini adalah pola yang dikenal luas di cheminformatics — GNN butuh data dalam jumlah besar untuk mengungguli fingerprint + gradient boosting. Karena itu, **klaim "lebih bagus" harus Anda buktikan sendiri lewat eksperimen yang adil**, bukan disalin dari satu paper. Ini justru memperkuat posisi Anda di GEMASTIK: juri akan menilai proses pembuktian, bukan sekadar hasil akhir.

---

## 1. Kerangka Pembuktian Ilmiah (Sebelum Ngoding)

Rumuskan dulu hipotesis Anda secara eksplisit — ini yang akan Anda tulis di laporan/paper:

- **H0 (null):** Tidak ada perbedaan signifikan performa antara GATNN-DNN dan model konvensional terbaik (RF/LightGBM) pada task klasifikasi DILI, dengan fitur & split yang sama.
- **H1 (alternatif):** GATNN-DNN memiliki performa signifikan lebih tinggi (secara statistik, bukan cuma angka lebih besar).

Supaya klaim Anda valid, EMPAT syarat ini wajib dipenuhi:

1. **Fair comparison** — semua model dilatih & dievaluasi pada fold data yang *identik*, bukan split acak yang berbeda-beda per model.
2. **Statistical significance testing** — selisih AUC 0,75 vs 0,76 pada data kecil sering kali **tidak signifikan**. Anda wajib uji ini, jangan hanya bandingkan angka mentah.
3. **Splitting yang sesuai domain kimia** — random split pada data molekul menggelembungkan performa semua model (lihat §3).
4. **External/held-out validation** — model yang dievaluasi hanya lewat cross-validation pada data yang sama untuk tuning **rawan overclaiming**.

---

## 2. Persiapan Dataset

### 2.1 Dataset inti: DILIrank 2.0

- 1.336 senyawa obat berlabel FDA, dengan kelas: `vMost-DILI-Concern`, `vLess-DILI-Concern`, `vNo-DILI-Concern`, `Ambiguous DILI-concern`.
- Untuk klasifikasi biner (praktik standar di literatur, termasuk paper Wibowo et al.): `vMost + vLess = 1 (DILI positif)`, `vNo = 0 (DILI negatif)`. Kelas `Ambiguous` **dibuang** dari training (bukan diberi label paksa) — ini konvensi resmi FDA LTKB sendiri, karena label ambigu justru menambah noise ground-truth.
- Cek **duplikat SMILES** dan **senyawa dengan stereokimia sama tapi entry ganda** — ini sumber data leakage paling umum di studi DILI.

### 2.2 Dataset "pembantu" — cara kerja konkret, bukan sekadar narasi

Laporan Anda menyebut FAERS, Tox21, dan LiverTox sebagai "pengaya". Ini butuh dibedah — masing-masing punya cara kerja dan tingkat kelayakan yang **sangat berbeda**:

| Dataset | Peran yang *valid secara metodologis* | Catatan kehati-hatian |
|---|---|---|
| **LiverTox (NIH LTKB)** | **Augmentasi label langsung**: senyawa yang belum ada di DILIrank tapi punya kategori likelihood di LiverTox (A–E) dikonversi ke label biner sesuai skema yang sama, lalu digabung ke training set. Ini persis yang dilakukan Wibowo et al. — memperbesar N training. | Skema konversi likelihood→biner harus didokumentasikan eksplisit (mis. kategori A/B/C = positif, E = negatif, kategori "unlikely"/tanpa cukup bukti dibuang), dan harus konsisten dengan skema DILIrank supaya tidak mencampur definisi ground-truth yang berbeda. |
| **Tox21** | **Multi-task pretraining / transfer learning**: encoder graf (GATNN) dilatih dulu untuk memprediksi 12 endpoint toksisitas Tox21 (reseptor nuklir & stress-response pathway), lalu *fine-tuned* pada DILIrank. Ini pendekatan yang sudah mapan di literatur representation learning molekuler — bukan penggabungan label langsung, karena endpoint Tox21 bukan DILI. | Tox21 **tidak boleh** digabung langsung sebagai label DILI tambahan — endpoint biokimianya berbeda dari hepatotoksisitas klinis. Perannya adalah membantu encoder belajar representasi struktur molekul yang lebih general sebelum fokus ke DILI. |
| **FAERS** | Sumber sinyal *auxiliary/weak label* paling banter (mis. frekuensi laporan efek samping hepatik sebagai fitur tambahan), **bukan** untuk membangun label ground-truth. | FAERS memiliki *reporting bias* berat (over-reporting untuk obat baru/populer, tidak ada denominator populasi terpapar, tidak causal-verified). Menggunakannya sebagai label langsung akan **melemahkan**, bukan memvalidasi, kredibilitas model Anda di hadapan juri yang paham farmakovigilans. Kalau dipakai, batasi pada exploratory feature dan sebutkan keterbatasannya secara eksplisit. |

**Rekomendasi konkret:** gunakan LiverTox untuk augmentasi label (paling valid dan sudah terbukti di paper rujukan Anda), gunakan Tox21 untuk pretraining encoder (opsional, tapi kuat secara metodologis), dan **jangan** jadikan FAERS sebagai sumber label — cukup sebutkan sebagai potensi pengembangan lanjutan di bagian limitasi.

### 2.3 Splitting: random split vs scaffold split

Ini poin paling sering diabaikan dan paling sering membuat klaim "model X lebih baik" runtuh saat direview:

- **Random split** menempatkan molekul-molekul yang sangat mirip (scaffold sama, hanya beda substituen kecil) di train dan test secara bersamaan → model manapun (GNN maupun RF) akan tampak sangat akurat karena efektifnya "menghafal", bukan generalisasi.
- **Scaffold split** (Bemis-Murcko scaffold, tersedia di RDKit `MurckoScaffold`) mengelompokkan molekul berdasarkan kerangka inti, lalu memastikan scaffold yang sama tidak muncul di train dan test sekaligus. Ini adalah standar de facto di benchmark cheminformatics modern (MoleculeNet, dsb).

**Gunakan scaffold split sebagai split utama**, dan random split hanya sebagai pembanding sekunder untuk menunjukkan Anda sadar akan bias ini (nilai plus besar untuk kredibilitas ilmiah laporan Anda).

---

## 3. Featurisasi (untuk kedua jenis model)

Wajib **identik sumber fitur mentahnya** antara GATNN-DNN dan baseline supaya perbandingan adil:

- **Untuk cabang GAT (graf):** SMILES → graf molekul via RDKit → node features (jenis atom, muatan formal, hibridisasi, aromatisitas, jumlah H) & edge features (jenis ikatan, konjugasi, keanggotaan cincin).
- **Untuk cabang DNN & baseline konvensional (RF/LightGBM):** ECFP4 (radius 2, biasanya 1024–2048 bit) + MACCS keys + deskriptor fisikokimia (MW, TPSA, XLogP, jumlah donor/akseptor H-bond, dsb) — persis seperti yang sudah disebut di laporan Anda.

Penting: RF/LightGBM **tidak bisa** langsung memakai representasi graf — itu sebabnya perbandingan yang adil adalah *"graf+fingerprint (GATNN-DNN)" vs "fingerprint saja (RF/LightGBM)"*, bukan asumsi bahwa arsitektur yang lebih kompleks otomatis lebih unggul.

---

## 4. Arsitektur Model

```
Input SMILES
     │
     ├──► [Graph construction] ──► GAT layers (multi-head attention, 2–3 layer)
     │         │                         │
     │         │                    Graph-level pooling (attention pooling / mean+max)
     │         │                         │
     │         └────────────► Graph embedding (dim g)
     │
     └──► [ECFP4 + MACCS + descriptors] ──► DNN branch (Dense-BN-ReLU-Dropout x2-3)
                                                   │
                                          Feature embedding (dim d)
                                                   │
                        ┌──────────────────────────┘
                        ▼
              Concatenate [g ; d] ──► Dense fusion layer(s) ──► Sigmoid output
```

Baseline yang harus disandingkan (bukan cuma disebut, tapi benar-benar dilatih dan dites):
- **Random Forest** (scikit-learn `RandomForestClassifier`)
- **LightGBM** (`LGBMClassifier`)
- **XGBoost** (opsional tapi disarankan, karena sering jadi pembanding standar di literatur DILI)
- **Logistic Regression** sebagai sanity-check baseline paling sederhana

---

## 5. Protokol Training & Validasi yang Adil

### 5.1 Nested cross-validation

Supaya tuning hyperparameter tidak "mengintip" data test (data leakage klasik yang sering membuat klaim akurasi tidak bisa direplikasi):

```
Outer loop: 5-fold (atau 10-fold, ikuti paper rujukan) scaffold-stratified CV
  └─ Inner loop: pada 4 fold training, lakukan 3-fold CV untuk hyperparameter search
       (grid/random/Bayesian search — beri budget waktu/percobaan SAMA untuk semua model)
  └─ Evaluasi model dengan hyperparameter terbaik pada 1 fold outer yang belum pernah dilihat
```

Ulangi untuk GATNN-DNN dan semua baseline **pada fold outer yang identik** (gunakan seed & indeks split yang sama, simpan sebagai file agar reproducible).

### 5.2 External hold-out set

Sisihkan 15–20% data di awal (sebelum CV apapun), scaffold-disjoint dari training, dan JANGAN disentuh sampai model final selesai dituning. Ini adalah "ujian akhir" — angka dari sini yang paling kredibel untuk laporan Anda.

### 5.3 Mengatasi imbalance kelas

DILIrank binari biasanya tidak seimbang (~55–65% positif tergantung skema). Gunakan:
- Metrik yang robust terhadap imbalance: **AUPRC**, **MCC**, **F1**, bukan hanya accuracy.
- Class weighting (`class_weight='balanced'` di RF/LR) atau `scale_pos_weight` di LightGBM/XGBoost — jangan oversampling sintetik (SMOTE) pada representasi graf, karena interpolasi vektor graf tidak menghasilkan molekul valid secara kimiawi.

---

## 6. Pembuktian Statistik — Bagian Paling Sering Dilewatkan

Jangan cukup bandingkan "AUC GATNN-DNN = 0,80 vs RF = 0,76" lalu klaim menang. Lakukan:

1. **Paired comparison per fold**: catat skor (AUC/MCC/F1) tiap model di tiap fold outer CV yang *sama persis*.
2. **Wilcoxon signed-rank test** (non-parametrik, cocok untuk jumlah fold kecil, mis. 5–10) atau **paired t-test** bila distribusi selisih mendekati normal.
3. **DeLong's test** khusus untuk membandingkan dua AUC secara statistik pada test set yang sama (implementasi tersedia di `scikit-posthocs`, `pROC` R, atau reimplementasi Python-nya).
4. **Bootstrap confidence interval** (mis. 1000 resample) pada external hold-out set untuk melaporkan AUC dengan interval kepercayaan, bukan angka tunggal.
5. **Y-randomization / permutation test**: acak label training, latih ulang model — jika performa tetap tinggi, itu tanda model belajar pola palsu/leakage, bukan sinyal biologis nyata. Ini pengecekan sanity yang sangat dihargai reviewer/juri.

Laporkan hasil dengan format: *"GATNN-DNN mencapai AUC 0,XX (95% CI: a–b) dibanding RF 0,YY (95% CI: c–d); perbedaan signifikan secara statistik (p < 0,05, Wilcoxon signed-rank, n=10 fold)"* — bukan sekadar tabel angka.

---

## 7. Skeleton Kode (Python)

```python
# ============================================================
# 1. Scaffold split (RDKit) — dipakai sama untuk semua model
# ============================================================
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import StratifiedKFold
import numpy as np

def get_scaffold(smiles):
    mol = Chem.MolFromSmiles(smiles)
    return MurckoScaffold.MurckoScaffoldSmiles(mol=mol) if mol else None

def scaffold_kfold_split(smiles_list, labels, n_splits=10, seed=42):
    scaffolds = {}
    for idx, smi in enumerate(smiles_list):
        scaf = get_scaffold(smi)
        scaffolds.setdefault(scaf, []).append(idx)
    scaffold_groups = list(scaffolds.values())
    rng = np.random.RandomState(seed)
    rng.shuffle(scaffold_groups)
    folds = [[] for _ in range(n_splits)]
    for i, group in enumerate(scaffold_groups):
        folds[i % n_splits].extend(group)
    return folds  # list indeks per fold, scaffold-disjoint

# ============================================================
# 2. Featurisasi ECFP4 untuk baseline RF/LightGBM
# ============================================================
from rdkit.Chem import AllChem
import numpy as np

def smiles_to_ecfp4(smiles, n_bits=2048):
    mol = Chem.MolFromSmiles(smiles)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    return np.array(fp)

# ============================================================
# 3. Baseline model — LightGBM & Random Forest
# ============================================================
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, matthews_corrcoef, f1_score

def train_eval_baseline(model, X_train, y_train, X_test, y_test):
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = model.predict(X_test)
    return {
        "auc": roc_auc_score(y_test, proba),
        "auprc": average_precision_score(y_test, proba),
        "mcc": matthews_corrcoef(y_test, pred),
        "f1": f1_score(y_test, pred),
    }

lgbm = LGBMClassifier(class_weight="balanced", random_state=42)
rf = RandomForestClassifier(class_weight="balanced", n_estimators=500, random_state=42)

# ============================================================
# 4. GATNN-DNN — pakai PyTorch Geometric
# ============================================================
import torch
import torch.nn as nn
from torch_geometric.nn import GATv2Conv, global_mean_pool

class GATNN_DNN(nn.Module):
    def __init__(self, node_feat_dim, ecfp_dim, hidden=128, heads=4):
        super().__init__()
        self.gat1 = GATv2Conv(node_feat_dim, hidden, heads=heads, concat=True)
        self.gat2 = GATv2Conv(hidden * heads, hidden, heads=1, concat=False)
        self.dnn_branch = nn.Sequential(
            nn.Linear(ecfp_dim, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(),
        )
        self.fusion = nn.Sequential(
            nn.Linear(hidden + 128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 1),
        )

    def forward(self, x, edge_index, batch, ecfp):
        g = torch.relu(self.gat1(x, edge_index))
        g = torch.relu(self.gat2(g, edge_index))
        g = global_mean_pool(g, batch)          # graph-level embedding
        d = self.dnn_branch(ecfp)                # fingerprint embedding
        fused = torch.cat([g, d], dim=1)
        return torch.sigmoid(self.fusion(fused))

# ============================================================
# 5. Perbandingan statistik — Wilcoxon signed-rank per fold
# ============================================================
from scipy.stats import wilcoxon

auc_gatnn_per_fold = [...]   # isi dari hasil 10-fold outer CV
auc_rf_per_fold = [...]      # fold yang SAMA persis dengan di atas

stat, p_value = wilcoxon(auc_gatnn_per_fold, auc_rf_per_fold)
print(f"Wilcoxon p-value: {p_value:.4f}")
```

---

## 8. Format Pelaporan Hasil (untuk laporan/paper GEMASTIK)

Tabel minimal yang wajib ada:

| Model | Fitur | Split | AUC (95% CI) | AUPRC | MCC | F1 | p-value vs GATNN-DNN |
|---|---|---|---|---|---|---|---|
| Logistic Regression | ECFP4+MACCS+desc | Scaffold, 10-fold | ... | ... | ... | ... | ... |
| Random Forest | ECFP4+MACCS+desc | Scaffold, 10-fold | ... | ... | ... | ... | ... |
| LightGBM | ECFP4+MACCS+desc | Scaffold, 10-fold | ... | ... | ... | ... | ... |
| GATNN-DNN | Graf + ECFP4 fusion | Scaffold, 10-fold | ... | ... | ... | ... | — |
| GATNN-DNN (+ LiverTox augmentasi) | Graf + ECFP4 fusion | Scaffold, 10-fold | ... | ... | ... | ... | ... |
| GATNN-DNN (+ Tox21 pretraining) | Graf + ECFP4 fusion | Scaffold, 10-fold | ... | ... | ... | ... | ... |

Baris terakhir dua ini penting: dengan memisahkan efek dataset "pembantu" secara **ablation study** (dengan vs tanpa augmentasi/pretraining), Anda bisa membuktikan secara eksplisit apakah LiverTox/Tox21 benar-benar berkontribusi, bukan cuma diklaim.

---

## 9. Jebakan Umum yang Bisa Menjatuhkan Klaim Anda di Depan Juri

1. **Random split tapi diklaim general** — akan langsung dipertanyakan siapapun yang paham cheminformatics.
2. **Baseline "dilemahkan"** (mis. RF pakai hyperparameter default sementara GNN dituning ekstensif) — bikin perbandingan tidak adil dan mudah dibantah.
3. **Tidak ada uji signifikansi statistik** — selisih AUC 1–2 poin pada data 1.336 senyawa seringkali *noise*, bukan sinyal nyata.
4. **Label FAERS dipakai sebagai ground-truth** — akan dianggap tidak paham farmakovigilans oleh juri berlatar belakang farmasi/kedokteran.
5. **Tidak ada external hold-out** — semua angka berasal dari data yang "pernah dilihat" proses tuning.
6. **Tidak transparan soal AUC absolut** — laporan Anda sebaiknya jujur bahwa AUC 0,75–0,80-an adalah kisaran realistis untuk task ini (sesuai literatur), bukan angka >0,95 yang justru mencurigakan (indikasi leakage).

---

## Referensi Utama

- Wibowo AS, Chong KT, Tayara H (2025). *Enhancing DILI toxicity prediction through integrated graph attention (GATNN) and dense neural networks (DNN)*. Toxicology, 514:154108. https://doi.org/10.1016/j.tox.2025.154108 (ScienceDirect: https://www.sciencedirect.com/science/article/abs/pii/S0300483X25000642)
- Studi lanjutan DILIGeNN (GraphSAGE) — *Improving drug-induced liver injury prediction using graph neural networks with augmented graph features from molecular optimisation*, Journal of Cheminformatics (2025) — pembanding performa AUC 0,897 vs DNN-GATNN AUC 0,757.
  - https://jcheminf.biomedcentral.com/articles/10.1186/s13321-025-01068-3
  - https://link.springer.com/article/10.1186/s13321-025-01068-3
- FDA LTKB — DILIrank 2.0 Dataset: https://www.fda.gov/science-research/liver-toxicity-knowledge-base-ltkb/drug-induced-liver-injury-rank-dilirank-20-dataset
- Bemis GW, Murcko MA (1996) — dasar scaffold splitting.
- DeLong ER, DeLong DM, Clarke-Pearson DL (1988) — uji statistik pembanding AUC.
