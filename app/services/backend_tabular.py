import logging
import os
from typing import Any, Dict, List

import shap
from rdkit import Chem

from app.chem.features import feature_names, featurize
from app.chem.smarts_library import validated_library
from app.core.config import settings

logger = logging.getLogger(__name__)

class TabularDILIBackend:
    """Implementasi DILIBackend menggunakan model tabular LightGBM."""
    name: str = "tabular"
    version: str = "hepatwin-tabular-1.0.0"
    
    def __init__(self):
        self.model_path = os.path.join(settings.ARTIFACTS_DIR, "model.joblib")
        self.meta_path = os.path.join(settings.ARTIFACTS_DIR, "model_meta.json")
        self.model = None
        self.explainer = None
        self.feature_cols = feature_names()
        self.weights_loaded = False
        
        if os.path.exists(self.model_path):
            try:
                import joblib
                self.model = joblib.load(self.model_path)
                self.weights_loaded = True
                logger.info(f"Berhasil memuat model LightGBM dari {self.model_path}")
            except Exception as e:
                logger.error(f"Gagal memuat model LightGBM dari {self.model_path}: {e}")
        else:
            logger.warning(f"File model LightGBM tidak ditemukan di {self.model_path}. Berjalan tanpa bobot terlatih.")
            
    @property
    def model_status(self) -> str:
        return "trained" if self.weights_loaded else "untrained_random_weights"

    def predict_proba(self, mol: Chem.Mol) -> float:
        if not self.weights_loaded or self.model is None:
            # Fallback ke bobot random / uniform score
            return 0.5
        try:
            x = featurize(mol).reshape(1, -1)
            # Dapatkan probabilitas kelas 1 (DILI Concern)
            prob = self.model.predict_proba(x)[0, 1]
            return float(prob)
        except Exception as e:
            logger.error(f"Error predikasi LightGBM: {e}")
            return 0.5

    def explain(self, mol: Chem.Mol) -> List[Dict[str, Any]]:
        """Interpretasi kontribusi substruktur kimia menggunakan SHAP."""
        if not self.weights_loaded or self.model is None:
            return []
            
        try:
            x = featurize(mol).reshape(1, -1)
            
            # Buat TreeExplainer jika belum ada
            if self.explainer is None:
                self.explainer = shap.TreeExplainer(self.model)
                
            shap_values = self.explainer.shap_values(x)
            # SHAP output format bisa berbeda tergantung versi LightGBM.
            # Pada binary classification LightGBM:
            # - shap_values[1] atau shap_values saja (shape: 1, n_features) untuk probabilitas/margin.
            # Dapatkan nilai SHAP untuk kelas positif.
            if isinstance(shap_values, list) and len(shap_values) > 1:
                sv = shap_values[1][0]
            else:
                sv = shap_values[0] if len(shap_values.shape) == 2 else shap_values
                
            # Filter hanya fitur berprefiks smarts:: yang lolos validated_library()
            allowed_smarts = validated_library() # dict: key -> smarts_str
            
            explanations = []
            for i, val in enumerate(sv):
                feature_name = self.feature_cols[i]
                if feature_name.startswith("smarts::"):
                    smarts_key = feature_name.split("::")[1]
                    # Hanya yang ada di validated_library
                    if smarts_key in allowed_smarts and x[0, i] == 1.0:
                        # SHAP > 0 meningkatkan risiko DILI
                        explanations.append({
                            "gugus": smarts_key,
                            "kontribusi": float(val),
                            "deskripsi": f"Keberadaan gugus {smarts_key} meningkatkan risiko DILI" if val > 0 else f"Keberadaan gugus {smarts_key} mengurangi risiko DILI"
                        })
                        
            # Urutkan berdasarkan kontribusi terbesar (magnitudo)
            explanations.sort(key=lambda item: abs(item["kontribusi"]), reverse=True)
            return explanations
            
        except Exception as e:
            logger.error(f"Error interpretasi SHAP LightGBM: {e}")
            return []
