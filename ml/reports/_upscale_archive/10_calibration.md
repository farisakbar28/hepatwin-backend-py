# TU.10 -- Kalibrasi Probabilitas (Arm A, demonstrasi 1-seed)

Split: train=419, cal=252, test=168 (stratified, seed=42)
Metode kalibrator terpilih otomatis: **isotonic** (ambang isotonic UPSCALE.md SS6: cal set >= 200 -> isotonic, dipakai n_cal=252)

| Tahap | Brier | ECE |
|---|---|---|
| Sebelum kalibrasi | 0.2459 | 0.1645 |
| Sesudah kalibrasi | 0.2231 | 0.0831 |

## Reliability diagram (per bin confidence, before vs after)

| Bin | Tahap | n | Mean predicted | Mean observed |
|---|---|---|---|---|
| 0.0-0.1 | before | 22 | 0.053 | 0.364 |
| 0.0-0.1 | after | 7 | 0.014 | 0.286 |
| 0.1-0.2 | before | 14 | 0.141 | 0.714 |
| 0.1-0.2 | after | 2 | 0.143 | 0.000 |
| 0.2-0.3 | before | 14 | 0.251 | 0.214 |
| 0.2-0.3 | after | 30 | 0.281 | 0.533 |
| 0.3-0.4 | before | 8 | 0.335 | 0.500 |
| 0.4-0.5 | before | 11 | 0.451 | 0.545 |
| 0.4-0.5 | after | 36 | 0.448 | 0.472 |
| 0.5-0.6 | before | 10 | 0.558 | 0.700 |
| 0.5-0.6 | after | 10 | 0.551 | 0.600 |
| 0.6-0.7 | before | 19 | 0.642 | 0.526 |
| 0.6-0.7 | after | 19 | 0.624 | 0.632 |
| 0.7-0.8 | before | 8 | 0.751 | 0.750 |
| 0.8-0.9 | before | 25 | 0.854 | 0.800 |
| 0.8-0.9 | after | 54 | 0.822 | 0.796 |
| 0.9-1.0 | before | 37 | 0.944 | 0.811 |
| 0.9-1.0 | after | 10 | 0.929 | 0.800 |