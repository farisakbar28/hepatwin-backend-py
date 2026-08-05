# Baseline RF & MLP -- split=scaffold

Dataset: `ml/data/processed/arm_b.parquet` (1253 senyawa), 5 seed x 5 fold

| Metrik | RF mean | RF std | MLP mean | MLP std |
|---|---|---|---|---|
| auc_roc | 0.6663 | 0.0257 | 0.6056 | 0.0341 |
| auc_pr | 0.6464 | 0.0439 | 0.5735 | 0.0528 |
| accuracy | 0.6246 | 0.0252 | 0.5777 | 0.0327 |
| sensitivity | 0.5583 | 0.0486 | 0.4967 | 0.1921 |
| specificity | 0.6834 | 0.0440 | 0.6466 | 0.1949 |
| precision | 0.6154 | 0.0396 | 0.5802 | 0.0703 |
| f1 | 0.5842 | 0.0361 | 0.5076 | 0.1064 |
| mcc | 0.2439 | 0.0495 | 0.1585 | 0.0588 |
| brier | 0.2286 | 0.0060 | 0.2523 | 0.0134 |
| ece | 0.0639 | 0.0212 | 0.1075 | 0.0395 |