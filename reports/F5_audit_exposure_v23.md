# R8 -- Audit Sensitivitas exposure_evaluator v2.3

Regenerasi `reports/_v21_archive/F5_audit_exposure.md` (v2.1) terhadap Mesin A v2.3. XLogP tetap 1.2 (representatif) supaya fokus pada efek kovariat pasien+dosis, konsisten metodologi dgn versi arsip.

## Dewasa muda sehat (usia=25, jk=P, berat=65.0kg, tinggi=170.0cm, BMI=22.5, metabolic_risk_flag=False)

| dosis (mg/kg) | dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |
|---|---|---|---|---|
| 0.5 | 32.5 | 3.7772 | 0.347742 | LOW_EXPOSURE |
| 1 | 65.0 | 4.9883 | 0.347742 | LOW_EXPOSURE |
| 3 | 195.0 | 7.0575 | 0.347742 | LOW_EXPOSURE |
| 5 | 325.0 | 8.0523 | 0.347742 | LOW_EXPOSURE |
| 8 | 520.0 | 8.9770 | 0.347742 | MODERATE_EXPOSURE |
| 10 | 650.0 | 9.4182 | 0.347742 | MODERATE_EXPOSURE |
| 15 | 975.0 | 10.2223 | 0.347742 | MODERATE_EXPOSURE |
| 20 | 1300.0 | 10.7942 | 0.347742 | MODERATE_EXPOSURE |
| 30 | 1950.0 | 11.6017 | 0.347742 | HIGH_EXPOSURE |
| 50 | 3250.0 | 12.6205 | 0.347742 | HIGH_EXPOSURE |

## Paruh baya obesitas (BMI>=30) (usia=45, jk=L, berat=95.0kg, tinggi=170.0cm, BMI=32.9, metabolic_risk_flag=True)

| dosis (mg/kg) | dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |
|---|---|---|---|---|
| 0.5 | 47.5 | 3.8527 | 0.330806 | LOW_EXPOSURE |
| 1 | 95.0 | 5.0686 | 0.330806 | LOW_EXPOSURE |
| 3 | 285.0 | 7.1416 | 0.330806 | LOW_EXPOSURE |
| 5 | 475.0 | 8.1372 | 0.330806 | LOW_EXPOSURE |
| 8 | 760.0 | 9.0623 | 0.330806 | MODERATE_EXPOSURE |
| 10 | 950.0 | 9.5037 | 0.330806 | MODERATE_EXPOSURE |
| 15 | 1425.0 | 10.3079 | 0.330806 | MODERATE_EXPOSURE |
| 20 | 1900.0 | 10.8800 | 0.330806 | MODERATE_EXPOSURE |
| 30 | 2850.0 | 11.6875 | 0.330806 | HIGH_EXPOSURE |
| 50 | 4750.0 | 12.7065 | 0.330806 | HIGH_EXPOSURE |

## Lansia (usia=70, jk=P, berat=60.0kg, tinggi=160.0cm, BMI=23.4, metabolic_risk_flag=True)

| dosis (mg/kg) | dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |
|---|---|---|---|---|
| 0.5 | 30.0 | 3.5993 | 0.302128 | LOW_EXPOSURE |
| 1 | 60.0 | 4.7883 | 0.302128 | LOW_EXPOSURE |
| 3 | 180.0 | 6.8391 | 0.302128 | LOW_EXPOSURE |
| 5 | 300.0 | 7.8298 | 0.302128 | LOW_EXPOSURE |
| 8 | 480.0 | 8.7521 | 0.302128 | MODERATE_EXPOSURE |
| 10 | 600.0 | 9.1925 | 0.302128 | MODERATE_EXPOSURE |
| 15 | 900.0 | 9.9954 | 0.302128 | MODERATE_EXPOSURE |
| 20 | 1200.0 | 10.5668 | 0.302128 | MODERATE_EXPOSURE |
| 30 | 1800.0 | 11.3737 | 0.302128 | HIGH_EXPOSURE |
| 50 | 3000.0 | 12.3922 | 0.302128 | HIGH_EXPOSURE |

## Remaja (usia=16, jk=L, berat=50.0kg, tinggi=165.0cm, BMI=18.4, metabolic_risk_flag=False)

| dosis (mg/kg) | dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |
|---|---|---|---|---|
| 0.5 | 25.0 | 3.7484 | 0.362975 | LOW_EXPOSURE |
| 1 | 50.0 | 4.9584 | 0.362975 | LOW_EXPOSURE |
| 3 | 150.0 | 7.0268 | 0.362975 | LOW_EXPOSURE |
| 5 | 250.0 | 8.0215 | 0.362975 | LOW_EXPOSURE |
| 8 | 400.0 | 8.9461 | 0.362975 | MODERATE_EXPOSURE |
| 10 | 500.0 | 9.3873 | 0.362975 | MODERATE_EXPOSURE |
| 15 | 750.0 | 10.1913 | 0.362975 | MODERATE_EXPOSURE |
| 20 | 1000.0 | 10.7632 | 0.362975 | MODERATE_EXPOSURE |
| 30 | 1500.0 | 11.5707 | 0.362975 | HIGH_EXPOSURE |
| 50 | 2500.0 | 12.5895 | 0.362975 | HIGH_EXPOSURE |

