"""Kamus SMARTS + gerbang validasi Farmasi.

Dasar: PRD §8.5, §13 item #2 · AGENTS.md §3.7 · Arsitektur §D.2.

Pola SMARTS boleh dipakai sebagai fitur model kapan saja. Namun nama gugus
HANYA boleh muncul di output explainability (response API) bila lolos
`validated_library()` — yaitu setelah anggota Farmasi memberi ACC tertulis.
Nama yang salah di media pembelajaran lebih merusak daripada tidak ada nama.

Pola dikompilasi saat import: SMARTS invalid → error saat startup, bukan saat
request (EXECUTION_PLAN.md T1.7).
"""
from rdkit import Chem

# Sembilan pola yang sudah ada di repo (dipindah dari ai_engine.py, TA.2).
# JANGAN tambah/kurangi tanpa alasan — perubahan fitur = wajib latih ulang model.
SMARTS_LIBRARY: dict[str, str] = {
    "Phenol group": "c1ccccc1O",
    "Acetamide / Amide group": "C(=O)N",
    "Carboxylic acid group": "C(=O)O",
    "Sulfonamide group": "S(=O)(=O)N",
    "Beta-lactam ring": "C1C(=O)NC1",
    "Primary amine": "[NX3;H2,H3]",
    "Nitro group": "N(=O)=O",
    "Thiazole ring": "c1scnc1",
    "Piperazine": "C1CNCCN1",
}

# Diisi manusia SETELAH ACC tertulis dari anggota Farmasi. JANGAN diisi agent
# (AGENTS.md §3.7). Selama kosong, explainability tidak menampilkan nama gugus.
SMARTS_VALIDATED_BY_PHARMACY: set[str] = set()


def _compile_library() -> dict[str, "Chem.Mol"]:
    """Kompilasi semua pola saat import. Gagal kompilasi → error startup."""
    compiled: dict[str, "Chem.Mol"] = {}
    for name, smarts in SMARTS_LIBRARY.items():
        pattern = Chem.MolFromSmarts(smarts)
        if pattern is None:
            raise ValueError(
                f"Pola SMARTS invalid untuk '{name}': {smarts!r} (gagal MolFromSmarts)"
            )
        compiled[name] = pattern
    return compiled


# Kamus pola terkompilasi — dipakai bersama oleh featurizer & GNN struct features.
SMARTS_COMPILED: dict[str, "Chem.Mol"] = _compile_library()


def validated_library() -> dict[str, str]:
    """Hanya gugus ber-ACC Farmasi yang boleh tampil bernama di response API
    (PRD §8.5, §13 item #2). Kosong selama `SMARTS_VALIDATED_BY_PHARMACY` kosong."""
    return {k: v for k, v in SMARTS_LIBRARY.items() if k in SMARTS_VALIDATED_BY_PHARMACY}
