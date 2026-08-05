"""TU.6/TU.11 -- 9 pola SMARTS toxicophore untuk fitur DNN + explainability.

[KEPUTUSAN AI -- PENDING REVIEW FARMASI, lihat EXECUTION_PLAN_UPSCALE.md SS14.1
gerbang B5]: nama & pola berikut diwarisi dari
docs/REQUEST_VALIDASI_FARMASI.md (dev-vedo, belum pernah dikirim/dijawab
Farmasi) -- nama farmakologis kolom `name` BUKAN final, jangan ditampilkan ke
pengguna di panel explainability sebelum ACC tertulis Farmasi diterima.

Dua pola ditandai UPSCALE.md SS7 sebagai "bermasalah" dan diperbaiki di sini
(perbaikan sintaks SMARTS/kimia komputasi, bukan keputusan farmakologis):

- Nitro: pola asli `N(=O)=O` cuma cocok representasi netral pentavalen: banyak
  SMILES kanonik (termasuk keluaran standardize.py di sini) menulis nitro
  sebagai bentuk bermuatan-terpisah `[N+](=O)[O-]`, jadi pola asli sering GAGAL
  cocok pada struktur nyata. Diperbaiki jadi mencocokkan kedua bentuk.
- Fenol: pola asli `c1ccccc1O` mencocokkan OKSIGEN APA PUN yang menempel ke
  cincin (eter aromatik, ester aromatik, dll -- bukan cuma -OH). Diperbaiki
  jadi spesifik oksigen berikatan-2 dengan H (gugus -OH asli).
"""
from dataclasses import dataclass

from rdkit import Chem


@dataclass(frozen=True)
class SmartsPattern:
    name: str  # PENDING REVIEW FARMASI -- lihat docstring modul
    pattern: str
    note: str = ""


SMARTS_PATTERNS: list[SmartsPattern] = [
    SmartsPattern("Phenol group", "[OX2H]c", "diperbaiki dari c1ccccc1O (UPSCALE.md SS7)"),
    SmartsPattern("Acetamide / Amide group", "C(=O)N"),
    SmartsPattern("Carboxylic acid group", "C(=O)[OX2H1]"),
    SmartsPattern("Sulfonamide group", "S(=O)(=O)N"),
    SmartsPattern("Beta-lactam ring", "C1C(=O)NC1"),
    SmartsPattern("Primary amine", "[NX3;H2,H3;!$(NC=O)]"),
    SmartsPattern(
        "Nitro group",
        "[$([N+](=O)[O-]),$(N(=O)=O)]",
        "diperbaiki dari N(=O)=O agar cocok bentuk bermuatan-terpisah (UPSCALE.md SS7)",
    ),
    SmartsPattern("Thiazole ring", "c1scnc1"),
    SmartsPattern("Piperazine", "C1CNCCN1"),
]

# Indeks awal blok SMARTS di vektor fitur DNN gabungan (MACCS + ECFP4 + SMARTS),
# dipakai TU.11 (SHAP) untuk menunjuk balik ke pola asal. Lihat features/fingerprints.py.
SMARTS_SLICE = slice(-len(SMARTS_PATTERNS), None)

_compiled = [Chem.MolFromSmarts(p.pattern) for p in SMARTS_PATTERNS]
assert all(m is not None for m in _compiled), "Ada pola SMARTS yang gagal dikompilasi"


def smarts_flags(mol: Chem.Mol) -> list[int]:
    """Mol RDKit -> list[int] panjang 9, 1 bila pola cocok (HasSubstructMatch)."""
    return [1 if mol.HasSubstructMatch(patt) else 0 for patt in _compiled]
