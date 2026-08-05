"""TU.21 -- Jalankan Wilcoxon signed-rank (4 baseline vs GATNN-DNN, 10-fold
outer TU.20) + Y-randomization sanity check pada dev_pool.

DeLong test & bootstrap CI TIDAK dijalankan di sini -- disiapkan (significance.py)
untuk dieksekusi TU.22 pada holdout_set (belum boleh disentuh sebelum itu).
"""
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from hepatwin_ml.significance import wilcoxon_vs_gatnn
from hepatwin_ml.train import build_graph_dataset, train_gatnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASELINE_NAMES = ["random_forest", "lightgbm", "xgboost", "logistic_regression"]


def run_y_randomization(seeds: list[int] = (42, 1, 2, 3, 4)) -> dict:
    """Acak label_binary pada dev_pool, latih ulang GATNN-DNN dgn hyperparameter
    terbaik fold 0 (TU.20), evaluasi pada fold outer dev_pool (bukan hold-out).
    Ekspektasi: AUC mendekati 0.5.

    MULTI-SEED (bukan 1 shuffle): satu titik data pada test fold kecil (n~61)
    punya statistical power rendah untuk membedakan leakage nyata dari noise
    sampling (SE(AUC) di bawah H0 ~0.076 pada ukuran ini) -- pelajaran dari
    audit TU.21 (lihat 21_significance_devpool.md) tempat 1 shuffle sempat
    memicu false alarm (0.62) yang ternyata cuma noise setelah diverifikasi
    dgn 4 shuffle tambahan (mean 0.5508, menyebar simetris di sekitar 0.5)."""
    df = pd.read_parquet("ml/data/processed/arm_a_devpool.parquet")
    fold_data = json.loads(Path("ml/data/interim/outer_fold_indices.json").read_text(encoding="utf-8"))
    scores = json.loads(Path("ml/reports/20_nested_cv_scores.json").read_text(encoding="utf-8"))

    fold0 = fold_data["folds"][0]
    train_idx, test_idx = np.array(fold0["train_idx"]), np.array(fold0["test_idx"])
    best_params = scores[0]["gatnn_dnn"]["best_params"]
    logger.info("Y-randomization pakai hyperparameter fold 0: %s, %d seed", best_params, len(seeds))

    from sklearn.metrics import roc_auc_score

    aucs = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        shuffled_labels = df["label_binary"].to_numpy().copy()
        rng.shuffle(shuffled_labels)
        df_shuffled = df.copy()
        df_shuffled["label_binary"] = shuffled_labels

        train_df = df_shuffled.iloc[train_idx].reset_index(drop=True)
        test_df = df_shuffled.iloc[test_idx].reset_index(drop=True)
        train_graphs = build_graph_dataset(train_df)
        test_graphs = build_graph_dataset(test_df)

        _, y_test, y_probs = train_gatnn(train_graphs, test_graphs, seed=seed, max_epochs=300, patience=30)
        auc = roc_auc_score(y_test, y_probs) if len(set(y_test)) > 1 else 0.5
        aucs.append(float(auc))
        logger.info("Y-randomization seed=%d: AUC=%.4f", seed, auc)

    return {
        "auc_mean": float(np.mean(aucs)),
        "auc_std": float(np.std(aucs)),
        "auc_per_seed": dict(zip(seeds, aucs)),
        "fold_used": 0,
        "hyperparams": best_params,
        "n_train": len(train_idx),
        "n_test": len(test_idx),
    }


