# 18 -- Konstruksi External Hold-out Set (Arm A, v3.0 K3)

Seed: 42 (scaffold GROUP shuffle, bukan senyawa individual -- UPSCALE.md SS13.1)

| Set | n | % dari total | Proporsi label positif |
|---|---|---|---|
| Total (Arm A) | 839 | 100% | 0.6210 |
| holdout_set | 167 | 19.9% | 0.6826 |
| dev_pool | 672 | 80.1% | 0.6057 |

Selisih proporsi label (holdout vs total): 0.0617 (scaffold-disjoint diutamakan di atas stratifikasi sempurna, sesuai UPSCALE.md SS13.1 poin 6).

## Segel reproduksibilitas

Daftar lengkap 167 InChIKey holdout_set disimpan di `ml/data/interim/holdout_inchikeys.json` -- dicek ulang di TU.22 untuk membuktikan hold-out tidak pernah disentuh sebelum evaluasi akhir.