import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import SessionLocal
from app.services.lookup_service import CompoundRepository
from app.services.pbpk_engine import PBPKEngine
from app.services.ai_engine import HybridAIEngine

def test_backend_components():
    print("--- TESTING DATABASE CONNECTION & REPOSITORY ---")
    db = SessionLocal()
    try:
        repo = CompoundRepository(db)
        results = repo.search_autocomplete("para", limit=5)
        print(f"Autocomplete 'para' found {len(results)} items:")
        for r in results:
            print(f"  - [{r.hepatwin_id}] {r.compound_name} (Simulatable: {r.is_simulatable})")
            
        if results:
            first_id = results[0].hepatwin_id
            detail = repo.get_by_id(first_id)
            if detail:
                print(f"\nLookup detail '{first_id}':")
                print(f"  Name: {detail.compound_name}")
                print(f"  SMILES: {detail.canonical_smiles}")
                print(f"  Injury Pattern: {detail.injury_pattern}")
                print(f"  Segments: {detail.segment_list}")
            else:
                print(f"Failed to lookup detail for {first_id}")
    except Exception as e:
        print(f"DB Test Error: {e}")
    finally:
        db.close()

    print("\n--- TESTING PBPK ENGINE (SciPy ODE + Alometrik) ---")
    pbpk = PBPKEngine()
    ts, cmax, auc = pbpk.simulate(
        dosis_mg=1000.0,
        usia=45,
        jenis_kelamin="L",
        berat_badan_kg=70.0,
        tinggi_badan_cm=170.0
    )
    print(f"PBPK Simulation finished. Cmax_hati: {cmax} mg/L, AUC_hati: {auc}. Data points: {len(ts)}")

    print("\n--- TESTING AI ENGINE (GATNN-DNN + SHAP) ---")
    ai = HybridAIEngine()
    smiles_paracetamol = "CC(=O)NC1=CC=C(O)C=C1"
    score = ai.predict_dili_risk(smiles_paracetamol)
    shap_attr = ai.get_explainability(smiles_paracetamol)
    print(f"AI DILI Score for Paracetamol: {score}")
    print(f"SHAP Toxicophore Highlights: {shap_attr}")

if __name__ == "__main__":
    test_backend_components()
