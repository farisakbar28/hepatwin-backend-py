"""02 — Resolusi nama obat → SMILES (untuk DILIrank yang berisi nama).

Dasar: EXECUTION_PLAN.md T1.2 · AGENTS.md §7.5.

DILIrank berisi NAMA senyawa, bukan SMILES. Skrip ini meresolusi nama → struktur
lewat PubChem PUG-REST. Bila dataset yang kamu temukan SUDAH punya kolom SMILES,
lewati skrip ini dan langsung ke 03_standardize.py.

Prinsip (AGENTS.md §7.5):
- Cache hasil ke disk (json) — skrip idempoten, tidak menghit ulang layanan.
- Hormati rate limit PubChem. Batas yang DIDOKUMENTASIKAN PubChem (verifikasi ke
  dokumentasi resmi PUG-REST sebelum menaikkan): maks ~5 request/detik. Default
  konservatif di bawah menahan ~4 req/detik. JANGAN menebak/menaikkan tanpa cek.
- Nama gagal resolve → biarkan kosong, catat. JANGAN menebak struktur.

Contoh:
    python ml/scripts/02_resolve_smiles.py \
        --input ml/data/raw/dilirank.csv --name-col "Compound Name" \
        --label-col "vDILIConcern" --out ml/data/interim/dilirank_smiles.csv
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
from _common import DATA_INTERIM, write_report  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
MIN_INTERVAL_S = 0.25  # ~4 req/s, di bawah batas terdokumentasi PubChem (verifikasi)

# Sufiks garam umum untuk fallback (EXECUTION_PLAN.md T1.2).
SALT_SUFFIXES = [
    "sodium", "hydrochloride", "tartrate", "mesylate", "maleate", "besylate",
    "succinate", "citrate", "sulfate", "phosphate", "acetate", "potassium",
    "hydrobromide", "fumarate", "nitrate", "chloride",
]

# Pola biologik yang tidak punya SMILES bermakna (T1.2) → dibuang.
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
    """Nama → canonical SMILES via PubChem. None bila gagal."""
    encoded = quote(name)
    url = f"{PUBCHEM}/compound/name/{encoded}/property/CanonicalSMILES/TXT"
    result = _get(url)
    if result and "\n" not in result and result:
        return result.splitlines()[0].strip()
    return None


def strip_salt(name: str) -> str | None:
    lowered = name.lower()
    for suffix in SALT_SUFFIXES:
        if lowered.endswith(" " + suffix):
            return name[: -(len(suffix) + 1)].strip()
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Resolusi nama obat → SMILES (PubChem)")
    ap.add_argument("--input", required=True)
    ap.add_argument("--name-col", required=True)
    ap.add_argument("--label-col", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=str(DATA_INTERIM / "name_cache.json"))
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

    for _, r in df.iterrows():
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

    out_df = pd.DataFrame(rows, columns=["name", "smiles", "label"])
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    lines = [
        "# 02 Resolusi Nama → SMILES",
        "",
        f"- Input: `{args.input}` ({len(df)} baris)",
        f"- Output: `{args.out}` ({len(out_df)} baris)",
        "",
        "| Metrik | Jumlah |",
        "|---|---|",
        f"| Berhasil resolve | {n_ok} |",
        f"| — di antaranya via fallback strip-garam | {n_ok_after_salt} |",
        f"| Biologik dibuang (-mab/-cept/-ase/…) | {n_biologic} |",
        f"| Gagal resolve | {len(failed)} |",
        "",
        "## Nama gagal resolve (dibiarkan kosong, TIDAK ditebak — T1.2)",
        "",
        *(f"- {n}" for n in failed[:200]),
        ("" if len(failed) <= 200 else f"\n… dan {len(failed) - 200} lainnya"),
    ]
    write_report("02_resolve.md", lines)
    logger.info("Selesai. %d resolve, %d gagal → %s", n_ok, len(failed), out_path)


if __name__ == "__main__":
    main()
