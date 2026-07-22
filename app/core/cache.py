"""Cache key-value berbasis SQLite (audit TA.6, EXECUTION_PLAN.md T0.4).
Dasar: Arsitektur §E.5.

Catatan cakupan: modul ini BERDIRI SENDIRI. Belum diintegrasikan ke
`simulation_orchestrator.py` / endpoint `/simulate` — integrasi butuh nilai
`engine`/`model_version` yang nyata, yang belum diputuskan (lihat
docs/AUDIT_TASKS.md TA.4 item #3, masih terbuka). Menjadwalkan wiring ini
sesuai EXECUTION_PLAN.md T1.18, bukan sekarang.
"""
import hashlib
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_connection() -> sqlite3.Connection:
    db_path = Path(settings.CACHE_DB_PATH)
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def make_key(
    engine: str,
    model_version: str,
    inchikey_block1: str,
    dose: Optional[float],
    duration: Optional[int],
) -> str:
    """Bentuk kunci cache. `model_version` WAJIB masuk komposisi (Arsitektur
    §E.5) — tanpa itu, setelah deploy model baru, cache lama akan menyajikan
    hasil model lama tanpa terdeteksi."""
    raw = f"{engine}|{model_version}|{inchikey_block1}|{dose}|{duration}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get(key: str) -> Optional[str]:
    conn = _get_connection()
    try:
        row = conn.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def set(key: str, value: str) -> None:
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()


def clear() -> None:
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM cache")
        conn.commit()
    finally:
        conn.close()
