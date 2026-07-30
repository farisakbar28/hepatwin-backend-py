"""02 -- Resolusi nama obat -> SMILES (DILIrank/LiverTox berisi nama, bukan SMILES).

Dasar: EXECUTION_PLAN_UPSCALE.md TU.2. Resolusi lewat PubChem PUG-REST, dengan
cache disk (idempoten) dan penghormatan rate limit (~4 req/detik, di bawah
batas terdokumentasi PubChem).

Nama gagal resolve -> dibiarkan kosong, dicatat. TIDAK menebak struktur.
"""
import argparse
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
from rdkit import Chem

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
MIN_INTERVAL_S = 0.25  # ~4 req/s

SALT_SUFFIXES = [
    "sodium", "hydrochloride", "tartrate", "mesylate", "maleate", "besylate",
    "succinate", "citrate", "sulfate", "phosphate", "acetate", "potassium",
    "hydrobromide", "fumarate", "nitrate", "chloride",
]

# Pola biologik yang tidak punya SMILES bermakna -> dibuang, bukan "gagal resolve".
BIOLOGIC_PATTERNS = re.compile(r"(mab|cept|ase|toxin|globulin|interferon)$", re.IGNORECASE)


def _get(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.text.strip()
    except requests.RequestException as exc:
        logger.warning("Request gagal: %s", exc)
    return None


def resolve_name(name: str) -> str | None:
    """Nama -> canonical SMILES via PubChem. None bila gagal ATAU ambigu.

    PubChem TXT endpoint kadang mengembalikan >1 baris karena satu nama cocok ke
    beberapa CID/sinonim untuk molekul yang SAMA. Membandingkan SMILES kanonik
    RDKit (bukan string mentah) supaya senyawa umum tidak salah tercatat "gagal"
    padahal datanya ada dan konsisten. Bila baris-barisnya benar-benar struktur
    berbeda (ambigu asli) -> None, tidak ditebak.
    """
    encoded = quote(name)
    url = f"{PUBCHEM}/compound/name/{encoded}/property/CanonicalSMILES/TXT"
    result = _get(url)
    if not result:
        return None

    lines = [ln.strip() for ln in result.splitlines() if ln.strip()]
    if not lines:
        return None
    if len(lines) == 1:
        return lines[0]

    canonical_forms = set()
    for line in lines:
        mol = Chem.MolFromSmiles(line)
        if mol is None:
            logger.warning("Baris tak terparse RDKit untuk %r: %r", name, line)
            return None
        canonical_forms.add(Chem.MolToSmiles(mol))

    if len(canonical_forms) == 1:
        return lines[0]

    logger.warning("Nama %r ambigu: %d struktur berbeda ditemukan, tidak ditebak", name, len(canonical_forms))
    return None


def strip_salt(name: str) -> str | None:
    lowered = name.lower()
    for suffix in SALT_SUFFIXES:
        if lowered.endswith(" " + suffix):
            return name[: -(len(suffix) + 1)].strip()
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Resolusi nama obat -> SMILES (PubChem)")
    ap.add_argument("--input", required=True)
    ap.add_argument("--name-col", required=True)
    ap.add_argument("--label-col", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default="ml/data/interim/name_cache.json")
    ap.add_argument("--report", default="ml/reports/02_resolve_dilirank.md")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    if args.name_col not in df.columns:
        raise SystemExit(f"Kolom '{args.name_col}' tidak ada. Tersedia: {list(df.columns)}")

    cache_path = Path(args.cache)
    cache: dict[str, str | None] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        logger.info("Cache dimuat: %d entri", len(cache))

    rows = []
    n_biologic = 0
    n_ok = 0
    n_ok_after_salt = 0
    failed: list[str] = []

    total = len(df)
    for i, (_, r) in enumerate(df.iterrows()):
        name = str(r[args.name_col]).strip()
        label = r[args.label_col]
        if not name or name.lower() == "nan":
            continue
        if BIOLOGIC_PATTERNS.search(name.replace(" ", "")):
            n_biologic += 1
            continue

        if name in cache:
            smiles = cache[name]
        else:
            smiles = resolve_name(name)
            time.sleep(MIN_INTERVAL_S)
            if smiles is None:
                stripped = strip_salt(name)
                if stripped:
                    smiles = resolve_name(stripped)
                    time.sleep(MIN_INTERVAL_S)
                    if smiles is not None:
                        n_ok_after_salt += 1
            cache[name] = smiles
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=0), encoding="utf-8")

        if smiles:
            n_ok += 1
            rows.append({"name": name, "smiles": smiles, "label": label})
        else:
            failed.append(name)

        if (i + 1) % 100 == 0:
            logger.info("Progres: %d/%d (%d ok, %d gagal sejauh ini)", i + 1, total, n_ok, len(failed))

    out_df = pd.DataFrame(rows, columns=["name", "smiles", "label"])
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    lines = [
        "# 02 -- Resolusi Nama -> SMILES (DILIrank 2.0)",
        "",
        f"- Input: `{args.input}` ({len(df)} baris)",
        f"- Output: `{args.out}` ({len(out_df)} baris)",
        "",
        "| Metrik | Jumlah |",
        "|---|---|",
        f"| Berhasil resolve | {n_ok} |",
        f"| -- di antaranya via fallback strip-garam | {n_ok_after_salt} |",
        f"| Biologik dibuang (-mab/-cept/-ase/...) | {n_biologic} |",
        f"| Gagal resolve | {len(failed)} |",
        "",
        "## Nama gagal resolve (dibiarkan kosong, TIDAK ditebak)",
        "",
        *(f"- {n}" for n in failed[:200]),
        ("" if len(failed) <= 200 else f"\n... dan {len(failed) - 200} lainnya"),
    ]
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Selesai. %d resolve, %d gagal -> %s", n_ok, len(failed), out_path)


if __name__ == "__main__":
    main()
