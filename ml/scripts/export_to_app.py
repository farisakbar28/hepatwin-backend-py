"""C9 -- Salin artefak model GATNN-DNN + kalibrator dari ml/models/ ke
app/models/, supaya app/services/ai_engine.py (C10) bisa memuatnya saat
runtime. Penyalinan TERKONTROL (skrip ini), bukan manual -- EXECUTION_PLAN_FIX_MODEL.md
C9 langkah 2.

Model lama (bila ada) TIDAK ditimpa -- nama file baru (`model_gatnn_dnn.pt`,
bukan `model.pt`) sengaja beda supaya bisa dibandingkan (C9 AC).
"""
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "ml" / "models"
DST_DIR = REPO_ROOT / "app" / "models"

FILES_TO_COPY = [
    "model_gatnn_dnn.pt",
    "calibrator_gatnn_dnn.pkl",
    "model_gatnn_dnn_metadata.json",
]


def main() -> None:
    DST_DIR.mkdir(parents=True, exist_ok=True)
    for filename in FILES_TO_COPY:
        src = SRC_DIR / filename
        if not src.exists():
            raise SystemExit(
                f"Artefak tidak ditemukan: {src} -- jalankan ml/scripts/run_train.py "
                "dan ml/scripts/run_evaluate.py dulu (menghasilkan model + kalibrator)."
            )
        dst = DST_DIR / filename
        shutil.copy2(src, dst)
        print(f"Disalin: {src} -> {dst}")


if __name__ == "__main__":
    main()
