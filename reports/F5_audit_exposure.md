# F5 -- Analisis Sensitivitas exposure_evaluator

Enam profil pasien contoh x sepuluh dosis relatif (mg/kg). Karena `exposure_category` tidak bergantung pada identitas senyawa (lihat docstring skrip & `reports/F2_exposure_reachability_finding.md`), hasil di bawah berlaku SAMA untuk seluruh 1.231 senyawa `is_simulatable=TRUE` pada kombinasi pasien+dosis yang sama.

## Dewasa muda sehat (usia=25, jk=P, berat=65.0kg, tinggi=170.0cm, BMI=22.5, vulnerable=False)

| dosis (mg/kg) | dosis (mg) | cmax_auc_ratio | dose_per_kg | exposure_category |
|---|---|---|---|---|
| 0.5 | 32.5 | 0.4416 | 0.5 | HIGH_EXPOSURE |
| 1 | 65.0 | 0.4416 | 1.0 | HIGH_EXPOSURE |
| 3 | 195.0 | 0.4416 | 3.0 | HIGH_EXPOSURE |
| 5 | 325.0 | 0.4416 | 5.0 | HIGH_EXPOSURE |
| 8 | 520.0 | 0.4416 | 8.0 | HIGH_EXPOSURE |
| 10 | 650.0 | 0.4416 | 10.0 | HIGH_EXPOSURE |
| 15 | 975.0 | 0.4416 | 15.0 | HIGH_EXPOSURE |
| 20 | 1300.0 | 0.4416 | 20.0 | HIGH_EXPOSURE |
| 30 | 1950.0 | 0.4416 | 30.0 | HIGH_EXPOSURE |
| 50 | 3250.0 | 0.4416 | 50.0 | HIGH_EXPOSURE |

## Paruh baya obesitas (vulnerable/BMI) (usia=45, jk=L, berat=95.0kg, tinggi=170.0cm, BMI=32.9, vulnerable=True)

| dosis (mg/kg) | dosis (mg) | cmax_auc_ratio | dose_per_kg | exposure_category |
|---|---|---|---|---|
| 0.5 | 47.5 | 0.3683 | 0.5 | HIGH_EXPOSURE |
| 1 | 95.0 | 0.3683 | 1.0 | HIGH_EXPOSURE |
| 3 | 285.0 | 0.3683 | 3.0 | HIGH_EXPOSURE |
| 5 | 475.0 | 0.3683 | 5.0 | HIGH_EXPOSURE |
| 8 | 760.0 | 0.3683 | 8.0 | HIGH_EXPOSURE |
| 10 | 950.0 | 0.3683 | 10.0 | HIGH_EXPOSURE |
| 15 | 1425.0 | 0.3683 | 15.0 | HIGH_EXPOSURE |
| 20 | 1900.0 | 0.3683 | 20.0 | HIGH_EXPOSURE |
| 30 | 2850.0 | 0.3683 | 30.0 | HIGH_EXPOSURE |
| 50 | 4750.0 | 0.3683 | 50.0 | HIGH_EXPOSURE |

## Lansia (vulnerable/usia) (usia=70, jk=P, berat=60.0kg, tinggi=160.0cm, BMI=23.4, vulnerable=True)

| dosis (mg/kg) | dosis (mg) | cmax_auc_ratio | dose_per_kg | exposure_category |
|---|---|---|---|---|
| 0.5 | 30.0 | 0.4211 | 0.5 | HIGH_EXPOSURE |
| 1 | 60.0 | 0.4212 | 1.0 | HIGH_EXPOSURE |
| 3 | 180.0 | 0.4212 | 3.0 | HIGH_EXPOSURE |
| 5 | 300.0 | 0.4212 | 5.0 | HIGH_EXPOSURE |
| 8 | 480.0 | 0.4212 | 8.0 | HIGH_EXPOSURE |
| 10 | 600.0 | 0.4212 | 10.0 | HIGH_EXPOSURE |
| 15 | 900.0 | 0.4212 | 15.0 | HIGH_EXPOSURE |
| 20 | 1200.0 | 0.4212 | 20.0 | HIGH_EXPOSURE |
| 30 | 1800.0 | 0.4212 | 30.0 | HIGH_EXPOSURE |
| 50 | 3000.0 | 0.4212 | 50.0 | HIGH_EXPOSURE |

## Remaja (usia=16, jk=L, berat=50.0kg, tinggi=165.0cm, BMI=18.4, vulnerable=False)

| dosis (mg/kg) | dosis (mg) | cmax_auc_ratio | dose_per_kg | exposure_category |
|---|---|---|---|---|
| 0.5 | 25.0 | 0.464 | 0.5 | HIGH_EXPOSURE |
| 1 | 50.0 | 0.464 | 1.0 | HIGH_EXPOSURE |
| 3 | 150.0 | 0.464 | 3.0 | HIGH_EXPOSURE |
| 5 | 250.0 | 0.464 | 5.0 | HIGH_EXPOSURE |
| 8 | 400.0 | 0.464 | 8.0 | HIGH_EXPOSURE |
| 10 | 500.0 | 0.464 | 10.0 | HIGH_EXPOSURE |
| 15 | 750.0 | 0.464 | 15.0 | HIGH_EXPOSURE |
| 20 | 1000.0 | 0.464 | 20.0 | HIGH_EXPOSURE |
| 30 | 1500.0 | 0.464 | 30.0 | HIGH_EXPOSURE |
| 50 | 2500.0 | 0.464 | 50.0 | HIGH_EXPOSURE |

