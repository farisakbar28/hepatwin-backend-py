# R4 -- Analisis Dampak Dua Jalur Eskalasi PRD v2.3 (UKUR, TIDAK DIIMPLEMENTASI)

🚨 **Task ini TIDAK mengubah `fusion_service.py`.** Sesuai peringatan desain `PROJECT_FUSION_V23.md` SS3.2: menambahkan eskalasi warna mentah-mentah berisiko mengulang pola kegagalan SS3.1/SS3.2 lama (satu kondisi `atau` yang selalu menang membunuh cabang lain). Diukur dulu di sini, keputusan implementasi ada di gerbang G1/G2.

## Jalur A -- `metabolic_risk_flag` (BMI >= 30) -> minimal KUNING

Berbasis sweep R2 (`reports/R2_sweep_raw.csv`, n=20250):

| Metrik | Nilai |
|---|---|
| Kombinasi pasien+dosis dgn BMI >= 30 | 9000 / 20250 (44.44%) |
| Kombinasi LOW_EXPOSURE (berpotensi hijau) | 8791 / 20250 |
| Dari kombinasi LOW_EXPOSURE, yang BMI >= 30 (akan kehilangan hijau) | 3805 / 8791 (43.28%) |

**Kesimpulan Jalur A:** bila aturan diaktifkan, **44.4% dari seluruh kombinasi pasien+dosis realistis** (bukan hanya yang low-exposure -- SELURUH interaksi pengguna BMI>=30, apa pun senyawa dan dosisnya) TIDAK AKAN PERNAH bisa melihat HIJAU lagi, karena `metabolic_risk_flag` dicek independen dari AI/exposure band. Ini SEBANDING dengan pola kegagalan SS3.1 lama (satu kondisi mendominasi). HIJAU masih terjangkau utk pengguna BMI < 30 (55.6% populasi sweep).

## Jalur B -- "LiverTox strong evidence" -> MERAH

Basis: 1231 senyawa `is_simulatable=TRUE`. Breakdown `injury_pattern`:

| injury_pattern | n |
|---|---|
| Tidak Terklasifikasi | 824 |
| Hepatoseluler | 236 |
| Kolestatik | 128 |
| Campuran | 43 |

| Tafsiran | Kriteria | Senyawa terdampak (selalu MERAH) | % katalog |
|---|---|---|---|
| (i) | Punya `injury_pattern` spesifik | 407 | 33.1% |
| (ii) | (i) DAN `livertox_match_method=exact_name` | 218 | 17.7% |
| (iii) | (i) DAN `dili_concern=vMost-DILI-concern` | 120 | 9.7% |

**Kesimpulan Jalur B:** tafsiran (i) (paling longgar) memaksa **407 senyawa (33.1% katalog)** SELALU MERAH tanpa memandang skor AI atau dosis -- matriks 3x3 jadi tidak relevan utk sepertiga katalog. Tafsiran (iii) (paling ketat, mensyaratkan skor AI DAN bukti lokasi sejalan) jauh lebih sempit (120 senyawa, 9.7%) -- tapi definisi final tetap keputusan Farmasi (gerbang G2), bukan agent.

## Sintesis & Usulan (BUKAN keputusan final)

`[KEPUTUSAN AI -- PENDING REVIEW]` Dua alternatif yang TIDAK membunuh cabang lain, konsisten dgn PRD v2.3 SS8.3.3 sendiri yang menyebut `metabolic_risk_flag` sbg *"hanya flag naratif; tidak menurunkan clearance default"*:

- **Jalur A:** ekspos `metabolic_risk_flag` sbg field naratif terpisah (`metabolic_risk_note`), ditampilkan sbg peringatan teks di UI, TANPA mengubah warna. Memenuhi maksud PRD tanpa mengorbankan HIJAU utk 44% populasi.
- **Jalur B:** "strong evidence" memengaruhi `hotspot_intensity`/confidence tampilan (sudah ada infrastrukturnya sejak F4), BUKAN warna -- bukti kuat terlihat lebih tegas secara visual tanpa memaksa MERAH pada sepertiga katalog.

🚨 **Ambiguitas PRD wajib diangkat ke Ketua Tim (bukan diputuskan agent):** PRD v2.3 SS8.3.3 sendiri berkontradiksi -- teks naratif menyebut `metabolic_risk_flag` "hanya flag naratif", tapi tabel matriks eskalasi di baris yang sama menuliskannya sbg kondisi `atau` yang mengubah warna KUNING. Kedua tafsiran itu TIDAK bisa benar bersamaan. Perlu klarifikasi eksplisit sebelum R5 mengimplementasikan apa pun selain opsi default (field informatif tanpa pengaruh warna).
