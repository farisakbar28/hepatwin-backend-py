"""C9 -- kebijakan model statis: pencarian kode membuktikan tidak ada jalur
training (.backward()/optimizer.step()/torch.save()) di app/ manapun, dan
ai_engine.py memuat model dalam mode eval + no_grad."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "app"

_FORBIDDEN_PATTERNS = [
    re.compile(r"\.backward\s*\("),
    re.compile(r"optimizer\.step\s*\("),
    re.compile(r"\.step\s*\(\s*\)\s*#.*optimizer", re.IGNORECASE),
    re.compile(r"torch\.save\s*\("),
]


def _all_app_py_files() -> list[Path]:
    return [p for p in APP_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def test_no_training_calls_anywhere_in_app():
    offenders = []
    for path in _all_app_py_files():
        text = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern.search(text):
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {pattern.pattern}")
    assert not offenders, f"Ditemukan jalur training di app/ (dilarang C9): {offenders}"


def test_ai_engine_calls_model_eval():
    ai_engine_path = APP_DIR / "services" / "ai_engine.py"
    text = ai_engine_path.read_text(encoding="utf-8")
    assert ".eval()" in text, "ai_engine.py wajib memanggil model.eval() setelah load (C9)"


def test_ai_engine_wraps_inference_in_no_grad():
    ai_engine_path = APP_DIR / "services" / "ai_engine.py"
    text = ai_engine_path.read_text(encoding="utf-8")
    assert "torch.no_grad()" in text, "ai_engine.py wajib membungkus inferensi dengan torch.no_grad() (C9)"
