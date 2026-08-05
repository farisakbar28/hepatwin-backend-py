# Evaluasi GATNN-DNN -- split=random

Dataset: `ml/data/processed/arm_b.parquet` (1253 senyawa), 5 seed x 5 fold = 25 run

| Metrik | Mean | Std |
|---|---|---|
| auc_roc | 0.6850 | 0.0254 |
| auc_pr | 0.6507 | 0.0299 |
| accuracy | 0.6241 | 0.0374 |
| sensitivity | 0.6112 | 0.1461 |
| specificity | 0.6358 | 0.1782 |
| precision | 0.6150 | 0.0460 |
| f1 | 0.5999 | 0.0513 |
| mcc | 0.2587 | 0.0570 |
| brier | 0.2782 | 0.0405 |
| ece | 0.2014 | 0.1046 |