## Dewasa berat badan rendah (usia=30, jk=P, berat=45.0kg, tinggi=160.0cm, BMI=17.6, vulnerable=False)

| dosis (mg/kg) | dosis (mg) | cmax_auc_ratio | dose_per_kg | exposure_category |
|---|---|---|---|---|
| 0.5 | 22.5 | 0.4727 | 0.5 | HIGH_EXPOSURE |
| 1 | 45.0 | 0.4727 | 1.0 | HIGH_EXPOSURE |
| 3 | 135.0 | 0.4727 | 3.0 | HIGH_EXPOSURE |
| 5 | 225.0 | 0.4727 | 5.0 | HIGH_EXPOSURE |
| 8 | 360.0 | 0.4727 | 8.0 | HIGH_EXPOSURE |
| 10 | 450.0 | 0.4727 | 10.0 | HIGH_EXPOSURE |
| 15 | 675.0 | 0.4727 | 15.0 | HIGH_EXPOSURE |
| 20 | 900.0 | 0.4727 | 20.0 | HIGH_EXPOSURE |
| 30 | 1350.0 | 0.4727 | 30.0 | HIGH_EXPOSURE |
| 50 | 2250.0 | 0.4727 | 50.0 | HIGH_EXPOSURE |

## Lansia obesitas (double vulnerable) (usia=75, jk=L, berat=100.0kg, tinggi=165.0cm, BMI=36.7, vulnerable=True)

| dosis (mg/kg) | dosis (mg) | cmax_auc_ratio | dose_per_kg | exposure_category |
|---|---|---|---|---|
| 0.5 | 50.0 | 0.3444 | 0.5 | MODERATE_EXPOSURE |
| 1 | 100.0 | 0.3444 | 1.0 | MODERATE_EXPOSURE |
| 3 | 300.0 | 0.3444 | 3.0 | MODERATE_EXPOSURE |
| 5 | 500.0 | 0.3444 | 5.0 | MODERATE_EXPOSURE |
| 8 | 800.0 | 0.3444 | 8.0 | MODERATE_EXPOSURE |
| 10 | 1000.0 | 0.3444 | 10.0 | MODERATE_EXPOSURE |
| 15 | 1500.0 | 0.3444 | 15.0 | MODERATE_EXPOSURE |
| 20 | 2000.0 | 0.3444 | 20.0 | MODERATE_EXPOSURE |
| 30 | 3000.0 | 0.3444 | 30.0 | HIGH_EXPOSURE |
| 50 | 5000.0 | 0.3444 | 50.0 | HIGH_EXPOSURE |

## Ringkasan lintas 6 profil x 10 dosis (n=60 kombinasi)

| exposure_category | Jumlah | Persentase |
|---|---|---|
| LOW_EXPOSURE | 0 | 0.0% |
| MODERATE_EXPOSURE | 8 | 13.3% |
| HIGH_EXPOSURE | 52 | 86.7% |

🚩 **LOW_EXPOSURE tidak tercapai sama sekali** di keenam profil pasien contoh manapun, pada dosis serendah 0.5 mg/kg sekalipun -- konsisten dengan sweep besar F2 (`reports/F2_exposure_reachability_finding.md`, 0/20.250 kombinasi realistis). Kategori ini PRAKTIS MATI untuk skenario pasien manapun yang diuji, terlepas dari senyawa yang dipilih.

## Kesimpulan

- Di kelima profil PERTAMA (non-vulnerable maupun single-vulnerable), `cmax_auc_ratio` pasien itu sendiri
  (0.42-0.47) SUDAH melewati `high_threshold` yang berlaku (0.40 non-vulnerable / 0.35 vulnerable) --
  sehingga HIGH_EXPOSURE tercapai di SEMUA 10 dosis yang diuji (0.5 s.d. 50 mg/kg), termasuk dosis
  sangat rendah. Dosis TIDAK PERNAH jadi faktor penentu untuk kelima profil ini -- rasio sendirian sudah cukup.
- Hanya profil KEENAM (lansia obesitas, *double vulnerable*) yang menunjukkan `MODERATE_EXPOSURE` --
  karena ratio-nya (0.3444) kebetulan jatuh DI ANTARA `moderate_threshold` (0.20) dan `high_threshold`
  (0.35) vulnerable. Pada dosis >=30 mg/kg, `dose_per_kg` mengambil alih dan memicu HIGH. Ini SATU-SATUNYA
  dari 6 profil yang exposure_category-nya benar-benar dipengaruhi baik oleh rasio maupun dosis.
- Temuan ini MEMPERKUAT (bukan menggantikan) temuan F2: dengan enam ambang saat ini (`[ASUMSI DESAIN -- PENDING REVIEW FARMASI]`, gerbang K3), sistem secara efektif berperilaku sebagai klasifikasi 2-kelas (MODERATE vs HIGH) untuk sebagian besar skenario realistis, bukan 3-kelas seperti dirancang PRD. Tidak diubah di sini (logika dibekukan sampai keputusan Farmasi, PROJECT_FUSION.md SS8 prinsip #9) -- dilaporkan apa adanya untuk `reports/F9_limitations_fusion.md`.
