import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
try:
    from app.main import app
    from app.core.database import get_db, Base
    from app.models.domain import HepatwinCompound
    APP_IMPORTED = True
except ImportError:
    APP_IMPORTED = False

# Setup In-Memory SQLite untuk E2E tests (real DB engine, bukan Mock)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database(db: Session):
    compounds = [
        HepatwinCompound(
            hepatwin_id="HT-001", ltkb_id="LTKB-001", cid=1983,
            compound_name="Acetaminophen", compound_name_normalized="acetaminophen",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC(=O)NC1=CC=C(O)C=C1", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-002", ltkb_id="LTKB-002", cid=3672,
            compound_name="Ibuprofen", compound_name_normalized="ibuprofen",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-003", ltkb_id="LTKB-003", cid=33613,
            compound_name="Amoxicillin", compound_name_normalized="amoxicillin",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC1(C(N2C(S1)C(C2=O)NC(=O)C(C3=CC=C(C=C3)O)N)C(=O)O)C", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-004", ltkb_id="LTKB-004", cid=3767,
            compound_name="Isoniazid", compound_name_normalized="isoniazid",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="C1=CN=CC=C1C(=O)NN", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-005", ltkb_id="LTKB-005", cid=149096,
            compound_name="Levofloxacin", compound_name_normalized="levofloxacin",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC1COC2=C3N1C=C(C(=O)C3=CC(=C2F)N4CCN(CC4)C)C(=O)O", injury_pattern="Cholestatic",
            segment_list="II;III;IV"
        ),
        HepatwinCompound(
            hepatwin_id="HT-006", ltkb_id="LTKB-006", cid=2764,
            compound_name="Ciprofloxacin", compound_name_normalized="ciprofloxacin",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O", injury_pattern="Cholestatic",
            segment_list="II;III;IV"
        ),
        HepatwinCompound(
            hepatwin_id="HT-007", ltkb_id="LTKB-007", cid=3121,
            compound_name="Valproic Acid", compound_name_normalized="valproic acid",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CCCC(CCC)C(=O)O", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-008", ltkb_id="LTKB-008", cid=3562,
            compound_name="Halothane", compound_name_normalized="halothane",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="C(C(F)(F)F)(Cl)Br", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-009", ltkb_id="LTKB-009", cid=3033,
            compound_name="Diclofenac", compound_name_normalized="diclofenac",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="C1=CC=C(C(=C1)CC(=O)O)NC2=C(C=CC=C2Cl)Cl", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-010", ltkb_id="LTKB-010", cid=1775,
            compound_name="Phenytoin", compound_name_normalized="phenytoin",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="C1=CC=C(C=C1)C2(C(=O)NC(=O)N2)C3=CC=C(C=C3)", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-011", ltkb_id="LTKB-011", cid=2554,
            compound_name="Carbamazepine", compound_name_normalized="carbamazepine",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="C1=CC=C2C(=C1)C=CC3=CC=CC=C3N2C(=O)N", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-012", ltkb_id="LTKB-012", cid=447043,
            compound_name="Azithromycin", compound_name_normalized="azithromycin",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="CCC1C(C(C(N(CC(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)C)O)(C)O", injury_pattern="Cholestatic",
            segment_list="II;III;IV"
        ),
        HepatwinCompound(
            hepatwin_id="HT-013", ltkb_id="LTKB-013", cid=2162,
            compound_name="Amiodarone", compound_name_normalized="amiodarone",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CCCCC1=C(C2=CC=CC=C2O1)C(=O)C3=CC(=C(C(=C3)I)OCCN(CC)CC)I", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-014", ltkb_id="LTKB-014", cid=3823,
            compound_name="Ketoconazole", compound_name_normalized="ketoconazole",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC(=O)N1CCC(CC1)N2C=CC(=C2)OCC3COC(O3)(CN4C=CN=C4)C5=C(C=C(C=C5)Cl)Cl", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-015", ltkb_id="LTKB-015", cid=4112,
            compound_name="Methotrexate", compound_name_normalized="methotrexate",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)NC(CCC(=O)O)C(=O)O", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-016", ltkb_id="LTKB-016", cid=135398738,
            compound_name="Rifampin", compound_name_normalized="rifampin",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC1C=CC=C(C(=O)NC2=C(C(=C3C(=C2O)C(=C(C4=C3C(=O)C(O4)(OC=C1C(C(C(C(C(C(C)O)(C)O)C)OC(=O)C)C)OC)C)C)O)C=NNC5CCN(CC5)C)C", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-017", ltkb_id="LTKB-017", cid=12560,
            compound_name="Erythromycin", compound_name_normalized="erythromycin",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="CCC1C(C(C(C(=O)C(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)O)(C)O", injury_pattern="Cholestatic",
            segment_list="II;III;IV"
        ),
        HepatwinCompound(
            hepatwin_id="HT-018", ltkb_id="LTKB-018", cid=54675776,
            compound_name="Tetracycline", compound_name_normalized="tetracycline",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC1(C2CC3C(C(=O)C(=C(C3(C(=O)C2=C(C4=C1C=CC=C4O)O)O)O)C(=O)N)N(C)C)O", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-019", ltkb_id="LTKB-019", cid=6604200,
            compound_name="Nitrofurantoin", compound_name_normalized="nitrofurantoin",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="C1=C(OC(=C1)C=NNC2=O)C(=O)N(C2=O)C", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT-020", ltkb_id="LTKB-020", cid=54675783,
            compound_name="Minocycline", compound_name_normalized="minocycline",
            dili_concern="Most-DILI-Concern", is_simulatable=True,
            canonical_smiles="CN(C)C1=C(C=CC2=C1C(C3CC4C(C(=O)C(=C(C4(C(=O)C3=C2O)O)O)C(=O)N)N(C)C)O)O", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        # --- C11: senyawa sintetis untuk edge case (bukan data DILIrank nyata,
        # tidak pernah terjadi di 1231 simulatable asli -- C2 sudah
        # memverifikasi 0 gagal parse di korpus nyata). Murni menguji jalur
        # defensif ai_engine.py saat data tidak terduga sampai ke sana. ---
        HepatwinCompound(
            hepatwin_id="HT-C11-INVALID-SMILES", ltkb_id="LTKB-C11-01",
            compound_name="C11 Test Invalid SMILES", compound_name_normalized="c11 test invalid smiles",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="INVALID_NOT_A_REAL_SMILES_XYZ123", injury_pattern="Mixed",
            segment_list="I;II"
        ),
        HepatwinCompound(
            hepatwin_id="HT-C11-SALT", ltkb_id="LTKB-C11-02",
            compound_name="C11 Test Salt Compound", compound_name_normalized="c11 test salt compound",
            dili_concern="Less-DILI-Concern", is_simulatable=True,
            canonical_smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O.[Na+]", injury_pattern="Mixed",
            segment_list="I;II"
        ),
        # --- F8: fixture khusus utk test_d9_fusion_e2e.py ---
        # Pola cedera & intensitas hotspot memakai label Indonesia (sesuai data
        # Supabase nyata, F4) -- BEDA sengaja dari HT-001..HT-020 di atas yang
        # memakai label Inggris lama (diverifikasi tests/e2e/test_b7_lookup_e2e.py
        # sudah menguncinya, TIDAK diubah di sini utk menghindari regresi).
        HepatwinCompound(
            hepatwin_id="HT-HEPATOSELULER-TEST", ltkb_id="LTKB-F8-01", cid=1983,
            compound_name="F8 Test Hepatoseluler", compound_name_normalized="f8 test hepatoseluler",
            dili_concern="Most-DILI-concern", is_simulatable=True,
            canonical_smiles="CC(=O)NC1=CC=C(O)C=C1", injury_pattern="Hepatoseluler",
            segment_list="V;VI;VII;VIII", hotspot_base_intensity="high", hotspot_display_mode="focal",
        ),
        HepatwinCompound(
            hepatwin_id="HT-UNCLASSIFIED-SAME-SMILES", ltkb_id="LTKB-F8-02", cid=1983,
            compound_name="F8 Test Unclassified (SMILES identik dgn HT-HEPATOSELULER-TEST)",
            compound_name_normalized="f8 test unclassified",
            dili_concern="Most-DILI-concern", is_simulatable=True,
            # SMILES SENGAJA SAMA dgn HT-HEPATOSELULER-TEST -- dili_score dijamin
            # identik (model deterministik), sehingga AI band & visual_color
            # HARUS sama; hanya hotspot_intensity/mode yang beda (test #9 F8).
            canonical_smiles="CC(=O)NC1=CC=C(O)C=C1", injury_pattern="Tidak Terklasifikasi",
            segment_list=None, hotspot_base_intensity=None, hotspot_display_mode=None,
        ),
        HepatwinCompound(
            hepatwin_id="HT-VNO-SAFE-TEST", ltkb_id="LTKB-F8-03", cid=1080,
            compound_name="F8 Test vNo Safe (Calcitonin salmon, skor terendah katalog nyata)",
            compound_name_normalized="f8 test vno safe",
            dili_concern="No-DILI-concern", is_simulatable=True,
            # SMILES nyata Calcitonin salmon (HT0178 Supabase) -- skor terendah
            # terukur di seluruh katalog 1.231 senyawa (F1: 0.5078), dipakai
            # utk membuktikan band AI_LOW benar-benar tercapai pada senyawa asli.
            canonical_smiles=(
                "CC(C)CC1C(=O)NC(C(=O)NC(C(=O)NC(CSSCC(C(=O)NC(C(=O)NC(C(=O)N1)CC(=O)N)CO)N)"
                "C(=O)NC(C(C)C)C(=O)NC(CC(C)C)C(=O)NCC(=O)NC(CCCCN)C(=O)NC(CC(C)C)C(=O)NC(CO)"
                "C(=O)NC(CCC(=O)N)C(=O)NC(CCC(=O)O)C(=O)NC(CC(C)C)C(=O)NC(CC2=CN=CN2)C(=O)NC(CCCCN)"
                "C(=O)NC(CC(C)C)C(=O)NC(CCC(=O)N)C(=O)NC(C(C)O)C(=O)NC(CC3=CC=C(C=C3)O)"
                "C(=O)N4CCCC4C(=O)NC(CCCNC(=N)N)C(=O)NC(C(C)O)C(=O)NC(CC(=O)N)C(=O)NC(C(C)O)"
                "C(=O)NCC(=O)NC(CO)C(=O)NCC(=O)NC(C(C)O)C(=O)N5CCCC5C(=O)N)C(C)O)CO"
            ),
            injury_pattern="Tidak Terklasifikasi", segment_list=None,
            hotspot_base_intensity=None, hotspot_display_mode=None,
        ),
        # --- BIOLOGICS (is_simulatable = False) ---
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-001", ltkb_id="LTKB-B001",
            compound_name="Infliximab", compound_name_normalized="infliximab",
            dili_concern="Less-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-002", ltkb_id="LTKB-B002",
            compound_name="Rituximab", compound_name_normalized="rituximab",
            dili_concern="Less-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-003", ltkb_id="LTKB-B003",
            compound_name="Adalimumab", compound_name_normalized="adalimumab",
            dili_concern="Less-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-004", ltkb_id="LTKB-B004",
            compound_name="Epoetin alfa", compound_name_normalized="epoetin alfa",
            dili_concern="No-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-005", ltkb_id="LTKB-B005",
            compound_name="Insulin human", compound_name_normalized="insulin human",
            dili_concern="No-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-006", ltkb_id="LTKB-B006",
            compound_name="Trastuzumab", compound_name_normalized="trastuzumab",
            dili_concern="Less-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-007", ltkb_id="LTKB-B007",
            compound_name="Bevacizumab", compound_name_normalized="bevacizumab",
            dili_concern="Less-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-008", ltkb_id="LTKB-B008",
            compound_name="Pembrolizumab", compound_name_normalized="pembrolizumab",
            dili_concern="Less-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-009", ltkb_id="LTKB-B009",
            compound_name="Etanercept", compound_name_normalized="etanercept",
            dili_concern="Less-DILI-Concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT-BIOLOGIC-010", ltkb_id="LTKB-B010",
            compound_name="Daratumumab", compound_name_normalized="daratumumab",
            dili_concern="No-DILI-Concern", is_simulatable=False
        )
    ]
    db.add_all(compounds)
    db.commit()

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    if not APP_IMPORTED:
        yield
        return
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()
    
    # Patch SessionLocal secara global di app.core.database
    import app.core.database as db_module
    original_session_local = db_module.SessionLocal
    db_module.SessionLocal = TestingSessionLocal
    
    from app.repositories.compound_repository import clear_caches
    clear_caches()
    
    yield
    
    # Revert patch
    db_module.SessionLocal = original_session_local
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

if APP_IMPORTED:
    # Override dependency FastAPI agar menggunakan SQLite memory saat test
    app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client() -> TestClient:
    """Returns a FastAPI TestClient."""
    if not APP_IMPORTED:
        pytest.skip("FastAPI app or Supabase not available")
    with TestClient(app) as c:
        yield c
