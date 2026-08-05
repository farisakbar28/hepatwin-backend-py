"""Model SQLAlchemy untuk tabel `public.hepatwin_compounds` (Supabase).

Direkonstruksi karena file ini hilang dari seluruh riwayat git (tidak pernah
ter-commit di `master` maupun `fix-model`), padahal diimpor oleh
`compound_repository.py`, `simulation_orchestrator.py`, `compound_validator.py`,
dan `api/endpoints/compounds.py` -- tanpa file ini backend tidak bisa di-import
sama sekali. Skema 42 kolom di bawah diverifikasi lewat query langsung ke
Supabase (anon key, `SELECT *` satu baris), bukan ditebak dari kode pemanggil.

Catatan: `CompoundDetail` (app/models/schemas.py) dan
`api/endpoints/compounds.py` mengakses beberapa atribut deskriptor PubChem
(`iupac_name`, `heavy_atom_count`, `hydrogen_bond_donor_count`, dst.) yang
TIDAK ada di skema tabel nyata -- itu bug pra-eksisting di luar cakupan Alur
Kerja C, dicatat di `ml/reports/backlog.md`, TIDAK ditambahkan di sini sebagai
kolom karangan (menambah kolom yang tidak ada di tabel akan membuat setiap
SELECT gagal dengan "column does not exist").
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HepatwinCompound(Base):
    __tablename__ = "hepatwin_compounds"

    hepatwin_id: Mapped[str] = mapped_column(String, primary_key=True)
    ltkb_id: Mapped[Optional[str]] = mapped_column(String)
    cid: Mapped[Optional[int]] = mapped_column(Integer)
    compound_name: Mapped[str] = mapped_column(String, nullable=False)
    compound_name_normalized: Mapped[Optional[str]] = mapped_column(String)
    pubchem_title: Mapped[Optional[str]] = mapped_column(String)

    dili_severity_class: Mapped[Optional[int]] = mapped_column(Integer)
    dili_label_section: Mapped[Optional[str]] = mapped_column(String)
    dili_concern: Mapped[Optional[str]] = mapped_column(String)
    dili_concern_source: Mapped[Optional[str]] = mapped_column(String)
    dilirank_comment: Mapped[Optional[str]] = mapped_column(String)
    verification_status: Mapped[Optional[str]] = mapped_column(String)
    is_simulatable: Mapped[bool] = mapped_column(Boolean, nullable=False)

    canonical_smiles: Mapped[Optional[str]] = mapped_column(Text)
    isomeric_smiles: Mapped[Optional[str]] = mapped_column(Text)
    inchikey: Mapped[Optional[str]] = mapped_column(String)
    molecular_formula: Mapped[Optional[str]] = mapped_column(String)
    molecular_weight: Mapped[Optional[float]] = mapped_column(Float)
    tpsa: Mapped[Optional[float]] = mapped_column(Float)
    xlogp: Mapped[Optional[float]] = mapped_column(Float)

    injury_pattern: Mapped[Optional[str]] = mapped_column(String)
    injury_pattern_source: Mapped[Optional[str]] = mapped_column(String)
    segment_list: Mapped[Optional[str]] = mapped_column(String)
    segment_count: Mapped[Optional[int]] = mapped_column(Integer)
    histologic_zone: Mapped[Optional[str]] = mapped_column(String)
    hotspot_display_mode: Mapped[Optional[str]] = mapped_column(String)
    hotspot_base_intensity: Mapped[Optional[str]] = mapped_column(String)

    livertox_matched: Mapped[Optional[bool]] = mapped_column(Boolean)
    livertox_record: Mapped[Optional[str]] = mapped_column(String)
    livertox_match_method: Mapped[Optional[str]] = mapped_column(String)
    livertox_histology: Mapped[Optional[str]] = mapped_column(Text)
    livertox_r_ratio_notes: Mapped[Optional[str]] = mapped_column(Text)
    livertox_classification_method: Mapped[Optional[str]] = mapped_column(String)
    livertox_data_source_note: Mapped[Optional[str]] = mapped_column(Text)

    threshold_available: Mapped[Optional[bool]] = mapped_column(Boolean)
    threshold_reference: Mapped[Optional[str]] = mapped_column(Text)

    data_source_dili: Mapped[Optional[str]] = mapped_column(String)
    data_source_injury: Mapped[Optional[str]] = mapped_column(String)
    data_source_descriptor: Mapped[Optional[str]] = mapped_column(String)
    reference_ids: Mapped[Optional[str]] = mapped_column(String)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
