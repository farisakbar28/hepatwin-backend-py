"""Test kamus SMARTS + gerbang validasi (EXECUTION_PLAN.md T1.7, PRD §8.5).

CATATAN: ditulis sesuai spesifikasi, BELUM dieksekusi (belum ada venv Python di
sesi pembuatan). Jalankan `pytest tests/test_smarts_library.py -v` setelah setup.
"""
from app.chem import smarts_library
from app.chem.smarts_library import (
    SMARTS_COMPILED,
    SMARTS_LIBRARY,
    validated_library,
)


def test_all_patterns_compiled():
    """Setiap pola di SMARTS_LIBRARY berhasil dikompilasi (tidak None)."""
    assert set(SMARTS_COMPILED.keys()) == set(SMARTS_LIBRARY.keys())
    assert all(pat is not None for pat in SMARTS_COMPILED.values())


def test_validated_library_empty_by_default():
    """Belum ada ACC Farmasi → validated_library() kosong (PRD §8.5, §13 #2)."""
    assert validated_library() == {}


def test_validated_library_filters_to_approved(monkeypatch):
    """Isi himpunan validasi secara manual (di test) → hanya nama itu yang lolos."""
    one = next(iter(SMARTS_LIBRARY))
    monkeypatch.setattr(smarts_library, "SMARTS_VALIDATED_BY_PHARMACY", {one})
    result = validated_library()
    assert set(result.keys()) == {one}
