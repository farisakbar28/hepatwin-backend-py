import json
import os

from fastapi import APIRouter, HTTPException

from app.core.config import settings

router = APIRouter()

@router.get("/model-info")
def get_model_info():
    """
    Endpoint untuk menyajikan metadata model yang saat ini dimuat oleh server backend.
    
    Dasar: PRD §8.3, §14.5 · Arsitektur §E.1 · EXECUTION_PLAN.md T1.17.
    """
    meta_path = os.path.join(settings.ARTIFACTS_DIR, "model_meta.json")
    if not os.path.exists(meta_path):
        # Jika file metadata tidak ada, kembalikan response default/kosong yang jujur
        return {
            "model_version": f"hepatwin-{settings.ML_BACKEND}-1.0.0-dev",
            "backend": settings.ML_BACKEND,
            "trained_at": None,
            "n_train": 0,
            "feature_names_hash": None,
            "metrics": None
        }
        
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membaca metadata model: {str(e)}")
