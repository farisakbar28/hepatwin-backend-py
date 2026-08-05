from rdkit import Chem

from hepatwin_ml.data.standardize import standardize
from hepatwin_ml.features.fingerprints import FINGERPRINT_DIM, dnn_feature_vector
from hepatwin_ml.features.graph import EDGE_FEATURE_DIM, NODE_FEATURE_DIM, smiles_to_graph
from hepatwin_ml.features.smarts import SMARTS_PATTERNS, smarts_flags


def test_graph_feature_dims_match_spec():
    data = smiles_to_graph("c1ccccc1O")
    assert data.x.shape[1] == NODE_FEATURE_DIM == 34
    assert data.edge_attr.shape[1] == EDGE_FEATURE_DIM == 6


def test_graph_handles_molecule_without_bonds():
    data = smiles_to_graph("[Na+]")
    assert data.x.shape[0] == 1
    assert data.edge_index.shape == (2, 0)
    assert data.edge_attr.shape == (0, EDGE_FEATURE_DIM)


def test_paracetamol_graph_matches_rdkit_atom_and_bond_counts():
    """C3 AC: featurisasi parasetamol menghasilkan jumlah atom & ikatan yang benar."""
    smiles = "CC(=O)Nc1ccc(O)cc1"
    mol = Chem.MolFromSmiles(smiles)
    data = smiles_to_graph(smiles)

    assert data.x.shape[0] == mol.GetNumAtoms() == 11
    assert data.x.shape[1] == NODE_FEATURE_DIM
    # graf tak berarah disimpan sebagai edge terarah bolak-balik -> 2x jumlah ikatan RDKit
    assert data.edge_index.shape[1] == mol.GetNumBonds() * 2 == 22
    assert data.edge_attr.shape == (mol.GetNumBonds() * 2, EDGE_FEATURE_DIM)


def test_graph_built_from_standardized_salt_has_single_fragment():
    """C3 AC (konsistensi training<->inferensi): smiles_to_graph() dipakai pada
    smiles_standardized (hasil C2 standardize.py), bukan SMILES garam mentah --
    graf yang dihasilkan harus satu komponen (fragmen terbesar), bukan campuran."""
    raw_salt = "CC(=O)O.CCN"  # asam asetat + etilamina, salt-like multi-fragmen
    std = standardize(raw_salt)
    assert std is not None
    assert "." not in std.canonical_smiles

    data = smiles_to_graph(std.canonical_smiles)
    mol = Chem.MolFromSmiles(std.canonical_smiles)
    assert data.x.shape[0] == mol.GetNumAtoms()


def test_fingerprint_dim_matches_spec():
    mol = Chem.MolFromSmiles("CC(=O)Nc1ccc(O)cc1")
    vec = dnn_feature_vector(mol)
    assert vec.shape == (FINGERPRINT_DIM,) == (1200,)


def _hits(smiles: str) -> set[str]:
    mol = Chem.MolFromSmiles(smiles)
    flags = smarts_flags(mol)
    return {SMARTS_PATTERNS[i].name for i, f in enumerate(flags) if f}


def test_phenol_pattern_does_not_match_aromatic_ether():
    """Regresi bug UPSCALE.md SS7: pola lama c1ccccc1O ikut match anisole."""
    assert "Phenol group" in _hits("c1ccccc1O")
    assert "Phenol group" not in _hits("c1ccccc1OC")


def test_nitro_pattern_matches_both_neutral_and_charge_separated_forms():
    """Regresi bug UPSCALE.md SS7: pola lama N(=O)=O tidak match bentuk kanonik RDKit."""
    assert "Nitro group" in _hits("c1ccccc1N(=O)=O")
    assert "Nitro group" in _hits("O=[N+]([O-])c1ccccc1")


def test_amoxicillin_smarts_profile_is_chemically_sensible():
    hits = _hits(
        "CC1(C)S[C@@H]2[C@H](NC(=O)[C@H](N)c3ccc(O)cc3)C(=O)N2[C@H]1C(=O)O"
    )
    assert hits == {
        "Phenol group",
        "Acetamide / Amide group",
        "Carboxylic acid group",
        "Beta-lactam ring",
        "Primary amine",
    }
