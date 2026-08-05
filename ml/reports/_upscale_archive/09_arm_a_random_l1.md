# Evaluasi GATNN-DNN -- split=random

Dataset: `ml/data/processed/arm_a.parquet` (839 senyawa), 5 seed x 5 fold = 25 run

| Metrik | Mean | Std |
|---|---|---|
| auc_roc | 0.7385 | 0.0291 |
| auc_pr | 0.7976 | 0.0243 |
| accuracy | 0.6889 | 0.0380 |
| sensitivity | 0.7363 | 0.0973 |
| specificity | 0.6114 | 0.1066 |
| precision | 0.7600 | 0.0337 |
| f1 | 0.7432 | 0.0466 |
| mcc | 0.3521 | 0.0673 |
| brier | 0.2285 | 0.0304 |
| ece | 0.1776 | 0.0619 |