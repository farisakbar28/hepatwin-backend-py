# Baseline RF & MLP -- split=random

Dataset: `ml/data/processed/arm_a.parquet` (839 senyawa), 5 seed x 5 fold

| Metrik | RF mean | RF std | MLP mean | MLP std |
|---|---|---|---|---|
| auc_roc | 0.7518 | 0.0362 | 0.6546 | 0.0504 |
| auc_pr | 0.8189 | 0.0345 | 0.7329 | 0.0494 |
| accuracy | 0.7068 | 0.0253 | 0.6651 | 0.0348 |
| sensitivity | 0.8645 | 0.0404 | 0.8426 | 0.0831 |
| specificity | 0.4484 | 0.0486 | 0.3743 | 0.1442 |
| precision | 0.7200 | 0.0169 | 0.6915 | 0.0338 |
| f1 | 0.7852 | 0.0210 | 0.7563 | 0.0307 |
| mcc | 0.3508 | 0.0590 | 0.2465 | 0.0996 |
| brier | 0.1918 | 0.0097 | 0.2351 | 0.0362 |
| ece | 0.0811 | 0.0186 | 0.1378 | 0.0653 |