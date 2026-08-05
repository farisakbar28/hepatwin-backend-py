# 08 -- Ablasi Tox21 Multi-Task Auxiliary Head (TU.16, stretch)

Arm A (839 senyawa), 5-fold CV random split, seed=42 saja (eksperimen tambahan, TIDAK menggantikan tabel utama Arm A/B TU.9/TU.13).

| Kondisi | AUC-ROC (mean+-std) | MCC (mean+-std) |
|---|---|---|
| Tanpa auxiliary head | 0.7390 +/- 0.0229 | 0.3681 +/- 0.0522 |
| Dengan Tox21 auxiliary head (lambda=0.1) | 0.7420 +/- 0.0242 | 0.3610 +/- 0.0891 |

**Label jelas:** ini eksperimen tambahan terpisah (TU.16, stretch, opsional -- UPSCALE.md SS3.4), TIDAK menggantikan atau mengubah kesimpulan Arm A vs Arm B di `07_comparison.md`.

## Kesimpulan jujur

Selisih AUC (+0,0030) jauh di dalam rentang 1 std (±0,023-0,024) -- **secara
statistik tidak dapat dibedakan dari tanpa noise**, bukan peningkatan nyata.
MCC bahkan sedikit lebih rendah dengan auxiliary head (0,3610 vs 0,3681).
Kesimpulan: pada skala data ini (Arm A, 839 senyawa; Tox21, 7823 senyawa tanpa
overlap), auxiliary head Tox21 dengan λ=0,1 **tidak terbukti memberi manfaat
berarti** untuk tugas prediksi DILI -- konsisten dengan intuisi bahwa transfer
learning lintas-domain (bahan kimia industri → obat) butuh dataset primer yang
jauh lebih besar untuk sinyal auxiliary task benar-benar membantu representasi
bersama. Ini dilaporkan apa adanya (Aturan Main #5), bukan sebagai kegagalan
implementasi -- pipeline bekerja benar (3/3 test pytest hijau, properti
gradien mengalir ke kedua kepala terverifikasi), hasilnya saja netral.