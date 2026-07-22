# 03 Standardisasi — dilirank

- Input: `ml/data/interim/dilirank_smiles.csv` (1225 baris)
- Output: `ml/data/interim/dilirank_std.csv` (861 baris)

## Alur filter (baris masuk → keluar)

| Tahap | Jumlah |
|---|---|
| Baris masuk | 1225 |
| Dibuang: label tidak terpetakan/ambigu | 333 |
| Dibuang: gagal parse/standardisasi | 0 |
| Dibuang: tidak lolos kelayakan | 31 |
| **Baris keluar** | **861** |

## Rincian penolakan kelayakan

- `E_MOL_TOO_LARGE`: 31

## Pemetaan label (SEMENTARA — WAJIB dikonfirmasi tim, PRD §8.4 / T1.4)

Nilai label mentah yang ditemukan di input dan hitungannya:

- `ambiguous-dili-concern` → None (333 baris)
- `vless-dili-concern` → 1 (330 baris)
- `vmost-dili-concern` → 1 (206 baris)
- `vno-dili-concern` → 0 (356 baris)

> Pemetaan default: Most/Less-concern → 1, No-concern → 0, Ambiguous/tak dikenal → dibuang.
> Ini keputusan tim, bukan agent. Konfirmasi sebelum training final.
