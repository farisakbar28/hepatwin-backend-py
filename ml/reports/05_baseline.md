# 05 Laporan Baseline Tabular (LightGBM)

- **Jumlah Sampel Training**: 708
- **Jumlah Fitur**: 2067 (Morgan Fingerprint 2048-bit + 10 Deskriptor + 9 Gugus SMARTS)
- **Evaluasi**: 5-Fold Stratified Cross-Validation (Seed: 42)

## Performa Rata-rata 5-Fold CV

| Metrik | Rata-rata (Mean) | Standar Deviasi (Std) |
|---|---|---|
| Accuracy | 0.6992 | 0.0218 |
| AUROC | 0.7382 | 0.0320 |
| AUC-PR | 0.8185 | 0.0223 |
| Sensitivity | 0.7991 | 0.0497 |
| Specificity | 0.5321 | 0.1077 |
| MCC | 0.3447 | 0.0590 |

## Rincian Per Folds

| Fold | Accuracy | AUROC | AUC-PR | Sensitivity | Specificity | MCC |
|---|---|---|---|---|---|---|
| 1 | 0.6761 | 0.7269 | 0.8235 | 0.7753 | 0.5094 | 0.2926 |
| 2 | 0.7042 | 0.6875 | 0.7799 | 0.8876 | 0.3962 | 0.3324 |
| 3 | 0.6972 | 0.7676 | 0.8478 | 0.7528 | 0.6038 | 0.3553 |
| 4 | 0.7376 | 0.7770 | 0.8133 | 0.7614 | 0.6981 | 0.4523 |
| 5 | 0.6809 | 0.7318 | 0.8283 | 0.8182 | 0.4528 | 0.2912 |
