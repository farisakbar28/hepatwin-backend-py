from pathlib import Path

import pandas as pd


def test_data_integrity_no_overlap():
    """
    Assert nol overlap InChIKey blok-1 train ↔ external_test secara otomatis.
    
    Dasar: PRD §8.4 · AGENTS.md §7.5 · EXECUTION_PLAN.md T1.6.
    """
    processed_dir = Path("ml/data/processed")
    train_path = processed_dir / "train.csv"
    valid_path = processed_dir / "valid.csv"
    test_path = processed_dir / "external_test.csv"
    
    # Lewati jika file tidak ada di environment (misal saat fresh deployment)
    if not train_path.exists() or not test_path.exists():
        return
        
    df_train = pd.read_csv(train_path)
    df_valid = pd.read_csv(valid_path) if valid_path.exists() else pd.DataFrame(columns=["inchikey_block1"])
    df_test = pd.read_csv(test_path)
    
    train_blocks = set(df_train["inchikey_block1"].dropna())
    valid_blocks = set(df_valid["inchikey_block1"].dropna())
    test_blocks = set(df_test["inchikey_block1"].dropna())
    
    # Gabungkan training + validation set
    train_valid_blocks = train_blocks | valid_blocks
    
    # Harus nol overlap InChIKey blok-1 antara train/valid dengan external test
    overlap = train_valid_blocks & test_blocks
    assert len(overlap) == 0, f"Ditemukan overlap InChIKey blok-1 antara train/valid dengan external test: {overlap}"

def test_data_integrity_no_duplicates_internal():
    """
    Assert tidak ada inchikey_block1 duplikat dalam masing-masing file dataset.
    """
    processed_dir = Path("ml/data/processed")
    for filename in ["train.csv", "valid.csv", "external_test.csv"]:
        filepath = processed_dir / filename
        if not filepath.exists():
            continue
            
        df = pd.read_csv(filepath)
        # Cari baris yang terduplikasi secara internal berdasarkan inchikey_block1
        dup_count = df.duplicated(subset=["inchikey_block1"]).sum()
        assert dup_count == 0, f"Ditemukan {dup_count} duplikasi inchikey_block1 di dalam {filename}"
