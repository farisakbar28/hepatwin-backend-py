# F1 -- Diagnostik Distribusi Skor Katalog

**snapshot_at:** 2026-08-06T02:54:52.065883+00:00  
**Total senyawa is_simulatable=TRUE:** 1231  
**Skor berhasil:** 1231  |  **Gagal:** 0  
**Waktu total inferensi (1231x forward pass, sekuensial):** 9.12 detik (7.41 ms/senyawa rata-rata)

## Statistik global dili_score (n=1231)

| Statistik | Nilai |
|---|---|
| min | 0.5078 |
| p1 | 0.5229 |
| p5 | 0.5368 |
| p10 | 0.5496 |
| p25 | 0.5856 |
| p33 | 0.6046 |
| p50 | 0.6375 |
| p67 | 0.6664 |
| p75 | 0.6772 |
| p90 | 0.6992 |
| p95 | 0.7102 |
| p99 | 0.7222 |
| median (p50) | 0.6375 |
| max | 0.7329 |

## Verifikasi temuan SS3.1 (PROJECT_FUSION.md)

- Batas bawah aktual terukur pada katalog 1.231 senyawa: **0.5078**
- Batas atas aktual terukur pada katalog 1.231 senyawa: **0.7329**
- Jumlah senyawa dengan dili_score < 0.30: **0** (ekspektasi: 0) -- **terverifikasi, sesuai SS3.1**

**Klarifikasi penting soal dua angka yang berbeda maknanya:** PROJECT_FUSION.md SS3.1 mengutip
`raw=0.00 -> 0.4337` dan `raw=1.00 -> 0.7747` -- itu adalah **batas matematis teoretis** dari rumus
Platt scaling (`sigmoid(1.5016*raw - 0.2667)`) pada input mentah 0 dan 1, BUKAN klaim bahwa katalog
nyata akan menyentuh kedua ujung itu. Rentang empiris yang benar-benar terukur di atas (**0.5078 --
0.7329**) LEBIH SEMPIT dari batas teoretis (0.4337 -- 0.7747), dan itu **konsisten**, bukan kontradiksi:
tidak ada satu pun dari 1.231 SMILES nyata yang menghasilkan probabilitas mentah model persis 0.0 atau
1.0 sebelum kalibrasi. Batas teoretis SS3.1 tetap valid sebagai *lower/upper bound* absolut sistem;
angka empiris di sini adalah rentang yang **relevan langsung untuk penurunan ambang F2** (karena F2
menurunkan T_low/T_high dari distribusi 1.231 senyawa ini, bukan dari batas teoretis).

## Distribusi warna dengan ambang LAMA (0.30 / 0.70), murni dari dili_score

| Warna | Jumlah | Persentase |
|---|---|---|
| HIJAU (< 0.30) | 0 | 0.00% |
| KUNING (0.30-0.70) | 1113 | 90.41% |
| MERAH (> 0.70) | 118 | 9.59% |

## Distribusi per dili_concern

| dili_concern | n | min | p25 | median | p75 | max |
|---|---|---|---|---|---|---|
| Ambiguous-DILI-concern | 336 | 0.5101 | 0.5969 | 0.6449 | 0.6797 | 0.7264 |
| vLess-DILI-concern | 332 | 0.5290 | 0.6149 | 0.6539 | 0.6865 | 0.7329 |
| vMost-DILI-concern | 206 | 0.5311 | 0.6388 | 0.6691 | 0.6881 | 0.7271 |
| vNo-DILI-concern | 357 | 0.5078 | 0.5522 | 0.5868 | 0.6308 | 0.7143 |

