# R2 -- Uji Ulang Keterjangkauan LOW_EXPOSURE (Mesin A v2.3)

Sweep 20250 kombinasi (usia 18-90 step 3, tinggi 150-190cm, BMI 16-40, kedua jenis kelamin, dosis 0.5-50 mg/kg) -- rentang IDENTIK dengan sweep v2.1 arsip untuk perbandingan apel-ke-apel. XLogP tidak divariasikan (`xlogp=None`, fallback `xlogp_eff=0.0`) -- di luar cakupan sweep asli, dicatat sbg keterbatasan metodologis.

## Tabel perbandingan v2.1 (arsip) vs v2.3

| exposure_category | v2.1 (arsip) | v2.3 (sekarang) |
|---|---|---|
| LOW_EXPOSURE | 0 (0.00%) | 8791 (43.41%) |
| MODERATE_EXPOSURE | 2602 (12.85%) | 6959 (34.37%) |
| HIGH_EXPOSURE | 17648 (87.15%) | 4500 (22.22%) |

## Contoh kombinasi yang mencapai LOW_EXPOSURE (menampilkan 20 dari 8791)

| usia | tinggi | BMI | berat(kg) | jk | dosis(mg/kg) | exposure_index |
|---|---|---|---|---|---|---|
| 18 | 150 | 16 | 36.0 | L | 0.5 | 3.6638 |
| 18 | 150 | 16 | 36.0 | L | 1 | 4.8678 |
| 18 | 150 | 16 | 36.0 | L | 3 | 6.9317 |
| 18 | 150 | 16 | 36.0 | L | 5 | 7.9254 |
| 18 | 150 | 16 | 36.0 | P | 0.5 | 3.6451 |
| 18 | 150 | 16 | 36.0 | P | 1 | 4.8467 |
| 18 | 150 | 16 | 36.0 | P | 3 | 6.9087 |
| 18 | 150 | 16 | 36.0 | P | 5 | 7.902 |
| 18 | 150 | 18.5 | 41.6 | L | 0.5 | 3.7049 |
| 18 | 150 | 18.5 | 41.6 | L | 1 | 4.9119 |
| 18 | 150 | 18.5 | 41.6 | L | 3 | 6.9782 |
| 18 | 150 | 18.5 | 41.6 | L | 5 | 7.9724 |
| 18 | 150 | 18.5 | 41.6 | P | 0.5 | 3.6869 |
| 18 | 150 | 18.5 | 41.6 | P | 1 | 4.8918 |
| 18 | 150 | 18.5 | 41.6 | P | 3 | 6.9563 |
| 18 | 150 | 18.5 | 41.6 | P | 5 | 7.9501 |
| 18 | 150 | 22 | 49.5 | L | 0.5 | 3.7529 |
| 18 | 150 | 22 | 49.5 | L | 1 | 4.9634 |
| 18 | 150 | 22 | 49.5 | L | 3 | 7.0324 |
| 18 | 150 | 22 | 49.5 | L | 5 | 8.0272 |

## Sebaran exposure_index

Ambang beku: **p33 = 8.2388**, **p66 = 10.9192**

| Statistik | exposure_index |
|---|---|
| min | 3.4215 |
| p5 | 3.7650 |
| p25 | 6.9483 |
| median | 8.9763 |
| p75 | 10.3279 |
| p95 | 12.6408 |
| max | 12.9284 |

Posisi relatif: 8791 dari 20250 sampel (43.41%) di bawah p33; 4500 (22.22%) di atas p66.

## Uji ketergantungan dosis (rusak di v2.1, harus berubah di v2.3)

Profil tetap: usia=30, jk=P, berat=65kg, tinggi=165cm. v2.1 (arsip) menunjukkan `cmax_auc_ratio` TETAP PERSIS `0.441640` di semua dosis (50-4000mg) -- bukti bug dose-independence.

| dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |
|---|---|---|---|
| 50 | 4.5565 | 0.350020 | LOW_EXPOSURE |
| 200 | 7.1488 | 0.350020 | LOW_EXPOSURE |
| 500 | 8.9428 | 0.350020 | MODERATE_EXPOSURE |
| 1000 | 10.3160 | 0.350020 | MODERATE_EXPOSURE |
| 4000 | 13.0788 | 0.350020 | HIGH_EXPOSURE |

**exposure_index BERUBAH terhadap dosis** (kontras dgn v2.1 -- bukti perbaikan berhasil). `shape_ratio_h_inv` (alias `cmax_auc_ratio` lama) tetap konstan seperti diharapkan (rasio, bukan magnitude).

