import numpy as np

from hepatwin_ml.models.baselines import (
    MLP_INPUT_DIM,
    ecfp4_features,
    maccs_descriptor_features,
    make_mlp,
    make_random_forest,
)

_SMILES = ["c1ccccc1O", "CC(=O)Nc1ccc(O)cc1", "CCO", "CCN", "c1ccccc1N(=O)=O", "CCCl"]
_LABELS = [1, 1, 0, 0, 1, 0]


def test_ecfp4_features_shape():
    feats = ecfp4_features(_SMILES)
    assert feats.shape == (len(_SMILES), 1024)


def test_maccs_descriptor_features_shape():
    feats = maccs_descriptor_features(_SMILES)
    assert feats.shape == (len(_SMILES), MLP_INPUT_DIM)


def test_random_forest_trains_and_predicts():
    feats = ecfp4_features(_SMILES)
    rf = make_random_forest(seed=42)
    rf.fit(feats, _LABELS)
    preds = rf.predict_proba(feats)[:, 1]
    assert preds.shape == (len(_SMILES),)


def test_mlp_trains_and_predicts():
    # early_stopping=True perlu internal train/val split yang cukup besar untuk
    # stratifikasi 2 kelas -- gandakan fixture kecil supaya bukan itu yang gagal.
    smiles = _SMILES * 5
    labels = _LABELS * 5
    feats = maccs_descriptor_features(smiles)
    mlp = make_mlp(seed=42)
    mlp.fit(feats, labels)
    preds = mlp.predict_proba(feats)[:, 1]
    assert preds.shape == (len(smiles),)
