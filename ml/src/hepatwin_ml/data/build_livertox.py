"""TU.12 -- Bangun Arm B: DILIrank 2.0 + LiverTox Master List.

Jalankan sebagai modul: `python -m hepatwin_ml.data.build_livertox` (lihat
main() di bawah) setelah `ml/data/interim/livertox_smiles.csv` ada (keluaran
resolve_smiles.py untuk nama LiverTox).

Sumber mentah: `ml/data/raw/masterlist02-26.csv` (ekspor CSV dari spreadsheet
resmi NIDDK/NLM, diunduh manual 2026-07-31 dari
https://www.ncbi.nlm.nih.gov/books/NBK571102/bin/masterlist02-26.xlsx).

Kuirk data nyata yang diverifikasi langsung (bukan asumsi -- EXECUTION_PLAN_UPSCALE.md
TU.12 langkah 2 mewajibkan cek langsung):
- Baris 1 = judul, baris 2 = header kolom asli -- data mulai baris 3 (skiprows=1
  lalu header otomatis dari pandas).
- Ekspor CSV menempelkan baris header KEDUA (literal "Count,Ingredient,...") di
  index ~1708 diikuti baris ringkasan total ("1705" di semua kolom), lalu baris
  kosong -- SEMUA dibuang lewat filter "Count harus bisa di-parse sebagai int".
- Sebagian skor punya sufiks " [HD]"/"[HD]" (mis. "A [HD]", "C[HD]") -- kode
  huruf dasarnya tetap dipakai untuk binerisasi, sufiks dibuang.
"""
import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from hepatwin_ml.data.standardize import standardize

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_HD_SUFFIX_RE = re.compile(r"\s*\[?HD\]?\s*$", re.IGNORECASE)

_POSITIVE = {"a", "b"}
_NEGATIVE = {"e", "e*"}
_DROPPED = {"c", "d", "x"}


def clean_likelihood_score(raw) -> Optional[str]:
    """Bersihkan sufiks [HD]/spasi, lowercase untuk perbandingan konsisten."""
    if not isinstance(raw, str):
        return None
    cleaned = _HD_SUFFIX_RE.sub("", raw).strip().lower()
    return cleaned or None


def harmonize_livertox_score(raw) -> Optional[int]:
    """Skor LiverTox mentah -> 1/0/None (None = dibuang: C/D/X atau tak dikenal).

    [KEPUTUSAN AI -- PENDING REVIEW FARMASI, EXECUTION_PLAN_UPSCALE.md SS14.1
    gerbang B2 (skema serupa juga berlaku utk LiverTox)]: A/B=positif, E/E*=negatif,
    C/D/X dibuang -- mengikuti UPSCALE.md SS3.3, presedan literatur yang
    menggabungkan DILIrank+LiverTox dgn skema persis ini.
    """
    cleaned = clean_likelihood_score(raw)
    if cleaned is None:
        return None
    if cleaned in _POSITIVE:
        return 1
    if cleaned in _NEGATIVE:
        return 0
    if cleaned in _DROPPED:
        return None
    return None  # nilai tak dikenal -> dibuang, bukan ditebak


def load_livertox_raw(csv_path: str) -> pd.DataFrame:
    """Baca CSV mentah, buang baris artefak (header terduplikasi, ringkasan,
    baris kosong) lewat filter 'Count harus int'."""
    df = pd.read_csv(csv_path, skiprows=1)
    numeric_count = pd.to_numeric(df["Count"], errors="coerce")
    df = df[numeric_count.notna()].copy()
    df = df[["Ingredient", "Brand Name", "Likelihood Score", "Year Approved"]]
    df["Ingredient"] = df["Ingredient"].astype(str).str.strip()
    return df.reset_index(drop=True)


def _standardize_livertox_rows(resolved_csv: str) -> tuple[pd.DataFrame, int, int]:
    """resolve_smiles.py output (name, smiles, label=skor mentah) -> DataFrame
    standar (inchikey_block1, label_binary, ...), sudah dedup dalam LiverTox
    sendiri. Return (df, n_dropped_label, n_dropped_standardize)."""
    resolved = pd.read_csv(resolved_csv)
    rows = []
    n_dropped_label = 0
    n_dropped_standardize = 0
    for _, r in resolved.iterrows():
        label_binary = harmonize_livertox_score(r["label"])
        if label_binary is None:
            n_dropped_label += 1
            continue
        std = standardize(r["smiles"])
        if std is None or not std.eligible:
            n_dropped_standardize += 1
            continue
        rows.append(
            {
                "name": r["name"],
                "canonical_smiles": std.canonical_smiles,
                "inchikey": std.inchikey,
                "inchikey_block1": std.inchikey_block1,
                "heavy_atom_count": std.heavy_atom_count,
                "label_binary": label_binary,
            }
        )
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset="inchikey_block1", keep="first")
    return df, n_dropped_label, n_dropped_standardize


