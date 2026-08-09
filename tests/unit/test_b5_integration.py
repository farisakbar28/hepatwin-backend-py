import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool
from app.core.database import Base
from app.models.domain import HepatwinCompound
from app.repositories.compound_repository import CompoundRepository
from app.repositories.compound_registry import ensure_registry, get_registry, reset_registry

def test_get_compound_by_hepatwin_id_success():
    mock_db = MagicMock(spec=Session)
    mock_compound = HepatwinCompound(
        hepatwin_id="HT0012",
        compound_name="Acetaminophen",
        compound_name_normalized="acetaminophen",
        is_simulatable=True,
        dili_concern="vMost-DILI-concern"
    )
    mock_db.scalars.return_value.first.return_value = mock_compound
    
    repo = CompoundRepository(mock_db)
    result = repo.get_compound_by_hepatwin_id("HT0012")
    
    assert result is not None
    assert result.hepatwin_id == "HT0012"
    assert result.compound_name == "Acetaminophen"
    assert result.is_simulatable is True

def test_get_compound_by_hepatwin_id_not_simulatable_or_not_found():
    mock_db = MagicMock(spec=Session)
    mock_db.scalars.return_value.first.return_value = None
    
    repo = CompoundRepository(mock_db)
    result = repo.get_compound_by_hepatwin_id("HT0003")
    
    assert result is None

def test_search_by_name_filter_simulatable():
    mock_db = MagicMock(spec=Session)
    mock_compound1 = HepatwinCompound(
        hepatwin_id="HT0012",
        compound_name="Acetaminophen",
        compound_name_normalized="acetaminophen",
        is_simulatable=True
    )
    mock_db.scalars.return_value.all.return_value = [mock_compound1]
    
    repo = CompoundRepository(mock_db)
    results = repo.search_by_name("aceta", limit=5)
    
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].is_simulatable is True

def test_operational_error_handling():
    mock_db = MagicMock(spec=Session)
    mock_db.scalars.side_effect = OperationalError("Connection timeout", params=None, orig=None)
    
    repo = CompoundRepository(mock_db)
    with pytest.raises(OperationalError):
        repo.get_compound_by_hepatwin_id("HT0012")


# ---------------------------------------------------------------------------
# P1 -- CompoundRegistry in-memory: fast-path tanpa DB + fallback setelah reset
# ---------------------------------------------------------------------------


def _guard_db() -> Session:
    """Session SQLAlchemy nyata (kelas 'Session', BUKAN Mock) dengan `scalars`
    yang sengaja dibuat raise -- bila fast-path registry tidak aktif, test
    langsung gagal (bukti nol akses DB saat registry termuat)."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SessionCls = sessionmaker(bind=engine)
    db = SessionCls()

    def _forbid(*args, **kwargs):
        raise AssertionError("DB dipanggil padahal registry aktif")

    db.scalars = _forbid  # type: ignore[method-assign]
    return db


@pytest.fixture
def loaded_registry():
    """Registry global diisi dari SQLite kecil (di-reset otomatis setelah test).
    Reset sebelum load supaya independen dari state test lain (mis. e2e yang
    sudah memuat registry dari seed conftest)."""
    reset_registry()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionCls = sessionmaker(bind=engine)
    db = SessionCls()
    db.add_all([
        HepatwinCompound(hepatwin_id="HT0012", compound_name="Acetaminophen", compound_name_normalized="acetaminophen", is_simulatable=True),
        HepatwinCompound(hepatwin_id="HT9000", compound_name="Acetaminophen XR", compound_name_normalized="acetaminophen xr", is_simulatable=True),
        HepatwinCompound(hepatwin_id="HT0003", compound_name="Abatacept", compound_name_normalized="abatacept", is_simulatable=False),
    ])
    db.commit()
    ensure_registry(db)
    db.close()
    yield
    reset_registry()


def test_get_by_id_served_from_registry_without_db(loaded_registry):
    """P1: dengan registry termuat, get_by_id dilayani dari memori -- DB
    (session guard) TIDAK boleh disentuh sama sekali."""
    repo = CompoundRepository(_guard_db())
    assert repo.get_by_id("HT0012").hepatwin_id == "HT0012"
    assert repo.get_by_id("HT0003") is None   # biologik -> None (filter simulatable)
    assert repo.get_by_id("NOPE") is None     # tidak ada -> None


def test_search_served_from_registry_without_db_ordering(loaded_registry):
    """P1: autocomplete dari memori -- prefix-match dulu lalu compound_name
    asc, biologik TIDAK muncul."""
    repo = CompoundRepository(_guard_db())
    res = repo.search_by_name("aceta", limit=5)
    assert [c.hepatwin_id for c in res] == ["HT0012", "HT9000"]
    assert repo.search_by_name("abatacept") == []   # biologik tidak tampil


def test_reset_registry_restores_db_fallback(loaded_registry):
    """P1: setelah reset_registry, repository kembali ke jalur DB (fallback)."""
    reset_registry()
    assert get_registry() is None

    mock_db = MagicMock(spec=Session)
    mock_db.scalars.return_value.first.return_value = None
    repo = CompoundRepository(mock_db)
    assert repo.get_by_id("HT0012") is None


def test_ensure_registry_failure_is_non_fatal():
    """P1: kegagalan load registry TIDAK boleh crash -- registry tetap None
    dan pemanggil jatuh ke fallback DB."""
    broken_db = MagicMock(spec=Session)
    broken_db.scalars.side_effect = OperationalError("Connection timeout", params=None, orig=None)

    assert ensure_registry(broken_db) is None
    assert get_registry() is None
    reset_registry()
