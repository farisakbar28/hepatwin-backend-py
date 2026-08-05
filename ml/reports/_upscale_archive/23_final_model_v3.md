# 23 -- Model Final GATNN-DNN v3.0 (hyperparameter hasil TU.18-22)

**File model:** `ml/models/model_arm_a_v3_final.pt`
**Metadata:** `ml/models/model_arm_a_v3_final_metadata.json`
**Skrip pembuat:** `ml/scripts/train_final_arm_a_v3.py`

## Hyperparameter yang dipakai (pemenang nested CV TU.20)

| Hyperparameter | Nilai | Asal |
|---|---|---|
| `lr` (learning rate) | **0,0005** | Modus dari 10 fold outer nested CV, lihat `20_nested_cv_scores.md` |
| `hidden` (lebar layer GATv2Conv) | **64** | idem |
| `dropout` | **0,2** | idem |
| Arsitektur | GATv2Conv x2 (heads=4) + DNN branch, 883.585 parameter total | Tetap (UPSCALE.md SS5.1), tidak ikut di-tuning selain hidden/dropout di atas |
| Optimizer | AdamW, weight_decay=1e-4 | Tetap (UPSCALE.md SS5.5) |
| Batch size | 32 | Tetap |
| Seed | 42 | Konsisten seluruh pipeline |

Kombinasi ini yang **sama persis** dipakai untuk menghasilkan AUC 0,6821 pada
`holdout_set` di TU.22 (`14_final_comparison.md`) -- bedanya, model TU.22
dilatih dari `dev_pool` (672 senyawa), sedangkan `.pt` di file ini dilatih dari
**seluruh Arm A (839 senyawa)**.

## Data training

| | Jumlah |
|---|---|
| Total Arm A (dev_pool + holdout_set) | 839 |
| Dipakai belajar (train) | 755 |
| Disisihkan HANYA utk early-stopping (bukan evaluasi) | 84 |
| Early stopping berhenti di epoch | 35 (best_val_auc=0,6556 pada 84 senyawa early-stop, BUKAN metrik performa resmi) |

**Split 90/10 di atas beda tujuan dari `holdout_set` TU.18**: itu random
stratified sederhana, cuma buat tahu kapan berhenti training supaya tidak
overfitting -- bukan buat mengklaim performa. `val_auc=0,6556` di log training
BUKAN angka yang boleh dikutip sebagai "performa model ini", karena bukan
dari data yang benar-benar independen (himpunannya tumpang tindih dgn cara
lain dari holdout_set yang sudah dipakai TU.22).

## Catatan penting soal performa (jujur, Aturan Main #4/#5)

**Model `.pt` di file ini TIDAK memiliki angka performa sendiri yang diukur
pada data benar-benar baru** -- karena dilatih dari SELURUH Arm A (839), tidak
ada lagi senyawa DILIrank yang tersisa untuk mengujinya secara tidak bias.

Estimasi performa paling kredibel yang tersedia untuk kombinasi
arsitektur+hyperparameter ini tetap: **AUC 0,6821 (95% CI 0,588--0,770)** dari
`14_final_comparison.md` (TU.22) -- diukur dari model dengan hyperparameter
identik, dilatih dari `dev_pool` (672), diuji pada `holdout_set` (167) yang
saat itu benar-benar belum pernah dilihat. Model `.pt` di sini secara wajar
diharapkan berperforma **serupa atau sedikit lebih baik** (karena data
training ~25% lebih banyak), tapi ini **estimasi, bukan angka terukur** untuk
file spesifik ini.

Ini bukan kelemahan unik file ini -- ini konsekuensi matematis wajar dari
"refit pada seluruh data setelah nested CV selesai", praktik standar di ML
(sama seperti `refit=True` di `sklearn.GridSearchCV`). Kalau butuh angka
performa yang benar-benar terukur untuk model spesifik ini, satu-satunya cara
adalah dataset senyawa BARU (di luar Arm A) -- di luar cakupan kerja saat ini.

## Cara memuat model ini

```python
import torch
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

model = GatnnDnn(hidden=64, dropout=0.2)  # HARUS sama dgn hyperparameter di atas
state = torch.load("ml/models/model_arm_a_v3_final.pt", map_location="cpu", weights_only=True)
model.load_state_dict(state)
model.eval()
```

**Perhatian:** file ini **belum** disalin ke `app/models/` dan **belum**
menggantikan model produksi TU.14 (`app/models/model_arm_a.pt`, yang
memakai hyperparameter generik `lr=1e-3` dari UPSCALE.md v1/v2, BUKAN hasil
tuning v3.0 ini). Belum ada kalibrator untuk model ini juga -- kalau mau
dipakai produksi, perlu diulang proses kalibrasi (TU.10-style) dan
`export_to_app.py` secara terpisah.
