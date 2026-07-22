"""Test featurizer (EXECUTION_PLAN.md T1.8, Arsitektur §D.3).

CATATAN: ditulis sesuai spesifikasi, BELUM dieksekusi (belum ada venv Python).
Jalankan `pytest tests/test_features.py -v` setelah setup.
"""
from rdkit import Chem

from app.chem.features import feature_names, featurize, featurize_batch
from app.chem.smarts_library import SMARTS_LIBRARY


def test_feature_vector_length_matches_names():
    """len(featurize(mol)) == len(feature_names()) — invariant paling penting."""
    mol = Chem.MolFromSmiles("CC(=O)Nc1ccc(O)cc1")  # paracetamol
    assert len(featurize(mol)) == len(feature_names())


def test_feature_names_composition():
    """2048 ECFP + 10 deskriptor + n SMARTS."""
    names = feature_names()
    assert sum(n.startswith("ecfp_") for n in names) == 2048
    assert sum(n.startswith("smarts::") for n in names) == len(SMARTS_LIBRARY)


def test_vector_length_consistent_across_molecules():
    smis = ["CCO", "c1ccccc1", "CC(=O)Nc1ccc(O)cc1", "O=C(O)c1ccccc1"]
    lengths = {len(featurize(Chem.MolFromSmiles(s))) for s in smis}
    assert len(lengths) == 1


def test_smarts_flag_set_when_group_present():
    """Molekul dengan asam karboksilat → flag smarts::'Carboxylic acid group' == 1."""
    names = feature_names()
    idx = names.index("smarts::Carboxylic acid group")
    vec = featurize(Chem.MolFromSmiles("O=C(O)c1ccccc1"))  # benzoic acid
    assert vec[idx] == 1.0


def test_featurize_batch_shape():
    mols = [Chem.MolFromSmiles(s) for s in ["CCO", "c1ccccc1"]]
    matrix = featurize_batch(mols)
    assert matrix.shape == (2, len(feature_names()))
