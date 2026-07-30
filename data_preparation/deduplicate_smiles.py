# OBSOLETE (branch upscale, UPSCALE.md v2.0): tanpa external test (K3), logika ini
# digantikan ml/src/hepatwin_ml/data/build_dataset.py. Dibiarkan ada sebagai jejak
# histori keputusan desain, tidak dipanggil oleh pipeline ml/ yang baru.
import pandas as pd
from rdkit import Chem
import argparse
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_canonical_smiles(smiles: str) -> str:
    """Mengubah SMILES menjadi Canonical SMILES menggunakan RDKit"""
    try:
        if pd.isna(smiles) or not isinstance(smiles, str):
            return None
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
    except Exception:
        return None

def deduplicate_datasets(dilirank_path: str, xu_path: str, output_path: str):
    """
    Melakukan deduplikasi dataset eksternal (Xu et al.) terhadap dataset latih (DILIrank)
    untuk mencegah data leakage semu.
    """
    logging.info(f"Membaca dataset DILIrank dari {dilirank_path}...")
    try:
        df_dilirank = pd.read_csv(dilirank_path)
    except Exception as e:
        logging.error(f"Gagal membaca dataset DILIrank: {e}")
        return

    logging.info(f"Membaca dataset Xu et al. dari {xu_path}...")
    try:
        df_xu = pd.read_csv(xu_path)
    except Exception as e:
        logging.error(f"Gagal membaca dataset Xu et al.: {e}")
        return
        
    if 'SMILES' not in df_dilirank.columns or 'SMILES' not in df_xu.columns:
        logging.error("Kolom 'SMILES' tidak ditemukan pada salah satu atau kedua dataset.")
        return

    logging.info("Memproses Canonical SMILES untuk DILIrank...")
    df_dilirank['Canonical_SMILES'] = df_dilirank['SMILES'].apply(get_canonical_smiles)
    valid_dilirank = df_dilirank.dropna(subset=['Canonical_SMILES'])
    dilirank_smiles_set = set(valid_dilirank['Canonical_SMILES'].tolist())
    
    logging.info("Memproses Canonical SMILES untuk Xu et al...")
    df_xu['Canonical_SMILES'] = df_xu['SMILES'].apply(get_canonical_smiles)
    
    initial_xu_count = len(df_xu)
    valid_xu = df_xu.dropna(subset=['Canonical_SMILES'])
    invalid_xu_count = initial_xu_count - len(valid_xu)
    
    # Proses deduplikasi (menghapus senyawa di Xu yang sudah ada di DILIrank)
    logging.info("Melakukan deduplikasi independen...")
    df_xu_dedup = valid_xu[~valid_xu['Canonical_SMILES'].isin(dilirank_smiles_set)]
    
    overlap_count = len(valid_xu) - len(df_xu_dedup)
    
    logging.info(f"Total awal Xu et al. : {initial_xu_count}")
    logging.info(f"SMILES invalid/gagal parsing : {invalid_xu_count}")
    logging.info(f"Overlap ditemukan di DILIrank : {overlap_count}")
    logging.info(f"Tersisa untuk external test set : {len(df_xu_dedup)}")
    
    # Simpan hasil deduplikasi
    try:
        df_xu_dedup.to_csv(output_path, index=False)
        logging.info(f"Dataset external test set yang telah dideduplikasi disimpan ke: {output_path}")
    except Exception as e:
        logging.error(f"Gagal menyimpan dataset output: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deduplikasi dataset DILIrank dan Xu et al. 2015 berdasarkan Canonical SMILES")
    parser.add_argument("--dilirank", type=str, required=True, help="Path ke file CSV dataset DILIrank (training set)")
    parser.add_argument("--xu", type=str, required=True, help="Path ke file CSV dataset Xu et al. (external test set asli)")
    parser.add_argument("--output", type=str, required=True, help="Path output untuk external test set setelah deduplikasi")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dilirank):
        logging.error(f"File DILIrank tidak ditemukan: {args.dilirank}")
    elif not os.path.exists(args.xu):
        logging.error(f"File Xu et al. tidak ditemukan: {args.xu}")
    else:
        deduplicate_datasets(args.dilirank, args.xu, args.output)
