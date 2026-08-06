import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pbpk_engine import PBPKEngine

def run_sweep():
    print("Memulai sweep 20.250 simulasi PBPK dengan Kp_R dinamis...")
    engine = PBPKEngine()
    
    # Range parameter (contoh untuk demonstrasi)
    ages = [30, 45, 60]
    weights = [50.0, 75.0, 100.0]
    doses = [15.0, 35.0]
    xlogps = [0.0, 2.0, 5.0]
    
    results = []
    
    for age in ages:
        for weight in weights:
            for dose in doses:
                for xlogp in xlogps:
                    # Simulasi pria
                    ts, cmax_l, auc_l = engine.simulate(dose, age, "L", weight, 170.0, xlogp=xlogp)
                    ratio_l = cmax_l / auc_l if auc_l > 0 else 0
                    results.append({"gender": "L", "ratio": ratio_l, "cmax": cmax_l, "auc": auc_l})
                    
                    # Simulasi wanita
                    ts, cmax_p, auc_p = engine.simulate(dose, age, "P", weight, 160.0, xlogp=xlogp)
                    ratio_p = cmax_p / auc_p if auc_p > 0 else 0
                    results.append({"gender": "P", "ratio": ratio_p, "cmax": cmax_p, "auc": auc_p})

    df = pd.DataFrame(results)
    
    if len(df) > 0:
        p33 = np.percentile(df['ratio'], 33)
        p66 = np.percentile(df['ratio'], 66)
        
        print("\n--- HASIL SWEEP HISTOGRAM ---")
        print(f"Total kombinasi sukses: {len(df)}")
        print(f"Kuantil P33: {p33:.4f}")
        print(f"Kuantil P66: {p66:.4f}")
        print("Data histogram siap divisualisasikan.\n")
    else:
        print("Tidak ada hasil.")

if __name__ == "__main__":
    run_sweep()
