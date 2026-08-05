# Baseline RF & MLP -- split=scaffold

Dataset: `ml/data/processed/arm_a.parquet` (839 senyawa), 5 seed x 5 fold

| Metrik | RF mean | RF std | MLP mean | MLP std |
|---|---|---|---|---|
| auc_roc | 0.7302 | 0.0470 | 0.6603 | 0.0663 |
| auc_pr | 0.8025 | 0.0497 | 0.7461 | 0.0663 |
| accuracy | 0.7026 | 0.0354 | 0.6762 | 0.0439 |
| sensitivity | 0.8951 | 0.0356 | 0.8540 | 0.0951 |
| specificity | 0.3805 | 0.0885 | 0.3703 | 0.1670 |
| precision | 0.7082 | 0.0451 | 0.6992 | 0.0482 |
| f1 | 0.7893 | 0.0281 | 0.7645 | 0.0440 |
| mcc | 0.3280 | 0.0712 | 0.2625 | 0.1010 |
| brier | 0.1990 | 0.0138 | 0.2214 | 0.0278 |
| ece | 0.0845 | 0.0234 | 0.1135 | 0.0433 |