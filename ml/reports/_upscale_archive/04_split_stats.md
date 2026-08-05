# 04 -- Statistik Split Arm A

Total senyawa: 839

## L1 -- Random 5-fold CV (stratified)

| Fold | Train | Test | Test pos | Test neg |
|---|---|---|---|---|
| 0 | 671 | 168 | 105 | 63 |
| 1 | 671 | 168 | 104 | 64 |
| 2 | 671 | 168 | 104 | 64 |
| 3 | 671 | 168 | 104 | 64 |
| 4 | 672 | 167 | 104 | 63 |

## L2 -- Scaffold 5-fold CV (Bemis-Murcko)

| Fold | Train | Test | Test pos | Test neg |
|---|---|---|---|---|
| 0 | 662 | 177 | 107 | 70 |
| 1 | 689 | 150 | 95 | 55 |
| 2 | 702 | 137 | 84 | 53 |
| 3 | 698 | 141 | 102 | 39 |
| 4 | 605 | 234 | 133 | 101 |

## Temporal split -- OPSIONAL, tidak dijalankan

DILIrank 2.0 tidak menyertakan kolom tahun persetujuan per baris, jadi `temporal_split()` mengembalikan None. Tidak masuk Definition of Done (UPSCALE.md SS4.3).