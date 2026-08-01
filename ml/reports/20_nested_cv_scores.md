# 20 -- Nested CV Scores (Arm A dev_pool, 10-fold outer scaffold CV)

dev_pool: 672 senyawa (holdout_set 167 TIDAK disentuh). Budget hyperparameter: 10 trial random search, inner 3-fold, IDENTIK lintas model (UPSCALE.md SS13.3).

**Catatan koreksi (2026-08-01):** GATNN-DNN sempat punya bug hyperparameter tuning no-op (lr/hidden/dropout tidak benar-benar dipakai) - lihat commit `fix(critical)`. Angka di bawah SUDAH terkoreksi (hasil refix_gatnn_nested_cv.py).

| Model | AUC-ROC (mean+-std) | MCC (mean+-std) | AUC-PR (mean+-std) |
|---|---|---|---|
| gatnn_dnn | 0.7451 +/- 0.0446 | 0.3446 +/- 0.1052 | 0.8060 +/- 0.0385 |
| random_forest | 0.7402 +/- 0.0523 | 0.3679 +/- 0.0858 | 0.8098 +/- 0.0528 |
| lightgbm | 0.6809 +/- 0.0633 | 0.3164 +/- 0.1478 | 0.7570 +/- 0.0559 |
| xgboost | 0.6915 +/- 0.0672 | 0.3077 +/- 0.1012 | 0.7586 +/- 0.0626 |
| logistic_regression | 0.6927 +/- 0.0547 | 0.2961 +/- 0.0966 | 0.7588 +/- 0.0296 |

## AUC per fold outer (utk uji Wilcoxon TU.21)

| Fold | gatnn_dnn | random_forest | lightgbm | xgboost | logistic_regression |
|---|---|---|---|---|---|
| 0 | 0.7375 | 0.7542 | 0.6958 | 0.6347 | 0.6889 |
| 1 | 0.7185 | 0.7315 | 0.6528 | 0.6683 | 0.6887 |
| 2 | 0.7615 | 0.7013 | 0.6577 | 0.6692 | 0.7192 |
| 3 | 0.7719 | 0.8000 | 0.6351 | 0.7825 | 0.7439 |
| 4 | 0.7873 | 0.7732 | 0.7297 | 0.6933 | 0.6733 |
| 5 | 0.7644 | 0.7985 | 0.7215 | 0.7393 | 0.7748 |
| 6 | 0.7975 | 0.7867 | 0.7587 | 0.7050 | 0.7348 |
| 7 | 0.6681 | 0.6646 | 0.6097 | 0.5806 | 0.6431 |
| 8 | 0.6661 | 0.6427 | 0.5709 | 0.6315 | 0.5692 |
| 9 | 0.7779 | 0.7497 | 0.7767 | 0.8108 | 0.6910 |

## Hyperparameter GATNN-DNN terpilih per fold (setelah koreksi)

| Fold | best_params |
|---|---|
| 0 | {'lr': 0.001, 'hidden': 64, 'dropout': 0.2} |
| 1 | {'lr': 0.0005, 'hidden': 64, 'dropout': 0.2} |
| 2 | {'lr': 0.0005, 'hidden': 64, 'dropout': 0.2} |
| 3 | {'lr': 0.001, 'hidden': 128, 'dropout': 0.4} |
| 4 | {'lr': 0.0005, 'hidden': 64, 'dropout': 0.2} |
| 5 | {'lr': 0.001, 'hidden': 128, 'dropout': 0.2} |
| 6 | {'lr': 0.0005, 'hidden': 64, 'dropout': 0.3} |
| 7 | {'lr': 0.0005, 'hidden': 64, 'dropout': 0.4} |
| 8 | {'lr': 0.0005, 'hidden': 128, 'dropout': 0.2} |
| 9 | {'lr': 0.0005, 'hidden': 64, 'dropout': 0.4} |
