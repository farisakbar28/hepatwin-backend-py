"""Standardisasi molekul + cek kelayakan.

Dasar: PRD §8.4 · Arsitektur §D.7 · EXECUTION_PLAN.md T1.3.

Urutan standardisasi: parse RDKit → Cleanup → LargestFragmentChooser → Uncharger.
Mengembalikan canonical SMILES, InChIKey lengkap, blok-1 InChIKey (14 karakter,
kunci dedup lintas dataset — bukan SMILES string, lihat AGENTS.md §7.5), dan
jumlah atom berat.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

from app.core.errors import (
    InorganicError,
    MixtureError,
    MolTooLargeError,
    SmilesInvalidError,
)

logger = logging.getLogger(__name__)

# Himpunan atom organik yang didukung (Arsitektur §D.7): H,B,C,N,O,F,Si,P,S,Cl,Se,Br,I
_ORGANIC_ATOMIC_NUMS: frozenset[int] = frozenset(
    {1, 5, 6, 7, 8, 9, 14, 15, 16, 17, 34, 35, 53}
)

_MIN_HEAVY_ATOMS = 5
_MAX_HEAVY_ATOMS = 100

# Komponen standardizer RDKit (dibuat sekali, dipakai ulang).
_largest_fragment = rdMolStandardize.LargestFragmentChooser()
_uncharger = rdMolStandardize.Uncharger()


@dataclass(frozen=True)
class StandardizedMol:
    """Hasil standardisasi satu molekul."""

    mol: "Chem.Mol"
    canonical_smiles: str
    inchikey: str
    inchikey_block1: str  # 14 karakter pertama InChIKey (kunci konektivitas)
    heavy_atom_count: int


def standardize(smiles: str) -> Optional[StandardizedMol]:
    """Standardisasi SMILES → StandardizedMol, atau None bila gagal parse.

    Tidak melempar error — dipakai di pipeline batch yang mentoleransi kegagalan.
    Untuk jalur request yang butuh error eksplisit, pakai `standardize_or_raise`.
    """
    if not smiles or not isinstance(smiles, str):
        return None

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    try:
        mol = rdMolStandardize.Cleanup(mol)
        mol = _largest_fragment.choose(mol)
        mol = _uncharger.uncharge(mol)
    except Exception as exc:  # noqa: BLE001 - RDKit dapat melempar beragam error
        logger.warning("Standardisasi gagal untuk %r: %s", smiles, exc)
        return None

    if mol is None:
        return None

    canonical = Chem.MolToSmiles(mol, canonical=True)
    inchikey = Chem.MolToInchiKey(mol)
    if not inchikey:
        return None

    return StandardizedMol(
        mol=mol,
        canonical_smiles=canonical,
        inchikey=inchikey,
        inchikey_block1=inchikey[:14],
        heavy_atom_count=mol.GetNumHeavyAtoms(),
    )


def check_eligibility(std: StandardizedMol) -> None:
    """Lempar error taksonomi bila molekul di luar cakupan model (Arsitektur §D.7).

    - atom berat < 5 atau > 100 → E_MOL_TOO_LARGE
    - atom di luar himpunan organik → E_INORGANIC
    - masih campuran (>1 fragmen / mengandung '.') → E_MIXTURE
    """
    if std.heavy_atom_count < _MIN_HEAVY_ATOMS or std.heavy_atom_count > _MAX_HEAVY_ATOMS:
        raise MolTooLargeError(
            f"Molekul di luar cakupan model ({std.heavy_atom_count} atom berat, "
            f"batas {_MIN_HEAVY_ATOMS}-{_MAX_HEAVY_ATOMS})"
        )

    for atom in std.mol.GetAtoms():
        if atom.GetAtomicNum() not in _ORGANIC_ATOMIC_NUMS:
            raise InorganicError(
                f"Senyawa mengandung atom tidak didukung: {atom.GetSymbol()}"
            )

    if "." in std.canonical_smiles:
        raise MixtureError("Masukkan satu senyawa tunggal (masih terdeteksi campuran)")


def standardize_or_raise(smiles: str) -> StandardizedMol:
    """Standardisasi + cek kelayakan untuk jalur request. Melempar
    SmilesInvalidError bila gagal parse, lalu error kelayakan dari check_eligibility."""
    std = standardize(smiles)
    if std is None:
        raise SmilesInvalidError()
    check_eligibility(std)
    return std
