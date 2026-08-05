# Baseline RF & MLP -- split=random

Dataset: `ml/data/processed/arm_b.parquet` (1253 senyawa), 5 seed x 5 fold

| Metrik | RF mean | RF std | MLP mean | MLP std |
|---|---|---|---|---|
| auc_roc | 0.6834 | 0.0258 | 0.6084 | 0.0306 |
| auc_pr | 0.6544 | 0.0317 | 0.5695 | 0.0337 |
| accuracy | 0.6362 | 0.0278 | 0.5757 | 0.0293 |
| sensitivity | 0.5842 | 0.0454 | 0.4866 | 0.1975 |
| specificity | 0.6830 | 0.0339 | 0.6558 | 0.2072 |
| precision | 0.6237 | 0.0306 | 0.5851 | 0.0678 |
| f1 | 0.6026 | 0.0345 | 0.5002 | 0.0970 |
| mcc | 0.2689 | 0.0562 | 0.1595 | 0.0563 |
| brier | 0.2246 | 0.0077 | 0.2501 | 0.0103 |
| ece | 0.0637 | 0.0162 | 0.0992 | 0.0270 |