# 21 -- Uji Signifikansi Statistik (dev_pool, Tahap 2 v3.0)

## Wilcoxon signed-rank berpasangan (GATNN-DNN vs tiap baseline, 10-fold outer identik)

| Baseline | mean_diff (GATNN - baseline) | statistic | p-value | Signifikan (p<0.05)? |
|---|---|---|---|---|
| random_forest | +0.0048 | 24.00 | 0.7695 | Tidak |
| lightgbm | +0.0642 | 0.00 | 0.0020 | Ya |
| xgboost | +0.0536 | 4.00 | 0.0137 | Ya |
| logistic_regression | +0.0524 | 1.00 | 0.0039 | Ya |

## Y-randomization multi-seed (sanity check leakage)

AUC dengan label diacak, 5 shuffle seed (dev_pool, fold 0, hyperparameter terbaik fold 0): **0.5547 +/- 0.0752** (ekspektasi ~0.5)

SE(AUC) analitis di bawah H0 = 0.0847, z = 0.65, ambang leakage: |z| > 2 (~p<0.05 dua-sisi pada MEAN multi-seed).

n_train=611, n_test=61, hyperparameter dipakai: {'lr': 0.001, 'hidden': 64, 'dropout': 0.2}

| Seed | AUC |
|---|---|
| 42 | 0.6322 |
| 1 | 0.5929 |
| 2 | 0.4119 |
| 3 | 0.5621 |
| 4 | 0.5742 |

✅ AUC mendekati 0.5 (dalam rentang noise sampling) -- tidak ada indikasi leakage tersembunyi. Aman melanjutkan ke TU.22.