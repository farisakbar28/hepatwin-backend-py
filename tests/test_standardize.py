"""Test standardisasi + kelayakan (EXECUTION_PLAN.md T1.3, Arsitektur §D.7).

CATATAN: ditulis sesuai spesifikasi, BELUM dieksekusi (belum ada venv Python).
Jalankan `pytest tests/test_standardize.py -v` setelah setup. Contoh molekul
mungkin perlu penyesuaian kecil setelah verifikasi RDKit nyata.
"""
import pytest

from app.core.errors import InorganicError, MolTooLargeError, SmilesInvalidError
from app.chem.standardize import (
    check_eligibility,
    standardize,
    standardize_or_raise,
)


def test_invalid_smiles_returns_none():
    assert standardize("bukan_smiles_valid$$$") is None
    assert standardize("") is None


def test_salt_is_stripped():
    """Garam natrium benzoat → fragmen terbesar (benzoat) + netralisasi, tanpa '.'."""
    std = standardize("[Na+].[O-]C(=O)c1ccccc1")
    assert std is not None
    assert "." not in std.canonical_smiles
    assert "Na" not in std.canonical_smiles


def test_same_molecule_different_smiles_same_block1():
    """Dua penulisan asam benzoat → blok-1 InChIKey identik (kunci dedup)."""
    a = standardize("O=C(O)c1ccccc1")
    b = standardize("OC(=O)c1ccccc1")
    assert a is not None and b is not None
    assert a.inchikey_block1 == b.inchikey_block1
    assert len(a.inchikey_block1) == 14


def test_too_small_molecule_rejected():
    """< 5 atom berat → E_MOL_TOO_LARGE (etanol, 3 atom berat)."""
    std = standardize("CCO")
    assert std is not None
    with pytest.raises(MolTooLargeError):
        check_eligibility(std)


def test_inorganic_metal_rejected():
    """Senyawa dengan logam (Pb) + cukup atom → E_INORGANIC.
    Tetraethyllead: Pb + 8 C = 9 atom berat, lolos cek ukuran lalu kena inorganic."""
    std = standardize("CC[Pb](CC)(CC)CC")
    assert std is not None
    with pytest.raises(InorganicError):
        check_eligibility(std)


def test_standardize_or_raise_invalid():
    with pytest.raises(SmilesInvalidError):
        standardize_or_raise("$$$invalid$$$")
