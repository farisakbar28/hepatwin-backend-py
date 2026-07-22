"""04 — Deduplikasi (InChIKey blok-1) + scaffold split.

Dasar: PRD §8.4 · Arsitektur §D.7 · AGENTS.md §7.5 · EXECUTION_PLAN.md T1.5.

MENGGANTIKAN metode salah di `data_preparation/deduplicate_smiles.py` yang
memakai canonical SMILES string (masih membedakan stereoisomer/tautomer →
kebocoran lolos). Di sini kunci dedup = blok pertama InChIKey (14 karakter),
merepresentasikan konektivitas molekul.

Aturan (PRD §8.4):
- Dedup internal DILIrank per inchikey_block1. Bila satu block1 punya label
  BERBEDA → buang SEMUA barisnya (konflik label), catat.
- Dedup lintas dataset: senyawa tumpang tindih dibuang dari EXTERNAL TEST
  (Xu et al.), BUKAN dari training — jaga kapasitas training, jamin independensi.
- Split scaffold (Bemis-Murcko) pada training: grup scaffold tidak boleh terpecah
  antara train dan valid.

Contoh:
    python ml/scripts/04_dedup_split.py \
        --dilirank-std ml/data/interim/dilirank_std.csv \
        --xu-std ml/data/interim/xu2015_std.csv \
        --out-dir ml/data/processed --valid-frac 0.15 --seed 42
"""
import argparse
import logging
from pathlib import Path

