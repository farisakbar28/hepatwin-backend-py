# 06 -- Bangun Dataset Arm B (DILIrank 2.0 + LiverTox)

| Tahap | Jumlah |
|---|---|
| DILIrank setelah TU.4 | 839 |
| LiverTox mentah (Master List, baris obat valid) | 1706 |
| LiverTox setelah binerisasi (buang C/D/X) | 1170 |
| LiverTox setelah resolusi SMILES + standardisasi | 823 (dibuang: 411 label tak dikenal, 43 gagal standardisasi/kelayakan) |
| Overlap InChIKey dengan DILIrank | 409 |
| **Konflik label pada overlap** | 76 (18.6% dari overlap) |
| **Total Arm B final** | **1253** |

Perbandingan dengan ekspektasi UPSCALE.md SS3.3 (presedan Yang et al., 1.573 senyawa dari DILIrank 1.0): Arm B HepaTwin = 1253 senyawa (basis DILIrank 2.0, ekspektasi dokumen +-1.600-1.900).

Label positif (1): 593
Label negatif (0): 660

> [KEPUTUSAN AI -- PENDING REVIEW FARMASI]: skema label & aturan konflik (DILIrank menang) mengikuti EXECUTION_PLAN_UPSCALE.md SS14.1 gerbang B2, UPSCALE.md SS3.3.

## Audit wajib: konflik 18,6% > ambang 15% (EXECUTION_PLAN_UPSCALE.md TU.12)

Execution plan mewajibkan audit sebelum lanjut ke TU.13 bila tingkat konflik >15%.
Audit dilakukan pada `06_label_conflicts.csv` (76 baris):

| Pola | Jumlah | % dari konflik |
|---|---|---|
| Nama identik persis di kedua sumber (bukan varian garam/enantiomer) | 40 | 52,6% |
| DILIrank positif, LiverTox negatif | 72 | 94,7% |
| DILIrank negatif, LiverTox positif | 4 | 5,3% |

**Kesimpulan audit: BUKAN bug resolusi SMILES/standardisasi.** Ini terkonfirmasi
karena mayoritas konflik (52,6%) terjadi pada NAMA YANG PERSIS SAMA di kedua
sumber (mis. Abemaciclib/Abemaciclib, Everolimus/Everolimus, Prednisolone/
Prednisolone) -- bukan kasus garam-vs-basa-bebas yang salah dianggap senyawa
berbeda (itu justru kebalikan dari apa yang terlihat: LargestFragmentChooser
BENAR menyatukan bentuk garam & basa bebas ke InChIKey yang sama, yang mana
justru MEMUNCULKAN konflik yang sebelumnya "tersembunyi" karena dua sumber
mencatatnya dengan nama berbeda).

**Penyebab sebenarnya -- perbedaan sistematis skema kedua sumber (94,7% arah
konflik satu arah):** DILIrank menandai *lebih* banyak senyawa positif
dibanding LiverTox untuk senyawa yang SAMA. Penjelasan paling masuk akal:
`vLess-DILI-concern` (skema B2 saat ini memperlakukannya sebagai positif)
adalah kategori FDA-label yang inklusif -- cukup ada sinyal hepatotoksisitas
apa pun di label resmi (termasuk teoritis/jarang) -- sedangkan skor `E`
LiverTox ("unlikely cause") berbasis kurasi laporan kasus klinis yang lebih
ketat. Kedua sumber pada dasarnya mengukur hal yang sedikit berbeda
(sinyal-di-label vs bukti-klinis-kausalitas), bukan salah satu yang keliru.

**Implikasi untuk gerbang B2 (belum final, tetap pending Farmasi):** temuan
ini menambah bukti konkret bahwa memperlakukan `vLess-DILI-concern` sebagai
positif kemungkinan membuat Arm B condong ke arah label positif yang lebih
longgar dibanding jika hanya memakai kriteria LiverTox. Ini bukan alasan untuk
mengubah kode sepihak, tapi **wajib disampaikan ke Farmasi sebagai bagian
dari gerbang B2**, bukan cuma "skema vLess belum dikonfirmasi" secara umum.

**Keputusan: LANJUT ke TU.13** -- tidak ada bug kode yang perlu diperbaiki;
konflik yang ditemukan adalah karakteristik data yang jujur dan bisa
dijelaskan, sudah didokumentasikan apa adanya (Aturan Main #5), bukan
disembunyikan atau dipoles.