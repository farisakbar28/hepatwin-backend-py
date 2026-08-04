import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.models.domain import HepatwinCompound
from app.repositories.compound_repository import CompoundRepository

def test_get_compound_by_hepatwin_id_success():
    mock_db = MagicMock(spec=Session)
    mock_compound = HepatwinCompound(
        hepatwin_id="HT-001",
        compound_name="Acetaminophen",
        compound_name_normalized="acetaminophen",
        is_simulatable=True,
        dili_concern="Most-DILI-Concern"
    )
    mock_db.scalars.return_value.first.return_value = mock_compound
    
    repo = CompoundRepository(mock_db)
    result = repo.get_compound_by_hepatwin_id("HT-001")
    
    assert result is not None
    assert result.hepatwin_id == "HT-001"
    assert result.compound_name == "Acetaminophen"
    assert result.is_simulatable is True

def test_get_compound_by_hepatwin_id_not_simulatable_or_not_found():
    mock_db = MagicMock(spec=Session)
    mock_db.scalars.return_value.first.return_value = None
    
    repo = CompoundRepository(mock_db)
    result = repo.get_compound_by_hepatwin_id("HT-BIOLOGIC-999")
    
    assert result is None

def test_search_by_name_filter_simulatable():
    mock_db = MagicMock(spec=Session)
    mock_compound1 = HepatwinCompound(
        hepatwin_id="HT-001",
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
        repo.get_compound_by_hepatwin_id("HT-001")
