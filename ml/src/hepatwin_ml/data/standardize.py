"""Standardisasi molekul untuk pipeline ml/ (batch, tanpa exception per-baris).

Urutan standardisasi: parse RDKit -> Cleanup -> LargestFragmentChooser -> Uncharger.
Logika & ambang sama dengan app/chem/standardize.py (dev-vedo) supaya artefak yang
dihasilkan konsisten dengan validasi runtime, tapi tidak melempar exception -
dipakai di loop batch atas ribuan baris, kegagalan satu baris tidak boleh
menghentikan seluruh pipeline (Aturan Main #5: kegagalan itu keluaran yang sah).
"""
from dataclasses import dataclass
from typing import Optional

from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

_ORGANIC_ATOMIC_NUMS: frozenset[int] = frozenset(
    {1, 5, 6, 7, 8, 9, 14, 15, 16, 17, 34, 35, 53}
)
_MIN_HEAVY_ATOMS = 5
_MAX_HEAVY_ATOMS = 100

_largest_fragment = rdMolStandardize.LargestFragmentChooser()
_uncharger = rdMolStandardize.Uncharger()


@dataclass(frozen=True)
class StandardizedMol:
    canonical_smiles: str
    inchikey: str
    inchikey_block1: str
    heavy_atom_count: int
    eligible: bool
    reject_reason: Optional[str]


def standardize(smiles: str) -> Optional[StandardizedMol]:
    """SMILES -> StandardizedMol, atau None bila gagal parse RDKit sama sekali."""
    if not smiles or not isinstance(smiles, str):
        return None

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    try:
        mol = rdMolStandardize.Cleanup(mol)
        mol = _largest_fragment.choose(mol)
        mol = _uncharger.uncharge(mol)
    except Exception:
        return None

    if mol is None:
        return None

    canonical = Chem.MolToSmiles(mol, canonical=True)
    inchikey = Chem.MolToInchiKey(mol)
    if not inchikey:
        return None

    heavy = mol.GetNumHeavyAtoms()
    reject_reason = None
    if heavy < _MIN_HEAVY_ATOMS or heavy > _MAX_HEAVY_ATOMS:
        reject_reason = f"heavy_atom_count={heavy} di luar rentang {_MIN_HEAVY_ATOMS}-{_MAX_HEAVY_ATOMS}"
    elif any(atom.GetAtomicNum() not in _ORGANIC_ATOMIC_NUMS for atom in mol.GetAtoms()):
        reject_reason = "mengandung atom non-organik di luar himpunan didukung"
    elif "." in canonical:
        reject_reason = "masih campuran setelah LargestFragmentChooser"

    return StandardizedMol(
        canonical_smiles=canonical,
        inchikey=inchikey,
        inchikey_block1=inchikey[:14],
        heavy_atom_count=heavy,
        eligible=reject_reason is None,
        reject_reason=reject_reason,
    )