## Dewasa berat badan rendah (usia=30, jk=P, berat=45.0kg, tinggi=160.0cm, BMI=17.6, metabolic_risk_flag=False)

| dosis (mg/kg) | dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |
|---|---|---|---|---|
| 0.5 | 22.5 | 3.6757 | 0.359374 | LOW_EXPOSURE |
| 1 | 45.0 | 4.8786 | 0.359374 | LOW_EXPOSURE |
| 3 | 135.0 | 6.9415 | 0.359374 | LOW_EXPOSURE |
| 5 | 225.0 | 7.9349 | 0.359374 | LOW_EXPOSURE |
| 8 | 360.0 | 8.8588 | 0.359374 | MODERATE_EXPOSURE |
| 10 | 450.0 | 9.2997 | 0.359374 | MODERATE_EXPOSURE |
| 15 | 675.0 | 10.1034 | 0.359374 | MODERATE_EXPOSURE |
| 20 | 900.0 | 10.6751 | 0.359374 | MODERATE_EXPOSURE |
| 30 | 1350.0 | 11.4824 | 0.359374 | HIGH_EXPOSURE |
| 50 | 2250.0 | 12.5012 | 0.359374 | HIGH_EXPOSURE |

## Lansia obesitas (BMI>=30 + usia>=60) (usia=75, jk=L, berat=100.0kg, tinggi=165.0cm, BMI=36.7, metabolic_risk_flag=True)

| dosis (mg/kg) | dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |
|---|---|---|---|---|
| 0.5 | 50.0 | 3.6892 | 0.282565 | LOW_EXPOSURE |
| 1 | 100.0 | 4.8841 | 0.282565 | LOW_EXPOSURE |
| 3 | 300.0 | 6.9395 | 0.282565 | LOW_EXPOSURE |
| 5 | 500.0 | 7.9312 | 0.282565 | LOW_EXPOSURE |
| 8 | 800.0 | 8.8541 | 0.282565 | MODERATE_EXPOSURE |
| 10 | 1000.0 | 9.2946 | 0.282565 | MODERATE_EXPOSURE |
| 15 | 1500.0 | 10.0978 | 0.282565 | MODERATE_EXPOSURE |
| 20 | 2000.0 | 10.6693 | 0.282565 | MODERATE_EXPOSURE |
| 30 | 3000.0 | 11.4764 | 0.282565 | HIGH_EXPOSURE |
| 50 | 5000.0 | 12.4949 | 0.282565 | HIGH_EXPOSURE |

## Ringkasan lintas 6 profil x 10 dosis (n=60 kombinasi)

| exposure_category | Jumlah | Persentase |
|---|---|---|
| LOW_EXPOSURE | 24 | 40.0% |
| MODERATE_EXPOSURE | 24 | 40.0% |
| HIGH_EXPOSURE | 12 | 20.0% |

**6/6 profil pasien menunjukkan exposure_category BERUBAH seiring dosis** (0.5 s.d. 50 mg/kg) -- kontras langsung dengan versi v2.1 arsip, di mana SELURUH 6 profil menunjukkan `exposure_category` konstan di semua dosis kecuali via jalur `dose_per_kg` terpisah (bug dose-independence `cmax_auc_ratio`). Di v2.3, `exposure_index` sendiri (bukan jalur terpisah) yang membawa efek dosis.

## Kesimpulan

- `exposure_index` naik monoton terhadap dosis pada profil pasien tetap (lihat tabel per profil) -- BERBEDA fundamental dari `cmax_auc_ratio` v2.1 yang matematis konstan thd dosis.
- `shape_ratio_h_inv` (alias `cmax_auc_ratio` lama) TETAP konstan per profil terlepas dari dosis, sesuai desain barunya (rasio bentuk kurva, bukan magnitude paparan) -- backward-compatible utk field lama tapi TIDAK lagi dipakai utk kategori.
- Ketiga kategori (LOW/MODERATE/HIGH) SEMUA terpakai pada rentang profil+dosis yang diuji (lihat R2 utk pembuktian skala penuh 20.250 kombinasi).
- p33/p66 (`app/services/pbpk_calibration.py`) adalah kuantil kalibrasi distribusional internal (PBPK_EXPOSURE_CALIBRATION_V2_3, hash katalog `0a06e54dbea3dd0c...`), BUKAN ambang klinis -- ditegaskan ulang di sini sesuai PRD v2.3 SS8.2.2.8.
