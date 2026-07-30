"""TU.4 -- Bangun dataset Arm A (DILIrank 2.0 saja).

Pipeline: dilirank_smiles.csv (nama+SMILES+label mentah dari TU.2)
          -> harmonisasi label (TU.3, harmonize_labels.py)
          -> standardisasi + kelayakan (TU.2, standardize.py)
          -> dedup InChIKey blok-1
          -> ml/data/processed/arm_a.parquet
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

from hepatwin_ml.data.harmonize_labels import harmonize_vdili_concern
from hepatwin_ml.data.standardize import standardize

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def build_arm_a(input_path: str, out_path: str, report_path: str) -> None:
    df = pd.read_csv(input_path)
    n_resolved = len(df)

    n_dropped_ambiguous = 0
    n_unrecognized = 0
    n_reject_standardize = 0
    rows = []

    for _, r in df.iterrows():
        name = r["name"]
        smiles_raw = r["smiles"]
        label_raw = r["label"]

        try:
            label_binary = harmonize_vdili_concern(label_raw)
        except ValueError:
            n_unrecognized += 1
            logger.warning("Label tak dikenal untuk %r: %r", name, label_raw)
            continue
        if label_binary is None:
            n_dropped_ambiguous += 1
            continue

        std = standardize(smiles_raw)
        if std is None or not std.eligible:
            n_reject_standardize += 1
            reason = std.reject_reason if std else "gagal parse RDKit"
            logger.info("Ditolak standardisasi %r: %s", name, reason)
            continue

        rows.append(
            {
                "name": name,
                "smiles_raw": smiles_raw,
                "canonical_smiles": std.canonical_smiles,
                "inchikey": std.inchikey,
                "inchikey_block1": std.inchikey_block1,
                "heavy_atom_count": std.heavy_atom_count,
                "label_binary": label_binary,
                "source_dataset": "dilirank",
            }
        )

    built = pd.DataFrame(rows)
    n_before_dedup = len(built)

    conflict_mask = built.groupby("inchikey_block1")["label_binary"].transform("nunique") > 1
    n_label_conflicts = int(conflict_mask.sum())

    deduped = built.drop_duplicates(subset="inchikey_block1", keep="first")
    n_final = len(deduped)

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    deduped.to_parquet(out_file, index=False)

    lines = [
        "# 03/04 -- Bangun Dataset Arm A (DILIrank 2.0)",
        "",
        "| Tahap | Jumlah |",
        "|---|---|",
        f"| Resolusi SMILES berhasil (TU.2) | {n_resolved} |",
        f"| Label tak dikenal (data quality, dibuang) | {n_unrecognized} |",
        f"| Ambiguous-DILI-concern dibuang (TU.3, B2) | {n_dropped_ambiguous} |",
        f"| Ditolak standardisasi/kelayakan (TU.2) | {n_reject_standardize} |",
        f"| Sebelum dedup InChIKey blok-1 | {n_before_dedup} |",
        f"| Baris dengan konflik label pada InChIKey blok-1 sama | {n_label_conflicts} |",
        f"| **Total Arm A final** | **{n_final}** |",
        "",
        f"Label positif (1): {int((deduped['label_binary'] == 1).sum())}",
        f"Label negatif (0): {int((deduped['label_binary'] == 0).sum())}",
        "",
        "> [KEPUTUSAN AI -- PENDING REVIEW FARMASI]: skema label mengikuti "
        "EXECUTION_PLAN_UPSCALE.md SS14.1 gerbang B2 (vMost+vLess=1, vNo=0, "
        "Ambiguous dibuang).",
    ]
    Path(report_path).write_text("\n".join(lines), encoding="utf-8")
    logger.info("Arm A final: %d senyawa -> %s", n_final, out_path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Bangun dataset Arm A (DILIrank 2.0)")
    ap.add_argument("--input", default="ml/data/interim/dilirank_smiles.csv")
    ap.add_argument("--out", default="ml/data/processed/arm_a.parquet")
    ap.add_argument("--report", default="ml/reports/03_build_arm_a.md")
    args = ap.parse_args()
    build_arm_a(args.input, args.out, args.report)


if __name__ == "__main__":
    main()
