import logging
import os
from typing import Any, Dict, List

import numpy as np
import shap
import torch
from rdkit import Chem

from app.chem.smarts_library import SMARTS_LIBRARY, validated_library
from app.core.config import settings
from app.services.ai_engine import HybridGNN, smiles_to_graph_and_features

logger = logging.getLogger(__name__)

class GNNDILIBackend:
    """Implementasi DILIBackend menggunakan arsitektur Hybrid GNN (PyTorch Geometric)."""
    name: str = "gnn"
    version: str = "hepatwin-gnn-1.0.0"
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = os.path.join(settings.ARTIFACTS_DIR, "model.pt")
        num_struct_features = len(SMARTS_LIBRARY)
        self.model = HybridGNN(num_struct_features=num_struct_features).to(self.device)
        self.weights_loaded = False
        
        if os.path.exists(self.model_path):
            try:
                self.model.load_state_dict(
                    torch.load(self.model_path, map_location=self.device, weights_only=True)
                )
                self.weights_loaded = True
                logger.info(f"Berhasil memuat model GNN dari {self.model_path}")
            except Exception as e:
                logger.error(f"Gagal memuat model GNN dari {self.model_path}: {e}")
        else:
            logger.warning(f"File model GNN tidak ditemukan di {self.model_path}. Berjalan tanpa bobot terlatih.")
            
        self.model.eval()

    @property
    def model_status(self) -> str:
        return "trained" if self.weights_loaded else "untrained_random_weights"

    def predict_proba(self, mol: Chem.Mol) -> float:
        try:
            # Dapatkan SMILES dari RDKit Mol
            smiles = Chem.MolToSmiles(mol)
            data, struct_tensor = smiles_to_graph_and_features(smiles)
            if data is None or struct_tensor is None:
                return 0.5
                
            data = data.to(self.device)
            struct_tensor = struct_tensor.to(self.device)
            batch = torch.zeros(data.x.size(0), dtype=torch.long).to(self.device)
            
            with torch.no_grad():
                score = self.model(data.x, data.edge_index, batch, struct_tensor)
            return float(score.item())
        except Exception as e:
            logger.error(f"Error predikasi GNN: {e}")
            return 0.5

    def explain(self, mol: Chem.Mol) -> List[Dict[str, Any]]:
        """Interpretasi kontribusi substruktur kimia GNN via SHAP KernelExplainer."""
        if not self.weights_loaded:
            return []
            
        try:
            smiles = Chem.MolToSmiles(mol)
            data, struct_tensor = smiles_to_graph_and_features(smiles)
            if data is None or struct_tensor is None:
                return []
                
            data = data.to(self.device)
            struct_tensor = struct_tensor.to(self.device)
            batch = torch.zeros(data.x.size(0), dtype=torch.long).to(self.device)
            
            def model_predict(struct_input):
                n_samples = struct_input.shape[0]
                out_scores = []
                for i in range(n_samples):
                    struct_t = torch.tensor(struct_input[i:i+1], dtype=torch.float).to(self.device)
                    with torch.no_grad():
                        out = self.model(data.x, data.edge_index, batch, struct_t)
                    out_scores.append(out.cpu().numpy()[0])
                return np.array(out_scores)
                
            background = np.zeros((1, len(SMARTS_LIBRARY)))
            explainer = shap.KernelExplainer(model_predict, background)
            shap_values = explainer.shap_values(struct_tensor.cpu().numpy(), silent=True)
            
            sv = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
            feature_names = list(SMARTS_LIBRARY.keys())
            allowed_smarts = validated_library()
            
            explanations = []
            for i, val in enumerate(sv):
                smarts_key = feature_names[i]
                if smarts_key in allowed_smarts and struct_tensor[0][i].item() == 1.0:
                    explanations.append({
                        "gugus": smarts_key,
                        "kontribusi": float(val),
                        "deskripsi": f"Keberadaan gugus {smarts_key} meningkatkan risiko DILI" if val > 0 else f"Keberadaan gugus {smarts_key} mengurangi risiko DILI"
                    })
                    
            explanations.sort(key=lambda item: abs(item["kontribusi"]), reverse=True)
            return explanations
            
        except Exception as e:
            logger.error(f"Error interpretasi SHAP GNN: {e}")
            return []