import pandas as pd
from _common import DATA_PROCESSED, write_report  # noqa: E402
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def dedup_internal(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Dedup per inchikey_block1. Konflik label → buang semua barisnya.
    Kembalikan (df_bersih, n_konflik_dibuang, n_duplikat_digabung)."""
    conflict_blocks = []
    keep_indices = []
    n_dup_merged = 0
    for block1, grp in df.groupby("inchikey_block1"):
        labels = set(grp["label"].tolist())
        if len(labels) > 1:
            conflict_blocks.append(block1)
            continue  # buang semua baris block1 ini
        # label konsisten → simpan satu wakil
        keep_indices.append(grp.index[0])
        n_dup_merged += len(grp) - 1
    clean = df.loc[keep_indices].reset_index(drop=True)
    return clean, len(conflict_blocks), n_dup_merged


def scaffold_of(smiles: str) -> str:
    """Bemis-Murcko scaffold SMILES; string kosong bila gagal (grup sendiri)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    try:
        return MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
    except Exception:
        return ""


def scaffold_split(df: pd.DataFrame, valid_frac: float, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split berbasis scaffold: seluruh grup scaffold masuk salah satu set saja.
    Grup diacak (seed tetap) lalu diisikan ke valid sampai mendekati valid_frac."""
    df = df.copy()
    df["_scaffold"] = df["smiles"].map(scaffold_of)

    groups = list(df.groupby("_scaffold"))
    rng = __import__("random").Random(seed)
    rng.shuffle(groups)

    n_target_valid = int(round(len(df) * valid_frac))
    valid_idx: list = []
    for _, grp in groups:
        if len(valid_idx) < n_target_valid:
            valid_idx.extend(grp.index.tolist())
        # sisanya ke train
    valid_mask = df.index.isin(valid_idx)
    valid = df[valid_mask].drop(columns="_scaffold").reset_index(drop=True)
    train = df[~valid_mask].drop(columns="_scaffold").reset_index(drop=True)
    return train, valid


def main() -> None:
    ap = argparse.ArgumentParser(description="Dedup InChIKey blok-1 + scaffold split")
    ap.add_argument("--dilirank-std", required=True)
    ap.add_argument("--xu-std", required=True)
    ap.add_argument("--out-dir", default=str(DATA_PROCESSED))
    ap.add_argument("--valid-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    dili = pd.read_csv(args.dilirank_std)
    xu = pd.read_csv(args.xu_std)
    n_dili_in, n_xu_in = len(dili), len(xu)

    # 1) Dedup internal DILIrank
    dili_dedup, n_conflict, n_merged = dedup_internal(dili)

    # 2) Dedup lintas dataset: buang dari XU yang block1-nya ada di DILIrank
    dili_blocks = set(dili_dedup["inchikey_block1"])
    xu_before = len(xu)
    xu_dedup = xu[~xu["inchikey_block1"].isin(dili_blocks)].reset_index(drop=True)
    n_overlap_removed = xu_before - len(xu_dedup)

    # 3) Scaffold split pada training (DILIrank)
    train, valid = scaffold_split(dili_dedup, args.valid_frac, args.seed)

    # 4) Split acak sebagai pembanding pelaporan (tidak disimpan sebagai data resmi)
    shuffled = dili_dedup.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    n_valid_rand = int(round(len(shuffled) * args.valid_frac))
    rand_valid_blocks = set(shuffled.head(n_valid_rand)["inchikey_block1"])

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    train.to_csv(out_dir / "train.csv", index=False)
    valid.to_csv(out_dir / "valid.csv", index=False)
    xu_dedup.to_csv(out_dir / "external_test.csv", index=False)

    # 5) Assert wajib (T1.5, AGENTS.md §8): nol overlap train ↔ external_test
    train_blocks = set(train["inchikey_block1"])
    ext_blocks = set(xu_dedup["inchikey_block1"])
    assert len(train_blocks & ext_blocks) == 0, "OVERLAP train ↔ external_test terdeteksi!"

    # Scaffold tidak terpecah antara train & valid
    train_scaffolds = set(train["smiles"].map(scaffold_of))
    valid_scaffolds = set(valid["smiles"].map(scaffold_of))
    shared_scaffold = (train_scaffolds & valid_scaffolds) - {""}
    assert not shared_scaffold, f"Scaffold bocor antara train & valid: {list(shared_scaffold)[:3]}"

    lines = [
        "# 04 Deduplikasi + Split",
        "",
        f"Seed: {args.seed} · valid_frac: {args.valid_frac}",
        "",
        "## DILIrank (training)",
        "",
        "| Tahap | Jumlah |",
        "|---|---|",
        f"| Masuk | {n_dili_in} |",
        f"| Duplikat block1 digabung | {n_merged} |",
        f"| Block1 konflik label dibuang (semua barisnya) | {n_conflict} |",
        f"| Setelah dedup internal | {len(dili_dedup)} |",
        f"| → train | {len(train)} |",
        f"| → valid | {len(valid)} |",
        "",
        "## Xu et al. (external test)",
        "",
        "| Tahap | Jumlah |",
        "|---|---|",
        f"| Masuk | {n_xu_in} |",
        f"| Overlap dg DILIrank dibuang (dari EXTERNAL, PRD §8.4) | {n_overlap_removed} |",
        f"| **External test final** | **{len(xu_dedup)}** |",
        "",
        "## Verifikasi",
        "",
        f"- Overlap block1 train ↔ external_test: **{len(train_blocks & ext_blocks)}** (harus 0)",
        f"- Scaffold bocor train ↔ valid: **{len(shared_scaffold)}** (harus 0)",
        f"- Pembanding split acak: {n_valid_rand} baris valid "
        f"(overlap block1 vs scaffold-valid: {len(rand_valid_blocks & set(valid['inchikey_block1']))})",
        "",
        "> Catatan PRD §8.4: DILIrank & Xu bersumber dari pool obat beririsan; external",
        "> test bisa menyusut jauh di bawah 344. Laporkan apa adanya + CI bootstrap saat evaluasi.",
    ]
    report_path = write_report("04_dedup_split.md", lines)
    logger.info(
        "Selesai. train=%d valid=%d external_test=%d. Laporan → %s",
        len(train), len(valid), len(xu_dedup), report_path,
    )


if __name__ == "__main__":
    main()
