from sqlalchemy import String, Boolean, BigInteger, Float, Text, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class HepatwinCompound(Base):
    __tablename__ = "hepatwin_compounds"

    # Primary Key (1)
    hepatwin_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    # Identitas & Nomenklatur Senyawa (4)
    ltkb_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    cid: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    compound_name: Mapped[str] = mapped_column(String, nullable=False)
    compound_name_normalized: Mapped[str] = mapped_column(String, nullable=False, index=True)
    
    # DILI & Status Simulasi (3)
    dili_concern: Mapped[str | None] = mapped_column(String, nullable=True)
    is_simulatable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[str | None] = mapped_column(String, nullable=True)

    # Notasi & Deskriptor Kimia Fisikokimia PubChem (18)
    canonical_smiles: Mapped[str | None] = mapped_column(Text, nullable=True)
    isomeric_smiles: Mapped[str | None] = mapped_column(Text, nullable=True)
    inchikey: Mapped[str | None] = mapped_column(String, nullable=True)
    molecular_formula: Mapped[str | None] = mapped_column(String, nullable=True)
    molecular_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    tpsa: Mapped[float | None] = mapped_column(Float, nullable=True)
    xlogp: Mapped[float | None] = mapped_column(Float, nullable=True)



    livertox_matched: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    livertox_match_method: Mapped[str | None] = mapped_column(String, nullable=True)
    injury_pattern: Mapped[str | None] = mapped_column(String, nullable=True)
    segment_list: Mapped[str | None] = mapped_column(Text, nullable=True)
    hotspot_base_intensity: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("idx_hepatwin_cid", cid),
        Index("idx_hepatwin_compound", compound_name),
        Index("idx_hepatwin_simulatable", is_simulatable),
        Index("idx_hepatwin_dili", dili_concern),
        Index("idx_hepatwin_pattern", injury_pattern),
    )


