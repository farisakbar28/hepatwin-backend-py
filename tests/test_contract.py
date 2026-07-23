from app.models.schemas import SimulationRequest
from app.services.simulation_orchestrator import SimulationOrchestrator


def test_triase_visual_pattern_always_heatmap_generik():
    """
    Assert visual_pattern mode triase SELALU 'heatmap_generik' untuk berbagai SMILES.
    
    Dasar: PRD §4.2 · AGENTS.md §3.2 · EXECUTION_PLAN.md T3.2.
    Ini adalah test kontrak untuk menegakkan batas scope produk.
    """
    orchestrator = SimulationOrchestrator()
    
    # Test dengan minimal 20 SMILES beragam
    smiles_list = [
        "CCO",  # Ethanol
        "CC(=O)O",  # Acetic acid
        "C1=CC=CC=C1",  # Benzene
        "CC(=O)NC1=CC=C(O)C=C1",  # Paracetamol
        "CC1(C)SC2C(NC(=O)C(N)c3ccc(O)cc3)C(=O)N12",  # Amoxicillin
        "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21",  # Diazepam
        "CN(C)C(=N)N=C(N)N",  # Metformin
        "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",  # Ibuprofen
        r"CC1=C(C(=O)N2C(C1)CS[C@@H]2C(=O)O)NC(=O)/C(=N\OC)/c3csc(N)n3",  # Cefotaxime
        "CS(=O)(=O)C1=CC=C(C=C1)C2=C(C(=O)OC2)C3=CC=CC=C3",  # Rofecoxib
        "CC(C)N=C(N)NC(=N)NC1=CC=C(Cl)C=C1",  # Proguanil
        "COC1=CC2=C(C=C1)C(C)C(O)(C2)C3=CC=C(F)C=C3",  # Generic structure
        "O=C(O)CC(O)(CC(=O)O)C(=O)O",  # Citric acid
        "C[C@@H](CC1=CC=C(O)C=C1)N",  # Hydroxyamphetamine
        "CN1CCC[C@H]1c2cccnc2",  # Nicotine
        "CC(C)(C)NCC(O)c1ccc(O)c(CO)c1",  # Salbutamol
        "CCN(CC)CCOc1ccc(cc1)C(=C(CC)c2ccccc2)c3ccccc3",  # Tamoxifen
        "CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C",  # Testosterone
        "CN1C(=O)N(C)C(=O)C2=C1N=CN2C",  # Caffeine
        "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    ]
    
    for smiles in smiles_list:
        req = SimulationRequest(
            mode="triase_umum",
            smiles_string=smiles
        )
        response = orchestrator.handle_request(req)
        assert response.visual_pattern == "heatmap_generik", f"Visual pattern untuk {smiles} harus 'heatmap_generik', didapatkan '{response.visual_pattern}'"
        assert response.affected_zone == "Macro_Generic"
        assert response.supports_micro_zoom is False
        assert response.compound_class == "unknown_general"
