"""
Legacy wrapper untuk memelihara kompatibilitas impor dengan `app.repositories.compound_repository`.
"""
from app.repositories.compound_repository import CompoundRepository, _cached_search_ids

__all__ = ["CompoundRepository", "_cached_search_ids"]

