import logging
from typing import Any, Dict, List, Protocol

from rdkit import Chem

from app.core.config import settings

logger = logging.getLogger(__name__)

class DILIBackend(Protocol):
    """Protocol / Antarmuka tunggal untuk backend model DILI (GNN & Tabular)."""
    name: str
    version: str
    
    def predict_proba(self, mol: Chem.Mol) -> float:
        """Mengembalikan probabilitas risiko DILI (0.0 - 1.0)."""
        ...
        
    def explain(self, mol: Chem.Mol) -> List[Dict[str, Any]]:
        """Mengembalikan daftar gugus kontributor beserta nilai kontribusinya."""
        ...

def get_backend() -> DILIBackend:
    """Memilih dan mengembalikan backend model yang aktif sesuai dengan setting ML_BACKEND."""
    backend_type = settings.ML_BACKEND.lower()
    
    if backend_type == "tabular":
        from app.services.backend_tabular import TabularDILIBackend
        return TabularDILIBackend()
    elif backend_type == "gnn":
        from app.services.backend_gnn import GNNDILIBackend
        return GNNDILIBackend()
    else:
        raise ValueError(
            f"Backend ML '{settings.ML_BACKEND}' tidak dikenal. "
            "Gunakan 'tabular' atau 'gnn'."
        )
