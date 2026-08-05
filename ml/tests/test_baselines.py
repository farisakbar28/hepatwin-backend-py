import numpy as np

from hepatwin_ml.models.baselines import (
    MLP_INPUT_DIM,
    compute_scale_pos_weight,
    ecfp4_features,
    maccs_descriptor_features,
    make_lightgbm,
    make_logistic_regression,
    make_mlp,
    make_random_forest,
    make_xgboost,
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


def test_random_forest_has_balanced_class_weight():
    rf = make_random_forest(seed=42)
    assert rf.class_weight == "balanced"


def test_compute_scale_pos_weight():
    assert compute_scale_pos_weight([1, 1, 1, 0]) == 1 / 3
    assert compute_scale_pos_weight([0, 0, 0, 0, 1]) == 4.0


def test_lightgbm_trains_and_predicts_on_small_subset():
    feats = ecfp4_features(_SMILES)
    spw = compute_scale_pos_weight(_LABELS)
    model = make_lightgbm(seed=42, scale_pos_weight=spw)
    model.fit(feats, _LABELS)
    preds = model.predict_proba(feats)[:, 1]
    assert preds.shape == (len(_SMILES),)


def test_xgboost_trains_and_predicts_on_small_subset():
    feats = ecfp4_features(_SMILES)
    spw = compute_scale_pos_weight(_LABELS)
    model = make_xgboost(seed=42, scale_pos_weight=spw)
    model.fit(feats, _LABELS)
    preds = model.predict_proba(feats)[:, 1]
    assert preds.shape == (len(_SMILES),)


def test_logistic_regression_trains_and_predicts_on_small_subset():
    feats = ecfp4_features(_SMILES)
    model = make_logistic_regression(seed=42)
    model.fit(feats, _LABELS)
    preds = model.predict_proba(feats)[:, 1]
    assert preds.shape == (len(_SMILES),)
    assert model.class_weight == "balanced"
    assert model.max_iter == 1000
