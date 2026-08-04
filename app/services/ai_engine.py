import logging
from typing import Optional, List
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
import numpy as np
import shap

logger = logging.getLogger(__name__)

# Daftar SMARTS patterns untuk fitur RDKit
SMARTS_PATTERNS = {
    "Phenol group": "c1ccccc1O",
    "Acetamide / Amide group": "C(=O)N",
    "Carboxylic acid group": "C(=O)O",
    "Sulfonamide group": "S(=O)(=O)N",
    "Beta-lactam ring": "C1C(=O)NC1",
    "Primary amine": "[NX3;H2,H3]",
    "Nitro group": "N(=O)=O",
    "Thiazole ring": "c1scnc1",
    "Piperazine": "C1CNCCN1"
}

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
        
    # Ekstraksi Structural Features via SMARTS
    struct_features = []
    for name, smarts in SMARTS_PATTERNS.items():
        pat = Chem.MolFromSmarts(smarts)
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
        
        num_struct_features = len(SMARTS_PATTERNS)
        self.model = HybridGNN(num_struct_features=num_struct_features).to(self.device)
        if self.model_path:
            try:
                self.model.load_state_dict(torch.load(self.model_path, map_location=self.device, weights_only=True))
                logger.info(f"Loaded weights from {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not load weights from {self.model_path}: {e}. Using random weights.")
        self.model.eval() # Set to evaluation mode
        
        logger.info(f"HybridAIEngine initialized on {self.device}. Path: {model_path}")
        self.ready = True

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
            background = np.zeros((1, len(SMARTS_PATTERNS)))
            explainer = shap.KernelExplainer(model_predict, background)
            
            # Hitung SHAP value untuk fitur molekul saat ini
            shap_values = explainer.shap_values(struct_tensor.cpu().numpy(), silent=True)
            
            # Ekstrak fitur yang paling berkontribusi positif
            contributing_features = []
            feature_names = list(SMARTS_PATTERNS.keys())
            
            # shap_values[0] adalah prediksi untuk sample pertama
            # Nilai SHAP > 0 berarti meningkatkan risiko DILI
            sv = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
            
            for i, val in enumerate(sv):
                if val > 0.001 and struct_tensor[0][i].item() == 1.0:
                    contributing_features.append(feature_names[i])
                    
            if not contributing_features:
                # Jika tidak ada atribusi kuat dari SHAP, fallback ke fitur struktural yang ada
                for i, val in enumerate(struct_tensor[0]):
                    if val.item() == 1.0:
                        contributing_features.append(feature_names[i])
                
            if not contributing_features:
                contributing_features = ["General structural features"]
                
            return contributing_features
            
        except Exception as e:
            logger.error(f"SHAP error: {e}")
            return ["Explainability evaluation error"]

    def predict_dili_risk(self, smiles: str) -> float:
        # Integrasi penuh (Sprint 1: inference asli pakai bobot PyG model)
        try:
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