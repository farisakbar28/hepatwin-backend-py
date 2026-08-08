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
    # PILIHAN FINAL: CURATED REAL IDs dari export ground truth (BIT-EXACT)
    compounds = [
        HepatwinCompound(
            hepatwin_id="HT0012", ltkb_id="LT00004", cid=1983,
            compound_name="Acetaminophen", compound_name_normalized="acetaminophen",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CC(=O)NC1=CC=C(C=C1)O", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0611", ltkb_id="LT00199", cid=3672,
            compound_name="Ibuprofen", compound_name_normalized="ibuprofen",
            dili_concern="vLess-DILI-concern", is_simulatable=True,
            canonical_smiles="CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0066", ltkb_id="LT00507", cid=33613,
            compound_name="Amoxicillin", compound_name_normalized="amoxicillin",
            dili_concern="vLess-DILI-concern", is_simulatable=True,
            canonical_smiles="CC1(C(N2C(S1)C(C2=O)NC(=O)C(C3=CC=C(C=C3)O)N)C(=O)O)C", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0647", ltkb_id="LT00306", cid=3767,
            compound_name="Isoniazid", compound_name_normalized="isoniazid",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="C1=CN=CC=C1C(=O)NN", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0695", ltkb_id="LT01488", cid=149096,
            compound_name="Levofloxacin", compound_name_normalized="levofloxacin",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CC1COC2=C3N1C=C(C(=O)C3=CC(=C2N4CCN(CC4)C)F)C(=O)O", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT1291", ltkb_id="LT00160", cid=3121,
            compound_name="Valproic acid", compound_name_normalized="valproic acid",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CCCC(CCC)C(=O)O", injury_pattern="Fallback_Diffuse",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0977", ltkb_id="LT00032", cid=1775,
            compound_name="Phenytoin", compound_name_normalized="phenytoin",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="C1=CC=C(C=C1)C2(C(=O)NC(=O)N2)C3=CC=CC=C3", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0190", ltkb_id="LT00060", cid=2554,
            compound_name="Carbamazepine", compound_name_normalized="carbamazepine",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="C1=CC=C2C(=C1)C=CC3=CC=CC=C3N2C(=O)N", injury_pattern="Mixed",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0112", ltkb_id="LT00265", cid=447043,
            compound_name="Azithromycin", compound_name_normalized="azithromycin",
            dili_concern="vLess-DILI-concern", is_simulatable=True,
            canonical_smiles="CCC1C(C(C(N(CC(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)C)O)(C)O", injury_pattern="Cholestatic",
            segment_list="II;III;IV"
        ),
        HepatwinCompound(
            hepatwin_id="HT0664", ltkb_id="LT00111", cid=47576,
            compound_name="Ketoconazole", compound_name_normalized="ketoconazole",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CC(=O)N1CCN(CC1)C2=CC=C(C=C2)OCC3COC(O3)(CN4C=CN=C4)C5=C(C=C(C=C5)Cl)Cl", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT1072", ltkb_id="LT00034", cid=135398735,
            compound_name="Rifampin", compound_name_normalized="rifampin",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CC1C=CC=C(C(=O)NC2=C(C(=C3C(=C2O)C(=C(C4=C3C(=O)C(O4)(OC=CC(C(C(C(C(C(C1O)C)O)C)OC(=O)C)C)OC)C)C)O)O)C=NN5CCN(CC5)C)C", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0868", ltkb_id="LT00125", cid=6604200,
            compound_name="Nitrofurantoin", compound_name_normalized="nitrofurantoin",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="C1C(=O)NC(=O)N1N=CC2=CC=C(O2)[N+](=O)[O-]", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0393", ltkb_id="LT00393", cid=54671203,
            compound_name="Doxycycline", compound_name_normalized="doxycycline",
            dili_concern="vLess-DILI-concern", is_simulatable=True,
            canonical_smiles="CC1C2C(C3C(C(=O)C(=C(C3(C(=O)C2=C(C4=C1C=CC=C4O)O)O)O)C(=O)N)N(C)C)O", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0775", ltkb_id="LT00026", cid=11329481,
            compound_name="Methotrexate sodium", compound_name_normalized="methotrexate",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)NC(CCC(=O)[O-])C(=O)[O-].[Na+].[Na+]", injury_pattern="Fallback_Diffuse",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0444", ltkb_id="LT00092", cid=441371,
            compound_name="Erythromycin estolate", compound_name_normalized="erythromycin estolate",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CCCCCCCCCCCCOS(=O)(=O)O.CCC1C(C(C(C(=O)C(CC(C(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)OC(=O)CC)(C)O)C)C)O)(C)O", injury_pattern="Fallback_Diffuse",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0806", ltkb_id="LT00416", cid=54685925,
            compound_name="Minocycline hydrochloride", compound_name_normalized="minocycline",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CN(C)C1C2CC3CC4=C(C=CC(=C4C(=C3C(=O)C2(C(=C(C1=O)C(=O)N)O)O)O)O)N(C)C.Cl", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0060", ltkb_id="LT00046", cid=441325,
            compound_name="Amiodarone hydrochloride", compound_name_normalized="amiodarone",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="CCCCC1=C(C2=CC=CC=C2O1)C(=O)C3=CC(=C(C(=C3)I)OCCN(CC)CC)I.Cl", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0255", ltkb_id="LT00178", cid=62998,
            compound_name="Ciprofloxacin hydrochloride", compound_name_normalized="ciprofloxacin",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O.O.Cl", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0359", ltkb_id="LT00084", cid=5018304,
            compound_name="Diclofenac sodium", compound_name_normalized="diclofenac",
            dili_concern="vMost-DILI-concern", is_simulatable=True,
            canonical_smiles="C1=CC=C(C(=C1)CC(=O)[O-])NC2=C(C=CC=C2Cl)Cl.[Na+]", injury_pattern="Hepatocellular",
            segment_list="V;VI;VII;VIII"
        ),
        HepatwinCompound(
            hepatwin_id="HT0433", ltkb_id="LT01316", cid=92043599,
            compound_name="Epoetin alfa", compound_name_normalized="epoetin alfa",
            dili_concern="vNo-DILI-concern", is_simulatable=True,
            canonical_smiles="CC1CC=CC=CC(C(CC(C(C(C(CC(=O)O1)O)OC)OC2C(C(C(C(O2)C)OC3CC(C(C(O3)C)O)(C)O)N(C)C)O)CCO)C)OC4CC(C(C(O4)C)O)(C)O", injury_pattern="Fallback_Diffuse",
            segment_list="I;II;III;IV;V;VI;VII;VIII"
        ),

        # --- C11: senyawa sintetis untuk edge case ---
        HepatwinCompound(
            hepatwin_id="HT-C11-INVALID-SMILES", ltkb_id="LTKB-C11-01",
            compound_name="C11 Test Invalid SMILES", compound_name_normalized="c11 test invalid smiles",
            dili_concern="vLess-DILI-concern", is_simulatable=True,
            canonical_smiles="INVALID_NOT_A_REAL_SMILES_XYZ123", injury_pattern="Mixed",
            segment_list="I;II"
        ),
        HepatwinCompound(
            hepatwin_id="HT-C11-SALT", ltkb_id="LTKB-C11-02",
            compound_name="C11 Test Salt Compound", compound_name_normalized="c11 test salt compound",
            dili_concern="vLess-DILI-concern", is_simulatable=True,
            canonical_smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O.[Na+]", injury_pattern="Mixed",
            segment_list="I;II"
        ),

        # --- BIOLOGICS (is_simulatable = False) ---
        HepatwinCompound(
            hepatwin_id="HT0003", ltkb_id="LT01402",
            compound_name="Abatacept", compound_name_normalized="abatacept",
            dili_concern="vLess-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0004", ltkb_id="LT01330",
            compound_name="Abciximab", compound_name_normalized="abciximab",
            dili_concern="vNo-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0019", ltkb_id="LT01387",
            compound_name="Adalimumab", compound_name_normalized="adalimumab",
            dili_concern="vLess-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0023", ltkb_id="LT02385",
            compound_name="Agalsidase beta", compound_name_normalized="agalsidase beta",
            dili_concern="vNo-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0029", ltkb_id="LT01319",
            compound_name="Aldesleukin", compound_name_normalized="aldesleukin",
            dili_concern="Ambiguous-DILI-concern", is_simulatable=False,
            injury_pattern="Cholestatic", segment_list="II;III;IV"
        ),
        HepatwinCompound(
            hepatwin_id="HT0031", ltkb_id="LT01364",
            compound_name="Alemtuzumab", compound_name_normalized="alemtuzumab",
            dili_concern="vLess-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0035", ltkb_id="LT01404",
            compound_name="Alglucosidase alfa", compound_name_normalized="alglucosidase alfa",
            dili_concern="vNo-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0044", ltkb_id="LT01315",
            compound_name="Alteplase", compound_name_normalized="alteplase",
            dili_concern="vNo-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0072", ltkb_id="LT01373",
            compound_name="Anakinra", compound_name_normalized="anakinra",
            dili_concern="vLess-DILI-concern", is_simulatable=False
        ),
        # (25) Bevacizumab - HT0143
        HepatwinCompound(
            hepatwin_id="HT0143", ltkb_id="LT01390",
            compound_name="Bevacizumab", compound_name_normalized="bevacizumab",
            dili_concern="vNo-DILI-concern", is_simulatable=False
        ),
        # (26) Trastuzumab - HT1252
        HepatwinCompound(
            hepatwin_id="HT1252", ltkb_id="LT01352",
            compound_name="Trastuzumab", compound_name_normalized="trastuzumab",
            dili_concern="vLess-DILI-concern", is_simulatable=False
        ),
        HepatwinCompound(
            hepatwin_id="HT0076", ltkb_id="LT01442",
            compound_name="Antithymocyte globulin", compound_name_normalized="antithymocyte globulin",
            dili_concern="Ambiguous-DILI-concern", is_simulatable=False
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
