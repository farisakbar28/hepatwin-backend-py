# 03 Standardisasi — xu2015

- Input: `ml/data/raw/xu2015.csv` (475 baris)
- Output: `ml/data/interim/xu2015_std.csv` (470 baris)

## Alur filter (baris masuk → keluar)

| Tahap | Jumlah |
|---|---|
| Baris masuk | 475 |
| Dibuang: label tidak terpetakan/ambigu | 0 |
| Dibuang: gagal parse/standardisasi | 0 |
| Dibuang: tidak lolos kelayakan | 5 |
| **Baris keluar** | **470** |

## Rincian penolakan kelayakan

- `E_MOL_TOO_LARGE`: 5

## Pemetaan label (SEMENTARA — WAJIB dikonfirmasi tim, PRD §8.4 / T1.4)

Nilai label mentah yang ditemukan di input dan hitungannya:

- `0` → 0 (239 baris)
- `1` → 1 (236 baris)

> Pemetaan default: Most/Less-concern → 1, No-concern → 0, Ambiguous/tak dikenal → dibuang.
> Ini keputusan tim, bukan agent. Konfirmasi sebelum training final.
