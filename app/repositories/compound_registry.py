"""P1 -- Registry in-memory tabel `hepatwin_compounds` (nol query DB di hot path).

Memuat SELURUH baris (termasuk biologik is_simulatable=FALSE; ~1.336 di
produksi, set kecil di test) SEKALI saat startup (lihat warm-up di
`app/main.py`), sehingga:

- lookup deterministik by hepatwin_id -> O(1) dict read, TANPA I/O DB per request;
- deteksi biologik (422) tanpa query DB tambahan (validator & detail endpoint);
- autocomplete mereplikasi deterministik query SQL lama (LIKE + ordering).

Registry adalah snapshot statik (katalog dikurasi, tidak berubah saat runtime).
Bila DB tidak terjangkau saat load, registry tetap None dan pemanggil jatuh ke
jalur DB lama (degradasi halus, bukan crash).

Thread-safety: load sekali di bawah lock (double-checked); pembacaan
(dict lookup / scan hanya-baca) aman di CPython (GIL).
"""
import logging
import threading
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import HepatwinCompound

logger = logging.getLogger(__name__)


class CompoundRegistry:
    """Snapshot in-memory seluruh baris `hepatwin_compounds`."""

    def __init__(self, compounds: List[HepatwinCompound]):
        self.by_id: Dict[str, HepatwinCompound] = {
            c.hepatwin_id: c for c in compounds
        }
        self._simulatable = [c for c in compounds if c.is_simulatable]

    @classmethod
    def from_db(cls, db: Session) -> "CompoundRegistry":
        """SELECT seluruh baris + expunge dari session supaya objek aman
        dipakai di luar konteks session (registry berumur seumur proses)."""
        stmt = select(HepatwinCompound)
        compounds = list(db.scalars(stmt).all())
        for c in compounds:
            try:
                db.expunge(c)
            except Exception:
                pass
        return cls(compounds)

    def get(self, hepatwin_id: str) -> Optional[HepatwinCompound]:
        """Senyawa apa pun (termasuk biologik) atau None bila tidak ada."""
        return self.by_id.get(hepatwin_id)

    def search(self, query: str, limit: int = 10) -> List[HepatwinCompound]:
        """Replikasi deterministik query autocomplete lama (compound_repository
        `search_by_name`): match prefix compound_name / prefix
        compound_name_normalized / substring compound_name (case-insensitive),
        HANYA senyawa is_simulatable=TRUE, diurutkan prefix-match dulu lalu
        compound_name asc, dibatasi `limit`.

        Catatan determinisme: urutan memakai sort codepoint Python -- pendekatan
        deterministik, bukan bit-exact collation Postgres (mis. penempatan
        NULL/None vs NULLS LAST, locale casing). Data kurasi/test membuat
        perbedaan tidak relevan secara praktis."""
        clean = query.strip().lower()
        if not clean:
            return []

        matches = []
        for c in self._simulatable:
            name = (c.compound_name or "").lower()
            norm = (c.compound_name_normalized or "").lower()
            if name.startswith(clean) or (norm and norm.startswith(clean)) or clean in name:
                matches.append(c)

        matches.sort(
            key=lambda c: (
                0 if (c.compound_name or "").lower().startswith(clean) else 1,
                c.compound_name or "",
            )
        )
        return matches[:limit]


_registry: Optional[CompoundRegistry] = None
_registry_lock = threading.Lock()


def get_registry() -> Optional[CompoundRegistry]:
    """Registry saat ini (None bila belum dimuat / gagal dimuat). PURE GETTER --
    tidak pernah memicu load, supaya jalur Mock/test dan fallback DB tetap aman."""
    return _registry


def ensure_registry(db: Session) -> Optional[CompoundRegistry]:
    """Load registry dari `db` bila belum ada (double-checked lock). Dipanggil
    saat startup (`app/main.py`) dan dari `clear_caches()`. Gagal load ->
    registry tetap None (fallback DB aktif), TIDAK pernah melempar."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                try:
                    _registry = CompoundRegistry.from_db(db)
                    logger.info(
                        "CompoundRegistry dimuat: %d senyawa (simulatable=%d)",
                        len(_registry.by_id), len(_registry._simulatable),
                    )
                except Exception as exc:  # noqa: BLE001 -- non-fatal, fallback DB
                    logger.warning("Gagal memuat CompoundRegistry (fallback DB aktif): %s", exc)
                    _registry = None
    return _registry


def reset_registry() -> None:
    """Kosongkan registry (dipakai test & clear_caches)."""
    global _registry
    with _registry_lock:
        _registry = None
