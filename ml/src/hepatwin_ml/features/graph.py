"""TU.6 -- Featurizer graf: SMILES -> torch_geometric.data.Data.

Skema fitur mengikuti UPSCALE.md SS5.2/SS5.3 (34 dim node, 6 dim edge).

Node (34): atomic number one-hot (10) + degree one-hot (6) + formal charge
one-hot (5) + total-H one-hot (5) + hybridization one-hot (6) + aromatic (1)
+ in-ring (1).

[Catatan teknis, bukan gerbang Farmasi -- ini keputusan rekayasa fitur, bukan
klaim farmakologis]: himpunan 10 elemen atomic-number eksplisit dipilih dari
elemen organik paling umum pada senyawa mirip-obat; elemen di luar daftar
(mis. Si, B, Se yang tetap lolos check_eligibility standardize.py) jatuh ke
slot "OTHER" supaya total dimensi tetap 34 sesuai spek, bukan menambah slot.

Edge (6): bond type one-hot (4: SINGLE/DOUBLE/TRIPLE/AROMATIC) + conjugated (1)
+ in-ring (1).
"""
import torch
from rdkit import Chem
from rdkit.Chem import rdchem
from torch_geometric.data import Data

_ATOM_LIST = ["C", "N", "O", "S", "F", "Cl", "Br", "I", "P"]  # + OTHER = 10 slot
_DEGREE_LIST = [0, 1, 2, 3, 4]  # + OTHER(>=5) = 6 slot
_CHARGE_LIST = [-2, -1, 0, 1]  # + OTHER = 5 slot
_TOTAL_H_LIST = [0, 1, 2, 3]  # + OTHER(>=4) = 5 slot
_HYBRIDIZATION_LIST = [
    rdchem.HybridizationType.SP,
    rdchem.HybridizationType.SP2,
    rdchem.HybridizationType.SP3,
    rdchem.HybridizationType.SP3D,
    rdchem.HybridizationType.SP3D2,
]  # + OTHER/UNSPECIFIED = 6 slot
_BOND_TYPE_LIST = [
    rdchem.BondType.SINGLE,
    rdchem.BondType.DOUBLE,
    rdchem.BondType.TRIPLE,
    rdchem.BondType.AROMATIC,
]

NODE_FEATURE_DIM = 34
EDGE_FEATURE_DIM = 6


def _one_hot_with_other(value, allowed: list) -> list[float]:
    vec = [0.0] * (len(allowed) + 1)
    if value in allowed:
        vec[allowed.index(value)] = 1.0
    else:
        vec[-1] = 1.0
    return vec


def _atom_features(atom: rdchem.Atom) -> list[float]:
    return (
        _one_hot_with_other(atom.GetSymbol(), _ATOM_LIST)
        + _one_hot_with_other(atom.GetDegree(), _DEGREE_LIST)
        + _one_hot_with_other(atom.GetFormalCharge(), _CHARGE_LIST)
        + _one_hot_with_other(atom.GetTotalNumHs(), _TOTAL_H_LIST)
        + _one_hot_with_other(atom.GetHybridization(), _HYBRIDIZATION_LIST)
        + [1.0 if atom.GetIsAromatic() else 0.0]
        + [1.0 if atom.IsInRing() else 0.0]
    )


def _one_hot_strict(value, allowed: list) -> list[float]:
    """One-hot tanpa slot OTHER -- dipakai saat spek fitur menetapkan jumlah
    kategori tetap (mis. bond type: 4 slot persis, UPSCALE.md SS5.3)."""
    vec = [0.0] * len(allowed)
    if value in allowed:
        vec[allowed.index(value)] = 1.0
    return vec


def _bond_features(bond: rdchem.Bond) -> list[float]:
    return (
        _one_hot_strict(bond.GetBondType(), _BOND_TYPE_LIST)
        + [1.0 if bond.GetIsConjugated() else 0.0]
        + [1.0 if bond.IsInRing() else 0.0]
    )


def smiles_to_graph(smiles: str) -> Data | None:
    """Canonical SMILES (sudah distandardisasi) -> torch_geometric Data, atau
    None bila gagal parse. Molekul tanpa ikatan (atom tunggal) tetap valid
    (edge_index kosong)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    node_feats = [_atom_features(atom) for atom in mol.GetAtoms()]
    x = torch.tensor(node_feats, dtype=torch.float)

    edge_indices = []
    edge_feats = []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        feat = _bond_features(bond)
        edge_indices += [[i, j], [j, i]]
        edge_feats += [feat, feat]

    if edge_indices:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_feats, dtype=torch.float)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, EDGE_FEATURE_DIM), dtype=torch.float)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
