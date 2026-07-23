import logging
from typing import List

from rdkit import Chem

from app.services.predictor import get_backend

logger = logging.getLogger(__name__)

def explain_compound(mol: Chem.Mol) -> List[str]:
    """
    Hitung SHAP attribution untuk substruktur kimia yang lolos validated_library()
    menggunakan backend terpilih (saat ini Tabular DILI Backend).
    
    Mengembalikan daftar nama gugus yang paling berpengaruh positif terhadap risiko DILI
    (menyebabkan risiko naik). Jika tidak ada gugus tervalidasi yang cocok atau 
    validated_library() kosong, kembalikan list kosong sesuai larangan PRD §8.5.
    
    Dasar: PRD §8.5 · PRD §13 item #2 · EXECUTION_PLAN.md T1.14.
    """
    try:
        backend = get_backend()
        explanations = backend.explain(mol)
        
        # Saring hanya yang memiliki kontribusi positif (> 0) ke arah DILI concern.
        # Mengembalikan nama-nama gugus kimia (bukan indeks numerik).
        # Implementasi di backend_tabular sudah melakukan filtering terhadap validated_library()
        # dan menyaring hanya gugus dengan nilai kecocokan == 1.
        matched_gugus = []
        for item in explanations:
            if item["kontribusi"] > 0:
                matched_gugus.append(item["gugus"])
                
        return matched_gugus
    except Exception as e:
        logger.error(f"Gagal melakukan explainability substruktur: {e}")
        return []
