import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pbpk_engine import PBPKEngine

def run_sweep_full():
    print("Memulai sweep ~17.550 simulasi PBPK dengan Kp_R dinamis (PRD v2.1)...")
    engine = PBPKEngine()

    ages = list(range(18, 91, 3))  # 25
    bmis = list(range(16, 42, 2))  # 13
    doses_mg_per_kg = [0.5, 2, 5, 10, 15, 20, 30, 40, 50]  # 9
    xlogps = [0.0, 2.0, 5.0]  # 3
    heights = {"L": 170.0, "P": 160.0}

    results = []
    for age in ages:
        for bmi in bmis:
            for dose_mg_per_kg in doses_mg_per_kg:
                for xlogp in xlogps:
                    for gender in ["L", "P"]:
                        height = heights[gender]
                        weight = bmi * (height/100)**2
                        dose_mg = dose_mg_per_kg * weight
                        try:
                            ts, cmax, auc = engine.simulate(dose_mg, age, gender, weight, height, xlogp=xlogp)
                        except TypeError:
                            # fallback jika signature beda: simulate(dose, age, gender, weight, height, xlogp)
                            ts, cmax, auc = engine.simulate(dose_mg, age, gender, weight, height, xlogp)
                        ratio = cmax / auc if auc and auc > 0 else 0
                        results.append({"age":age,"bmi":bmi,"dose_mg_per_kg":dose_mg_per_kg,"gender":gender,"xlogp":xlogp,"ratio":ratio,"cmax":cmax,"auc":auc})

    df = pd.DataFrame(results)
    print(f"Total kombinasi sukses: {len(df)}")

    if len(df) > 0:
        p33 = np.percentile(df['ratio'], 33)
        p50 = np.percentile(df['ratio'], 50)
        p66 = np.percentile(df['ratio'], 66)
        print(f"\n--- HASIL SWEEP HISTOGRAM ---")
        print(f"Kuantil P33: {p33:.4f}")
        print(f"Kuantil P50: {p50:.4f}")
        print(f"Kuantil P66: {p66:.4f}")
        print(f"Min {df['ratio'].min():.4f} Max {df['ratio'].max():.4f}")
        print(f"LOW {(df['ratio']<p33).sum()} MOD {((df['ratio']>=p33)&(df['ratio']<p66)).sum()} HIGH {(df['ratio']>=p66).sum()}")

        os.makedirs("reports", exist_ok=True)
        df.to_csv("reports/F2_exposure_reachability_v2_KpR.csv", index=False)
        print("CSV: reports/F2_exposure_reachability_v2_KpR.csv")

        # Histogram tanpa matplotlib — pakai numpy histogram print
        hist, bins = np.histogram(df['ratio'], bins=10)
        print("\nHistogram (10 bins):")
        for i in range(len(hist)):
            print(f"  {bins[i]:.3f} - {bins[i+1]:.3f} : {hist[i]}")

        with open("reports/F2_exposure_reachability_v2_KpR.md","w",encoding="utf-8") as f:
            f.write(f"# Sweep PBPK {len(df)} — Kp_R Dinamis\n\nP33={p33:.4f} P50={p50:.4f} P66={p66:.4f}\n\nLOW {(df['ratio']<p33).sum()} MOD {((df['ratio']>=p33)&(df['ratio']<p66)).sum()} HIGH {(df['ratio']>=p66).sum()}\n")
        print("MD: reports/F2_exposure_reachability_v2_KpR.md")
        print(f"\nKANDIDAT K3:\n  low_ratio_max = {p33:.4f}\n  mod_ratio_max = {p66:.4f}")
    else:
        print("Tidak ada hasil.")

if __name__ == "__main__":
    run_sweep_full()
