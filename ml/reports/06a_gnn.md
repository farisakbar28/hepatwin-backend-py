# 06a Laporan Model GNN (HybridGNN)

- **Jumlah Sampel Training**: 708
- **Evaluasi**: 5-Fold Stratified Cross-Validation (Seed: 42)

## Performa Rata-rata 5-Fold CV

| Metrik | Rata-rata (Mean) | Standar Deviasi (Std) |
|---|---|---|
| Accuracy | 0.6229 | 0.0282 |
| AUROC | 0.6847 | 0.0327 |
| AUC-PR | 0.7821 | 0.0250 |
| Sensitivity | 0.5801 | 0.0739 |
| Specificity | 0.6943 | 0.1141 |
| MCC | 0.2699 | 0.0698 |

## Rincian Per Folds

| Fold | Accuracy | AUROC | AUC-PR | Sensitivity | Specificity | MCC |
|---|---|---|---|---|---|---|
| 1 | 0.6408 | 0.7178 | 0.8202 | 0.5281 | 0.8302 | 0.3546 |
| 2 | 0.5915 | 0.6248 | 0.7440 | 0.6404 | 0.5094 | 0.1471 |
| 3 | 0.6197 | 0.7100 | 0.7938 | 0.5730 | 0.6981 | 0.2627 |
| 4 | 0.5957 | 0.6822 | 0.7735 | 0.4773 | 0.7925 | 0.2697 |
| 5 | 0.6667 | 0.6887 | 0.7791 | 0.6818 | 0.6415 | 0.3155 |
