"""C2 -- Loader Supabase untuk pipeline riset ml/ (menggantikan resolusi PubChem).

Baca kredensial dari .env lewat python-dotenv. Pakai SUPABASE_ANON_KEY (bukan
SUPABASE_SERVICE_ROLE_KEY) -- pipeline training hanya perlu baca, service role
key melewati Row Level Security dan tidak boleh dipakai di skrip riset
(PROJECT_FIX_MODEL.md SS5.3 langkah 1).

Hasil query di-cache ke ml/data/interim/compounds_snapshot.parquet supaya
pipeline reproducible dan tidak bergantung ketersediaan jaringan saat re-run
(langkah 4). Nol panggilan PubChem/HTTP eksternal lain di modul ini.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import pandas as pd
from dotenv import load_dotenv

_TABLE: Final[str] = "hepatwin_compounds"

# Kolom yang diminta EXECUTION_PLAN_FIX_MODEL.md C2 langkah 2.
COLUMNS: Final[list[str]] = [
    "hepatwin_id",
    "compound_name",
    "canonical_smiles",
    "isomeric_smiles",
    "inchikey",
    "dili_concern",
    "is_simulatable",
    "injury_pattern",
    "segment_list",
]

EXPECTED_SIMULATABLE_COUNT: Final[int] = 1231

_REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SNAPSHOT_PATH: Final[Path] = _REPO_ROOT / "ml" / "data" / "interim" / "compounds_snapshot.parquet"
_PAGE_SIZE: Final[int] = 1000


def _load_env() -> None:
    """Cari .env dengan berjalan naik dari lokasi file ini (independen dari CWD)."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(dotenv_path=candidate, override=False)
            return
    load_dotenv(override=False)


def _fetch_from_supabase() -> pd.DataFrame:
    """Query hepatwin_compounds via Supabase REST (anon key), paginated."""
    _load_env()
    try:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_ANON_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_ANON_KEY tidak ditemukan di .env. "
            "Salin dari .env.example dan isi kredensial Supabase (anon key, "
            "BUKAN service role key)."
        ) from exc

    from supabase import create_client  # import lokal: hindari dependensi wajib saat baca cache

    client = create_client(url, key)

    rows: list[dict] = []
    offset = 0
    while True:
        resp = (
            client.table(_TABLE)
            .select(",".join(COLUMNS))
            .range(offset, offset + _PAGE_SIZE - 1)
            .execute()
        )
        batch = resp.data
        rows.extend(batch)
        if len(batch) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE

    if not rows:
        raise RuntimeError(
            f"Query ke '{_TABLE}' mengembalikan 0 baris -- periksa kredensial "
            "atau kebijakan RLS untuk anon key."
        )

    return pd.DataFrame(rows, columns=COLUMNS)


def fetch_compounds_snapshot(
    *,
    use_cache: bool = True,
    cache_path: Path = DEFAULT_SNAPSHOT_PATH,
) -> pd.DataFrame:
    """Ambil seluruh baris `hepatwin_compounds` (kolom C2), dari cache bila ada.

    Cache TIDAK difilter `is_simulatable` -- filtering dilakukan langkah
    terpisah (`filter_simulatable`) supaya tabel corong C2/C5 bisa melaporkan
    kedua angka (total vs simulatable) dari satu sumber data yang sama.
    """
    if use_cache and cache_path.exists():
        return pd.read_parquet(cache_path)

    df = _fetch_from_supabase()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, index=False)

    meta_path = cache_path.with_suffix(".meta.json")
    meta_path.write_text(
        json.dumps(
            {
                "snapshot_taken_at_utc": datetime.now(timezone.utc).isoformat(),
                "n_rows": len(df),
                "table": _TABLE,
                "columns": COLUMNS,
            },
            indent=2,
        )
    )
    return df


def filter_simulatable(df: pd.DataFrame) -> pd.DataFrame:
    """Filter `is_simulatable = TRUE`. Berhenti (raise) bila jumlahnya bukan 1.231.

    EXECUTION_PLAN_FIX_MODEL.md C2 langkah 3: "Kalau tidak, hentikan dan
    laporkan selisihnya" -- ini bukan warning, ini hard-stop supaya angka
    yang salah tidak diam-diam mengalir ke laporan.
    """
    simulatable = df[df["is_simulatable"] == True].reset_index(drop=True)  # noqa: E712
    n = len(simulatable)
    if n != EXPECTED_SIMULATABLE_COUNT:
        raise AssertionError(
            f"is_simulatable=TRUE menghasilkan {n} baris, ekspektasi "
            f"{EXPECTED_SIMULATABLE_COUNT} (PROJECT_FIX_MODEL.md SS4.3). "
            f"Selisih: {n - EXPECTED_SIMULATABLE_COUNT}. Periksa data Supabase "
            "sebelum melanjutkan pipeline -- jangan lanjut dengan angka yang tidak cocok."
        )
    return simulatable
