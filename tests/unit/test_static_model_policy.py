"""C9 -- kebijakan model statis: pencarian kode membuktikan tidak ada jalur
training (.backward()/optimizer.step()/torch.save()) di app/ manapun, dan
ai_engine.py memuat model dalam mode eval + no_grad.

Dicek lewat AST (bukan regex atas teks mentah) -- regex atas teks akan
salah tangkap saat docstring/komentar MENYEBUT nama pola ini secara sengaja
untuk mendokumentasikan kebijakan (persis yang terjadi di ai_engine.py C10)."""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "app"


def _all_app_py_files() -> list[Path]:
    return [p for p in APP_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def _forbidden_calls_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    offenders = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        attr = node.func.attr
        target = ast.unparse(node.func.value)
        if attr == "backward":
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}: {target}.backward()")
        elif attr == "step" and "optim" in target.lower():
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}: {target}.step()")
        elif attr == "save" and target == "torch":
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}: torch.save()")
    return offenders


def test_no_training_calls_anywhere_in_app():
    offenders = []
    for path in _all_app_py_files():
        offenders.extend(_forbidden_calls_in_file(path))
    assert not offenders, f"Ditemukan jalur training di app/ (dilarang C9): {offenders}"


def test_ai_engine_calls_model_eval():
    ai_engine_path = APP_DIR / "services" / "ai_engine.py"
    text = ai_engine_path.read_text(encoding="utf-8")
    assert ".eval()" in text, "ai_engine.py wajib memanggil model.eval() setelah load (C9)"


def test_ai_engine_wraps_inference_in_no_grad():
    ai_engine_path = APP_DIR / "services" / "ai_engine.py"
    text = ai_engine_path.read_text(encoding="utf-8")
    assert "torch.no_grad()" in text, "ai_engine.py wajib membungkus inferensi dengan torch.no_grad() (C9)"
