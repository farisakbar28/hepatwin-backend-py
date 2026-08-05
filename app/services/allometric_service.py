from typing import Dict, Any

class AllometricService:
    """
    Modul konversi kovariat pasien menjadi parameter fisiologis PBPK 4-Kompartemen.
    Seluruh konstanta telah diverifikasi oleh Anggi Fitriani (Spesialis Farmasi/Toksikologi).
    Rujukan Pustaka:
      - Brown et al. (1997) [22]: Volume hati 2.5% dari berat badan.
      - Deurenberg et al. (1991) [23]: Estimasi persentase lemak tubuh (%BF).
      - Soejima et al. (2022) [21]: Penurunan aliran darah hepatik 0.8%/tahun usia >= 40.
      - Ghabril et al. (2025) [17]: Reduksi klirens metabolisme 20% pada BMI >= 30 (MASLD).
    """
    @staticmethod
    def calculate_physiological_parameters(
        age: int,
        gender: str,
        weight_kg: float,
        height_cm: float,
        base_cl_metabolism_l_hr: float = 15.0  # Nilai default atau dari deskriptor senyawa
    ) -> Dict[str, Any]:
        if weight_kg <= 0.0 or height_cm <= 0.0:
            raise ValueError("Parameter berat dan tinggi badan harus lebih besar dari 0.")

        # 1. Indeks Massa Tubuh (BMI)
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m ** 2)

        # 2. Pemetaan Jenis Kelamin
        gender_upper = gender.strip().upper()
        if gender_upper in ["MALE", "M", "L", "LAKI-LAKI", "LAKI", "PRIA"]:
            sex_val = 1
        elif gender_upper in ["FEMALE", "F", "P", "PEREMPUAN", "WANITA"]:
            sex_val = 0
        else:
            raise ValueError("Format jenis kelamin tidak valid.")

        # 3. Persentase Lemak Tubuh (%BF - Deurenberg et al. 1991)
        body_fat_pct = max(0.0, 1.20 * bmi + 0.23 * float(age) - 10.8 * sex_val - 5.4)

        # 4. Volume Kompartemen (L) - Penskalaan proporsional berat tubuh
        v_liver = 0.025 * weight_kg       # V_L: 2.5% dari berat badan (Brown et al. 1997)
        v_plasma = 0.040 * weight_kg      # V_P: 4.0% dari berat badan (Sirkulasi plasma)
        v_kidney = 0.004 * weight_kg      # V_K: 0.4% dari berat badan
        v_remainder = weight_kg - (v_liver + v_plasma + v_kidney) # V_R: Sisa tubuh

        # 5. Laju Aliran Darah Hepatik Q_L (Soejima et al. 2022)
        q_l_base = 1.35 * ((weight_kg / 70.0) ** 0.75)  # Aliran baseline berskala alometrik
        if age >= 40:
            # Penurunan 0.8% (0.008) per tahun setelah umur 40 tahun
            age_factor = max(0.20, 1.0 - 0.008 * (float(age) - 40.0))  # Floor 20% agar tidak negatif
            q_liver = q_l_base * age_factor
        else:
            q_liver = q_l_base

        # Aliran darah organ lain (L/hr)
        q_kidney = 1.10 * ((weight_kg / 70.0) ** 0.75)
        q_remainder = 3.00 * ((weight_kg / 70.0) ** 0.75)

        # 6. Klirens Metabolisme Hepatik (Cl_metabolisme) & Koreksi Obesitas MASLD (Ghabril et al. 2025)
        cl_scaled = base_cl_metabolism_l_hr * ((weight_kg / 70.0) ** 0.75)
        if bmi >= 30.0:
            # Reduksi otomatis 20% pada BMI >= 30 akibat perlemakan hati kronis
            cl_metabolism = cl_scaled * 0.80
        else:
            cl_metabolism = cl_scaled

        cl_renal = 2.0 * ((weight_kg / 70.0) ** 0.75)

        return {
            "bmi": round(bmi, 2),
            "body_fat_pct": round(body_fat_pct, 2),
            "V_P": round(v_plasma, 4),
            "V_L": round(v_liver, 4),
            "V_K": round(v_kidney, 4),
            "V_R": round(v_remainder, 4),
            "Q_L": round(q_liver, 4),
            "Q_K": round(q_kidney, 4),
            "Q_R": round(q_remainder, 4),
            "Cl_metabolism": round(cl_metabolism, 4),
            "Cl_renal": round(cl_renal, 4),
            "K_P_L": 5.0,  # Koefisien partisi jaringan-terhadap-plasma standar
            "K_P_K": 2.0,
            "K_P_R": 1.0
        }
