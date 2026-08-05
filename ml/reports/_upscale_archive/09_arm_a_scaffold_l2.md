# Evaluasi GATNN-DNN -- split=scaffold

Dataset: `ml/data/processed/arm_a.parquet` (839 senyawa), 5 seed x 5 fold = 25 run

| Metrik | Mean | Std |
|---|---|---|
| auc_roc | 0.7336 | 0.0382 |
| auc_pr | 0.8017 | 0.0402 |
| accuracy | 0.6807 | 0.0583 |
| sensitivity | 0.7328 | 0.1465 |
| specificity | 0.5973 | 0.1306 |
| precision | 0.7576 | 0.0522 |
| f1 | 0.7327 | 0.0861 |
| mcc | 0.3406 | 0.0789 |
| brier | 0.2416 | 0.0416 |
| ece | 0.1948 | 0.0762 |