# Evaluasi GATNN-DNN -- split=scaffold

Dataset: `ml/data/processed/arm_b.parquet` (1253 senyawa), 5 seed x 5 fold = 25 run

| Metrik | Mean | Std |
|---|---|---|
| auc_roc | 0.6672 | 0.0291 |
| auc_pr | 0.6388 | 0.0454 |
| accuracy | 0.6162 | 0.0540 |
| sensitivity | 0.5768 | 0.1731 |
| specificity | 0.6547 | 0.1851 |
| precision | 0.6159 | 0.0670 |
| f1 | 0.5741 | 0.1076 |
| mcc | 0.2413 | 0.0846 |
| brier | 0.2692 | 0.0480 |
| ece | 0.1706 | 0.1133 |