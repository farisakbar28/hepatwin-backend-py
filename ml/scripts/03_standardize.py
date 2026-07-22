"""03 — Standardisasi dataset + pemetaan label biner + filter kelayakan.

Dasar: PRD §8.4 · EXECUTION_PLAN.md T1.4 · AGENTS.md §7.5.

Format-agnostik: kolom SMILES dan label ditentukan lewat argumen CLI, jadi
dataset apa pun (setelah punya kolom SMILES) bisa diproses tanpa mengubah kode.
Mengimpor standardisasi dari app/chem (sumber tunggal, AGENTS.md §4).

PENTING (PRD §8.4 / T1.4): pemetaan label kategori → biner adalah KEPUTUSAN TIM.
Default di bawah bersifat SEMENTARA dan dicatat eksplisit di laporan — konfirmasi
ke tim sebelum dipakai untuk training final.

Contoh:
    python ml/scripts/03_standardize.py \
        --input ml/data/interim/dilirank_smiles.csv \
        --smiles-col smiles --label-col dili_class --source dilirank \
        --out ml/data/interim/dilirank_std.csv
"""
import sys
from pathlib import Path

# Barrier: pastikan root repo di sys.path SEBELUM impor app.* (import-sorter tidak
# akan menghoist impor melewati statement ini). Skrip dijalankan sbg file, bukan -m
# (nama berawalan digit bukan modul valid).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse  # noqa: E402
import logging  # noqa: E402

import pandas as pd  # noqa: E402
from _common import DATA_INTERIM, write_report  # noqa: E402

from app.chem.standardize import check_eligibility, standardize  # noqa: E402
from app.core.errors import HepaTwinError  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Pemetaan label SEMENTARA (T1.4 — wajib dikonfirmasi tim, dicatat di laporan).
# Kunci di-lowercase & di-strip sebelum dicocokkan. Nilai None = baris dibuang.
DEFAULT_LABEL_MAP: dict[str, int | None] = {
    # positif DILI
    "vmost-dili-concern": 1,
    "most-dili-concern": 1,
    "vless-dili-concern": 1,
    "less-dili-concern": 1,
    "most": 1,
    "less": 1,
    "positive": 1,
    "1": 1,
    # negatif
    "vno-dili-concern": 0,
    "no-dili-concern": 0,
    "no": 0,
    "negative": 0,
    "0": 0,
    # ambigu → dibuang (jangan tebak)
    "ambiguous": None,
    "ambiguous-dili-concern": None,
}


def map_label(raw) -> int | None:
    if pd.isna(raw):
        return None
    key = str(raw).strip().lower()
    return DEFAULT_LABEL_MAP.get(key, None)


def main() -> None:
    ap = argparse.ArgumentParser(description="Standardisasi + label biner + filter kelayakan")
    ap.add_argument("--input", required=True, help="CSV input dengan kolom SMILES + label")
    ap.add_argument("--smiles-col", default="smiles")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--source", required=True, help="penanda sumber (mis. dilirank / xu2015)")
    ap.add_argument("--out", required=True, help="path CSV output")
    ap.add_argument("--report", default=None, help="path laporan md (default ml/reports/03_standardize_<source>.md)")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    n_in = len(df)
    logger.info("Baca %d baris dari %s", n_in, args.input)

    if args.smiles_col not in df.columns or args.label_col not in df.columns:
        raise SystemExit(
            f"Kolom '{args.smiles_col}' / '{args.label_col}' tidak ada. "
            f"Kolom tersedia: {list(df.columns)}"
        )

    rows = []
    n_parse_fail = 0
    n_label_drop = 0
    n_eligibility_drop = 0
    eligibility_reasons: dict[str, int] = {}
    label_counts: dict[str, int] = {}

    for _, r in df.iterrows():
        label = map_label(r[args.label_col])
        raw_label_key = str(r[args.label_col]).strip().lower()
        label_counts[raw_label_key] = label_counts.get(raw_label_key, 0) + 1
        if label is None:
            n_label_drop += 1
            continue

        std = standardize(r[args.smiles_col])
        if std is None:
            n_parse_fail += 1
            continue

        try:
            check_eligibility(std)
        except HepaTwinError as exc:
            n_eligibility_drop += 1
            eligibility_reasons[exc.code] = eligibility_reasons.get(exc.code, 0) + 1
            continue

        rows.append(
            {
                "smiles": std.canonical_smiles,
                "inchikey": std.inchikey,
                "inchikey_block1": std.inchikey_block1,
                "label": label,
                "source": args.source,
            }
        )

    out_df = pd.DataFrame(rows, columns=["smiles", "inchikey", "inchikey_block1", "label", "source"])
    n_out = len(out_df)

    # Sanity: tidak boleh ada inchikey_block1 kosong (T1.4).
    assert out_df["inchikey_block1"].str.len().eq(14).all(), "Ada inchikey_block1 tidak 14 karakter"

    from pathlib import Path

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    report_name = args.report or f"03_standardize_{args.source}.md"
    if args.report is None:
        report_name = f"03_standardize_{args.source}.md"
    lines = [
        f"# 03 Standardisasi — {args.source}",
        "",
        f"- Input: `{args.input}` ({n_in} baris)",
        f"- Output: `{args.out}` ({n_out} baris)",
        "",
        "## Alur filter (baris masuk → keluar)",
        "",
        "| Tahap | Jumlah |",
        "|---|---|",
        f"| Baris masuk | {n_in} |",
        f"| Dibuang: label tidak terpetakan/ambigu | {n_label_drop} |",
        f"| Dibuang: gagal parse/standardisasi | {n_parse_fail} |",
        f"| Dibuang: tidak lolos kelayakan | {n_eligibility_drop} |",
        f"| **Baris keluar** | **{n_out}** |",
        "",
        "## Rincian penolakan kelayakan",
        "",
        *(f"- `{code}`: {cnt}" for code, cnt in sorted(eligibility_reasons.items())),
        "",
        "## Pemetaan label (SEMENTARA — WAJIB dikonfirmasi tim, PRD §8.4 / T1.4)",
        "",
        "Nilai label mentah yang ditemukan di input dan hitungannya:",
        "",
        *(
            f"- `{k}` → {DEFAULT_LABEL_MAP.get(k, 'DIBUANG (tidak dikenal)')} ({v} baris)"
            for k, v in sorted(label_counts.items())
        ),
        "",
        "> Pemetaan default: Most/Less-concern → 1, No-concern → 0, Ambiguous/tak dikenal → dibuang.",
        "> Ini keputusan tim, bukan agent. Konfirmasi sebelum training final.",
    ]
    report_path = write_report(report_name, lines)
    logger.info("Selesai. Output %d baris → %s. Laporan → %s", n_out, out_path, report_path)


if __name__ == "__main__":
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    main()
