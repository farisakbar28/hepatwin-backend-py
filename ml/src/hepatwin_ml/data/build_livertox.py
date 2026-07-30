"""TU.12 -- Bangun Arm B: DILIrank 2.0 + LiverTox Master List.

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
import re
from typing import Optional

import pandas as pd

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
