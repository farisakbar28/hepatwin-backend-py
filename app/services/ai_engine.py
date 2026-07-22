import logging
from typing import List, Optional

import numpy as np
import shap
import torch
import torch.nn as nn
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, global_mean_pool

# Sumber tunggal kamus SMARTS + gerbang validasi (app/chem, Fase 1). ai_engine
# tidak lagi mendefinisikan SMARTS-nya sendiri (AGENTS.md §4: satu sumber).
from app.chem.smarts_library import (
    SMARTS_COMPILED,
    SMARTS_LIBRARY,
    validated_library,
)

logger = logging.getLogger(__name__)

class HybridGNN(nn.Module):
    """
    Arsitektur Hybrid GNN + Features.
    """
    def __init__(self, node_features=9, hidden_channels=64, num_struct_features=9, num_classes=1):
        super(HybridGNN, self).__init__()
        self.conv1 = GCNConv(node_features, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        
        # Concat GNN output (hidden_channels) dengan structural features (num_struct_features)
        self.lin = nn.Linear(hidden_channels + num_struct_features, num_classes)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, edge_index, batch, struct_features):
        # Lapisan Graf Molekuler
        x = self.conv1(x, edge_index)
        x = torch.relu(x)
        x = self.conv2(x, edge_index)
        x = torch.relu(x)
        
        # Global Pooling
        x = global_mean_pool(x, batch)
        
        # Penggabungan fitur (Concatenation)
        x = torch.cat([x, struct_features], dim=1)
        
        # Lapisan Klasifikasi Akhir
        x = self.lin(x)
        return self.sigmoid(x)

def smiles_to_graph_and_features(smiles: str) -> tuple:
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return None, None
        
    # Ekstraksi node (atom) features
    node_features = []
    for atom in mol.GetAtoms():
        # Feature 1-hot sederhana
        features = [
            atom.GetAtomicNum(),
            atom.GetDegree(),
            atom.GetValence(Chem.ValenceType.IMPLICIT),
            int(atom.GetIsAromatic())
        ]
        # Pad to 9 features untuk kesesuaian arsitektur
        features += [0] * (9 - len(features))
        node_features.append(features)
        
    x = torch.tensor(node_features, dtype=torch.float)
    
    # Ekstraksi edge (ikatan)
    edge_indices = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        edge_indices += [[i, j], [j, i]]
        
    if edge_indices:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        
    # Ekstraksi Structural Features via SMARTS (pola precompiled, sumber tunggal)
    struct_features = []
    for pat in SMARTS_COMPILED.values():
        has_match = 1.0 if mol.HasSubstructMatch(pat) else 0.0
        struct_features.append(has_match)
        
    struct_tensor = torch.tensor([struct_features], dtype=torch.float)
    
    data = Data(x=x, edge_index=edge_index)
    return data, struct_tensor