def build_arm_b(
    arm_a_path: str = "ml/data/processed/arm_a.parquet",
    livertox_resolved_path: str = "ml/data/interim/livertox_smiles.csv",
    livertox_raw_path: str = "ml/data/raw/masterlist02-26.csv",
    out_path: str = "ml/data/processed/arm_b.parquet",
    conflicts_path: str = "ml/reports/06_label_conflicts.csv",
    report_path: str = "ml/reports/06_arm_b_construction.md",
) -> None:
    arm_a = pd.read_parquet(arm_a_path)
    n_dilirank = len(arm_a)

    livertox_raw = load_livertox_raw(livertox_raw_path)
    n_livertox_raw = len(livertox_raw)
    n_livertox_binarized = livertox_raw["Likelihood Score"].apply(harmonize_livertox_score).notna().sum()

    livertox_clean, n_dropped_label, n_dropped_std = _standardize_livertox_rows(livertox_resolved_path)
    n_livertox_resolved = len(livertox_clean)

    arm_a_keys = set(arm_a["inchikey_block1"])
    livertox_keys = set(livertox_clean["inchikey_block1"])
    overlap_keys = arm_a_keys & livertox_keys
    n_overlap = len(overlap_keys)

    conflict_rows = []
    result_rows = []

    for _, row in arm_a.iterrows():
        key = row["inchikey_block1"]
        entry = dict(row)
        if key in livertox_keys:
            lt_row = livertox_clean[livertox_clean["inchikey_block1"] == key].iloc[0]
            if lt_row["label_binary"] != row["label_binary"]:
                conflict_rows.append(
                    {
                        "inchikey_block1": key,
                        "dilirank_name": row["name"],
                        "dilirank_label": row["label_binary"],
                        "livertox_name": lt_row["name"],
                        "livertox_label": lt_row["label_binary"],
                        "resolved_to": "dilirank (menang, aturan konflik tetap)",
                    }
                )
            entry["source_dataset"] = "both"
        else:
            entry["source_dataset"] = "dilirank_only"
        result_rows.append(entry)

    for _, lt_row in livertox_clean.iterrows():
        if lt_row["inchikey_block1"] in arm_a_keys:
            continue  # sudah ditangani di loop atas (source_dataset="both")
        result_rows.append(
            {
                "name": lt_row["name"],
                "smiles_raw": lt_row["canonical_smiles"],
                "canonical_smiles": lt_row["canonical_smiles"],
                "inchikey": lt_row["inchikey"],
                "inchikey_block1": lt_row["inchikey_block1"],
                "heavy_atom_count": lt_row["heavy_atom_count"],
                "label_binary": lt_row["label_binary"],
                "source_dataset": "livertox_only",
            }
        )

    arm_b = pd.DataFrame(result_rows)
    n_conflicts = len(conflict_rows)
    n_final = len(arm_b)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    arm_b.to_parquet(out_path, index=False)

    Path(conflicts_path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(conflict_rows).to_csv(conflicts_path, index=False)

    lines = [
        "# 06 -- Bangun Dataset Arm B (DILIrank 2.0 + LiverTox)",
        "",
        "| Tahap | Jumlah |",
        "|---|---|",
        f"| DILIrank setelah TU.4 | {n_dilirank} |",
        f"| LiverTox mentah (Master List, baris obat valid) | {n_livertox_raw} |",
        f"| LiverTox setelah binerisasi (buang C/D/X) | {n_livertox_binarized} |",
        f"| LiverTox setelah resolusi SMILES + standardisasi | {n_livertox_resolved} "
        f"(dibuang: {n_dropped_label} label tak dikenal, {n_dropped_std} gagal standardisasi/kelayakan) |",
        f"| Overlap InChIKey dengan DILIrank | {n_overlap} |",
        f"| **Konflik label pada overlap** | {n_conflicts} ({n_conflicts / max(n_overlap, 1) * 100:.1f}% dari overlap) |",
        f"| **Total Arm B final** | **{n_final}** |",
        "",
        f"Perbandingan dengan ekspektasi UPSCALE.md SS3.3 (presedan Yang et al., "
        f"1.573 senyawa dari DILIrank 1.0): Arm B HepaTwin = {n_final} senyawa "
        f"(basis DILIrank 2.0, ekspektasi dokumen +-1.600-1.900).",
        "",
        f"Label positif (1): {int((arm_b['label_binary'] == 1).sum())}",
        f"Label negatif (0): {int((arm_b['label_binary'] == 0).sum())}",
        "",
        "> [KEPUTUSAN AI -- PENDING REVIEW FARMASI]: skema label & aturan konflik "
        "(DILIrank menang) mengikuti EXECUTION_PLAN_UPSCALE.md SS14.1 gerbang B2, "
        "UPSCALE.md SS3.3.",
    ]
    Path(report_path).write_text("\n".join(lines), encoding="utf-8")
    logger.info(
        "Arm B final: %d senyawa (overlap=%d, konflik=%d) -> %s", n_final, n_overlap, n_conflicts, out_path
    )


def main() -> None:
    build_arm_b()


if __name__ == "__main__":
    main()
