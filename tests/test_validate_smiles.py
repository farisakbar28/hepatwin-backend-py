"""Test endpoint validate-smiles (T3.1).

Dasar: PRD §7.1 langkah 1 · EXECUTION_PLAN.md T3.1.

Endpoint ini ringan dan cepat — tidak memuat model ML, hanya RDKit.
"""
import pytest
from pydantic import ValidationError

from app.api.endpoints.validate_smiles import ValidateSmilesRequest, validate_smiles


def test_valid_smiles():
    """SMILES valid + eligible → valid=True + canonical_smiles.
    Paracetamol (11 heavy atoms) melewati both parse DAN eligibility check.
    """
    req = ValidateSmilesRequest(smiles="CC(=O)NC1=CC=C(O)C=C1")
    resp = validate_smiles(req)
    assert resp.valid is True
    assert resp.canonical_smiles is not None
    assert resp.error_code is None


def test_valid_but_too_small():
    """SMILES valid tapi terlalu kecil untuk model → E_MOL_TOO_LARGE.
    CCO (ethanol) hanya 3 atom berat, di bawah batas minimum 5.
    Endpoint melaporkan ini sebagai invalid untuk mode triase karena
    model tidak bisa memprosesnya.
    """
    req = ValidateSmilesRequest(smiles="CCO")
    resp = validate_smiles(req)
    assert resp.valid is False
    assert resp.error_code == "E_MOL_TOO_LARGE"


def test_invalid_smiles():
    """SMILES invalid → valid=False + error_code."""
    req = ValidateSmilesRequest(smiles="INVALID_SMILES_XXX")
    resp = validate_smiles(req)
    assert resp.valid is False
    assert resp.error_code == "E_SMILES_INVALID"


def test_empty_smiles_rejected_by_pydantic():
    """String kosong ditolak Pydantic sebelum sampai handler."""
    with pytest.raises(ValidationError):
        ValidateSmilesRequest(smiles="")


def test_too_small_molecule():
    """Molekul terlalu kecil (<5 atom berat) → E_MOL_TOO_LARGE."""
    req = ValidateSmilesRequest(smiles="CC")  # hanya 2 atom berat
    resp = validate_smiles(req)
    assert resp.valid is False
    assert resp.error_code == "E_MOL_TOO_LARGE"


def test_paracetamol_canonical():
    """Paracetamol → canonical SMILES terstandarisasi."""
    req = ValidateSmilesRequest(smiles="CC(=O)NC1=CC=C(O)C=C1")
    resp = validate_smiles(req)
    assert resp.valid is True
    assert resp.canonical_smiles is not None
    # Canonical SMILES harus konsisten
    req2 = ValidateSmilesRequest(smiles=resp.canonical_smiles)
    resp2 = validate_smiles(req2)
    assert resp2.valid is True
    assert resp2.canonical_smiles == resp.canonical_smiles


def test_various_valid_smiles():
    """Berbagai SMILES valid yang lolos eligibility harus valid=True.
    Semua harus punya minimal 5 atom berat.
    """
    valid_smiles = [
        "CC(=O)NC1=CC=C(O)C=C1",  # Paracetamol (11 heavy atoms)
        "C1=CC=CC=C1",  # Benzene (6 heavy atoms)
        "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21",  # Diazepam (16 heavy atoms)
        "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",  # Ibuprofen (13 heavy atoms)
    ]
    for smi in valid_smiles:
        req = ValidateSmilesRequest(smiles=smi)
        resp = validate_smiles(req)
        assert resp.valid is True, f"SMILES '{smi}' should be valid"
        assert resp.canonical_smiles is not None