class HybridAIEngine:
    """
    Model AI Hybrid (RDKit Substructure + GNN PyTorch Geometric).
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        num_struct_features = len(SMARTS_LIBRARY)
        self.model = HybridGNN(num_struct_features=num_struct_features).to(self.device)
        self.weights_loaded = False
        if self.model_path:
            try:
                self.model.load_state_dict(torch.load(self.model_path, map_location=self.device, weights_only=True))
                self.weights_loaded = True
                logger.info(f"Loaded weights from {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not load weights from {self.model_path}: {e}. Using random weights.")
        self.model.eval() # Set to evaluation mode

        logger.info(
            f"HybridAIEngine initialized on {self.device}. Path: {model_path}. "
            f"Weights loaded: {self.weights_loaded}"
        )
        self.ready = True

    @property
    def model_status(self) -> str:
        """'trained' hanya bila bobot artefak berhasil dimuat dari model_path;
        selain itu 'untrained_random_weights' (temuan audit F1, AGENTS.md §3.10).
        Dilarang mengembalikan skor dari model tak terlatih tanpa penanda ini."""
        return "trained" if self.weights_loaded else "untrained_random_weights"

    def validate_smiles(self, smiles: str) -> bool:
        """
        Validasi SMILES dasar menggunakan RDKit.
        """
        if not smiles or not isinstance(smiles, str) or len(smiles.strip()) == 0:
            return False
        
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(smiles)
            return mol is not None
        except Exception:
            return False

    def get_explainability(self, smiles: str) -> List[str]:
        # Implementasi SHAP attribution
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                return ["Invalid Structure"]

            data, struct_tensor = smiles_to_graph_and_features(smiles)
            if data is None:
                return ["Feature Extraction Failed"]
                
            data = data.to(self.device)
            struct_tensor = struct_tensor.to(self.device)
            batch = torch.zeros(data.x.size(0), dtype=torch.long).to(self.device)

            # SHAP explainer untuk layer struktural (memerlukan wrapper function)
            # Karena GNN kompleks di SHAP, kita targetkan substruktur RDKit
            
            def model_predict(struct_input):
                # struct_input is shape (n_samples, n_features)
                n_samples = struct_input.shape[0]
                
                # Expand data.x and data.edge_index to match n_samples if n_samples > 1
                # Because SHAP generates multiple synthetic samples
                out_scores = []
                for i in range(n_samples):
                    struct_t = torch.tensor(struct_input[i:i+1], dtype=torch.float).to(self.device)
                    with torch.no_grad():
                        out = self.model(data.x, data.edge_index, batch, struct_t)
                    out_scores.append(out.cpu().numpy()[0])
                return np.array(out_scores)

            # Baseline kosong (semua substruktur = 0)
            background = np.zeros((1, len(SMARTS_LIBRARY)))
            explainer = shap.KernelExplainer(model_predict, background)

            # Hitung SHAP value untuk fitur molekul saat ini
            shap_values = explainer.shap_values(struct_tensor.cpu().numpy(), silent=True)

            # Ekstrak fitur yang paling berkontribusi positif
            matched_features = []
            feature_names = list(SMARTS_LIBRARY.keys())

            # shap_values[0] adalah prediksi untuk sample pertama
            # Nilai SHAP > 0 berarti meningkatkan risiko DILI
            sv = shap_values[0] if isinstance(shap_values, list) else shap_values[0]

            for i, val in enumerate(sv):
                if val > 0.001 and struct_tensor[0][i].item() == 1.0:
                    matched_features.append(feature_names[i])

            if not matched_features:
                # Jika tidak ada atribusi kuat dari SHAP, fallback ke fitur struktural yang ada
                for i, val in enumerate(struct_tensor[0]):
                    if val.item() == 1.0:
                        matched_features.append(feature_names[i])

            # Saring: hanya gugus yang lolos ACC tertulis Farmasi boleh
            # tampil dengan nama farmakologis (PRD §8.5, AGENTS.md §3.7).
            allowed = validated_library()
            contributing_features = [f for f in matched_features if f in allowed]

            if not contributing_features:
                contributing_features = ["Menunggu validasi Farmasi untuk gugus spesifik"]

            return contributing_features
            
        except Exception as e:
            logger.error(f"SHAP error: {e}")
            return ["Explainability evaluation error"]

    def predict_dili_risk(self, smiles: str) -> float:
        # Integrasi penuh (Sprint 1: inference asli pakai bobot PyG model)
        try:
            # Handle hardcoded mock overrides for Edukasi Mendalam if needed
            if smiles == "paracetamol_mock":
                smiles = "CC(=O)NC1=CC=C(O)C=C1"
            elif smiles == "amox_mock":
                smiles = "CC1(C)SC2C(NC(=O)C(N)c3ccc(O)cc3)C(=O)N12" # Amoxicillin part

            data, struct_tensor = smiles_to_graph_and_features(smiles)
            if data is None:
                return 0.5
                
            data = data.to(self.device)
            struct_tensor = struct_tensor.to(self.device)
            batch = torch.zeros(data.x.size(0), dtype=torch.long).to(self.device)
            
            with torch.no_grad():
                score = self.model(data.x, data.edge_index, batch, struct_tensor)
                
            return float(score.item())
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 0.5