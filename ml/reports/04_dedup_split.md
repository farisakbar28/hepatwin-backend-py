# 04 Deduplikasi + Split

Seed: 42 · valid_frac: 0.15

## DILIrank (training)

| Tahap | Jumlah |
|---|---|
| Masuk | 861 |
| Duplikat block1 digabung | 21 |
| Block1 konflik label dibuang (semua barisnya) | 1 |
| Setelah dedup internal | 838 |
| → train | 708 |
| → valid | 130 |

## Xu et al. (external test)

| Tahap | Jumlah |
|---|---|
| Masuk | 470 |
| Overlap dg DILIrank dibuang (dari EXTERNAL, PRD §8.4) | 304 |
| **External test final** | **166** |

## Verifikasi

- Overlap block1 train ↔ external_test: **0** (harus 0)
- Scaffold bocor train ↔ valid: **0** (harus 0)
- Pembanding split acak: 126 baris valid (overlap block1 vs scaffold-valid: 23)

> Catatan PRD §8.4: DILIrank & Xu bersumber dari pool obat beririsan; external
> test bisa menyusut jauh di bawah 344. Laporkan apa adanya + CI bootstrap saat evaluasi.
