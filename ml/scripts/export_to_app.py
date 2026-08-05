"""TU.14 -- Salin artefak model & kalibrator terpilih dari ml/models/ ke
app/models/, supaya ai_engine.py bisa memuatnya saat runtime.

Model terpilih: Arm A (`model_arm_a.pt`) -- lihat ml/reports/07_comparison.md
untuk alasan berbasis data (Arm A signifikan lebih baik dari Arm B, p<0.0001).
"""
import shutil
from pathlib import Path

SRC_DIR = Path("ml/models")
DST_DIR = Path("app/models")

FILES_TO_COPY = [
    "model_arm_a.pt",
    "calibrator_arm_a.pkl",
    "model_arm_a_metadata.json",
]


def main() -> None:
    DST_DIR.mkdir(parents=True, exist_ok=True)
    for filename in FILES_TO_COPY:
        src = SRC_DIR / filename
        if not src.exists():
            raise SystemExit(f"Artefak tidak ditemukan: {src} -- jalankan ml/scripts/train_production_model.py dulu")
        shutil.copy2(src, DST_DIR / filename)
        print(f"Disalin: {src} -> {DST_DIR / filename}")


if __name__ == "__main__":
    main()