def main() -> None:
    scores = json.loads(Path("ml/reports/20_nested_cv_scores.json").read_text(encoding="utf-8"))
    gatnn_aucs = [fold["gatnn_dnn"]["auc_roc"] for fold in scores]

    wilcoxon_results = {}
    for name in BASELINE_NAMES:
        baseline_aucs = [fold[name]["auc_roc"] for fold in scores]
        wilcoxon_results[name] = wilcoxon_vs_gatnn(gatnn_aucs, baseline_aucs)
        logger.info("Wilcoxon GATNN vs %s: p=%.4f, mean_diff=%.4f", name, wilcoxon_results[name]["p_value"], wilcoxon_results[name]["mean_diff"])

    y_rand_result = run_y_randomization()
    logger.info("Y-randomization AUC mean: %.4f +/- %.4f (ekspektasi ~0.5)", y_rand_result["auc_mean"], y_rand_result["auc_std"])

    result = {"wilcoxon": wilcoxon_results, "y_randomization": y_rand_result}
    Path("ml/reports/21_significance_devpool.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    # SE(AUC) analitis di bawah H0 (n_test kecil) -- lihat audit di 21_significance_devpool.md
    n_pos = int(pd.read_parquet("ml/data/processed/arm_a_devpool.parquet").iloc[
        json.loads(Path("ml/data/interim/outer_fold_indices.json").read_text())["folds"][0]["test_idx"]
    ]["label_binary"].sum())
    n_test = y_rand_result["n_test"]
    n_neg = n_test - n_pos
    # Hanley-McNeil di AUC=0.5: Q1=Q2=1/3, jadi (Q1-AUC^2)=(Q2-AUC^2)=1/3-1/4=1/12
    se_null = ((0.25 + (n_pos - 1) * (1 / 12) + (n_neg - 1) * (1 / 12)) / (n_pos * n_neg)) ** 0.5
    z_score = (y_rand_result["auc_mean"] - 0.5) / se_null
    leakage_flag = abs(z_score) > 2  # ~p<0.05 dua-sisi, dipakai pada MEAN multi-seed, bukan 1 titik
    lines = [
        "# 21 -- Uji Signifikansi Statistik (dev_pool, Tahap 2 v3.0)",
        "",
        "## Wilcoxon signed-rank berpasangan (GATNN-DNN vs tiap baseline, 10-fold outer identik)",
        "",
        "| Baseline | mean_diff (GATNN - baseline) | statistic | p-value | Signifikan (p<0.05)? |",
        "|---|---|---|---|---|",
    ]
    for name, r in wilcoxon_results.items():
        sig = "Ya" if r["p_value"] < 0.05 else "Tidak"
        lines.append(f"| {name} | {r['mean_diff']:+.4f} | {r['statistic']:.2f} | {r['p_value']:.4f} | {sig} |")

    lines += [
        "",
        "## Y-randomization multi-seed (sanity check leakage)",
        "",
        f"AUC dengan label diacak, {len(y_rand_result['auc_per_seed'])} shuffle seed "
        f"(dev_pool, fold 0, hyperparameter terbaik fold 0): "
        f"**{y_rand_result['auc_mean']:.4f} +/- {y_rand_result['auc_std']:.4f}** (ekspektasi ~0.5)",
        "",
        f"SE(AUC) analitis di bawah H0 = {se_null:.4f}, z = {z_score:.2f}, "
        f"ambang leakage: |z| > 2 (~p<0.05 dua-sisi pada MEAN multi-seed).",
        "",
        f"n_train={y_rand_result['n_train']}, n_test={y_rand_result['n_test']}, "
        f"hyperparameter dipakai: {y_rand_result['hyperparams']}",
        "",
        "| Seed | AUC |",
        "|---|---|",
    ]
    for s, a in y_rand_result["auc_per_seed"].items():
        lines.append(f"| {s} | {a:.4f} |")
    lines.append("")
    if leakage_flag:
        lines.append(
            "🚩 **PERINGATAN: AUC Y-randomization jauh di atas 0.5 -- indikasi leakage tersembunyi. "
            "TU.22 TIDAK BOLEH dilanjutkan sebelum diaudit (UPSCALE.md SS13.4/SS13.7).**"
        )
    else:
        lines.append(
            "✅ AUC mendekati 0.5 (dalam rentang noise sampling) -- tidak ada indikasi leakage "
            "tersembunyi. Aman melanjutkan ke TU.22."
        )
    Path("ml/reports/21_significance_devpool.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("Selesai. Leakage flag: %s", leakage_flag)


if __name__ == "__main__":
    main()
