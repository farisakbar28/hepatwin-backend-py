# C6_train_summary.md -- Pelatihan Model & Checkpointing

Dataset: train=580 senyawa, val=116 senyawa (dari ml/data/processed/{train,val}.parquet, C5).
Hyperparameter (JANGAN dicari ulang, PROJECT_FIX_MODEL.md SS3): lr=0.0005, hidden=64, dropout=0.2.
Total waktu pelatihan 5 seed: 1.3 menit.

## Hasil per seed (val set)

| Seed | AUC-ROC | AUC-PR | MCC | Accuracy | Brier | ECE | Waktu (s) |
|---|---|---|---|---|---|---|---|
| 42 | 0.6625 | 0.7202 | 0.3060 | 0.6810 | 0.2173 | 0.1048 | 15.0 |
| 43 | 0.6557 | 0.7224 | 0.2587 | 0.6379 | 0.2245 | 0.1280 | 15.1 |
| 44 | 0.6612 | 0.7302 | 0.2085 | 0.5776 | 0.2389 | 0.1694 | 15.3 |
| 45 | 0.6551 | 0.7394 | 0.2612 | 0.6207 | 0.2294 | 0.1384 | 15.3 |
| 46 | 0.6583 | 0.7282 | 0.1038 | 0.4828 | 0.2551 | 0.2213 | 15.5 |

## Ringkasan lintas 5 seed (mean +- std)

| Metrik | Mean | Std |
|---|---|---|
| auc_roc | 0.6586 | 0.0029 |
| auc_pr | 0.7281 | 0.0067 |
| accuracy | 0.6000 | 0.0674 |
| sensitivity | 0.5595 | 0.1501 |
| specificity | 0.6714 | 0.0816 |
| precision | 0.7477 | 0.0162 |
| f1 | 0.6289 | 0.1089 |
| mcc | 0.2276 | 0.0692 |
| brier | 0.2330 | 0.0131 |
| ece | 0.1524 | 0.0402 |

## Model produksi: seed=42

Ditetapkan **sebelum** melihat hasil seed manapun (anti cherry-pick, EXECUTION_PLAN_FIX_MODEL.md C6 langkah 5). Checkpoint disimpan berdasarkan `val_auc` terbaik selama training, bukan epoch terakhir.

- val_auc: 0.6625
- val_mcc: 0.3060

## Uji determinisme

Melatih ulang seed=42 dengan hyperparameter identik: val_auc run pertama=0.662484, run kedua=0.662484 -> **IDENTIK**.

## Artefak

- `ml/models/model_gatnn_dnn.pt` (state_dict model seed=42)
- `ml/models/model_gatnn_dnn_metadata.json` (hyperparameter, seed, n_train, tanggal, hash split_manifest.json, metrik val)
- `ml/reports/C6_train_log/seed_<n>_val_metrics.json` (log per seed)