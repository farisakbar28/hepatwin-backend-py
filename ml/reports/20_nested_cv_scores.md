# 20 -- Nested CV Scores (Arm A dev_pool, 10-fold outer scaffold CV)

dev_pool: 672 senyawa (holdout_set 167 TIDAK disentuh). Budget hyperparameter: 10 trial random search, inner 3-fold, IDENTIK lintas model (UPSCALE.md SS13.3).

| Model | AUC-ROC (mean+-std) | MCC (mean+-std) | AUC-PR (mean+-std) |
|---|---|---|---|
| gatnn_dnn | 0.7397 +/- 0.0546 | 0.3550 +/- 0.1201 | 0.7976 +/- 0.0430 |
| random_forest | 0.7402 +/- 0.0523 | 0.3679 +/- 0.0858 | 0.8098 +/- 0.0528 |
| lightgbm | 0.6809 +/- 0.0633 | 0.3164 +/- 0.1478 | 0.7570 +/- 0.0559 |
| xgboost | 0.6915 +/- 0.0672 | 0.3077 +/- 0.1012 | 0.7586 +/- 0.0626 |
| logistic_regression | 0.6927 +/- 0.0547 | 0.2961 +/- 0.0966 | 0.7588 +/- 0.0296 |

## AUC per fold outer (utk uji Wilcoxon TU.21)

| Fold | gatnn_dnn | random_forest | lightgbm | xgboost | logistic_regression |
|---|---|---|---|---|---|
| 0 | 0.7278 | 0.7542 | 0.6958 | 0.6347 | 0.6889 |
| 1 | 0.7160 | 0.7315 | 0.6528 | 0.6683 | 0.6887 |
| 2 | 0.7526 | 0.7013 | 0.6577 | 0.6692 | 0.7192 |
| 3 | 0.7842 | 0.8000 | 0.6351 | 0.7825 | 0.7439 |
| 4 | 0.7885 | 0.7732 | 0.7297 | 0.6933 | 0.6733 |
| 5 | 0.7630 | 0.7985 | 0.7215 | 0.7393 | 0.7748 |
| 6 | 0.7938 | 0.7867 | 0.7587 | 0.7050 | 0.7348 |
| 7 | 0.6361 | 0.6646 | 0.6097 | 0.5806 | 0.6431 |
| 8 | 0.6488 | 0.6427 | 0.5709 | 0.6315 | 0.5692 |
| 9 | 0.7861 | 0.7497 | 0.7767 | 0.8108 | 0.6910 |
