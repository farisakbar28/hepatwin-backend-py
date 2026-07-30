# Limitations & Batasan -- HepaTwin Mesin B (branch upscale)

Disusun sebagai bagian TU.15, merangkum seluruh temuan TU.0-TU.14. Prinsip
penulisan dokumen ini: jujur apa adanya (Aturan Main #4/#5), tidak menyembunyikan
kelemahan demi presentasi yang lebih baik.

## 1. Tanpa external test dari studi independen -- keputusan sadar, bukan kelalaian

UPSCALE.md §1 mendasarkan keputusan ini pada rantai rujukan arsitektur itu
sendiri: Wibowo, Chong, & Tayara (2025) **tidak** menguji GATNN-DNN pada dataset
eksternal independen -- performa yang mereka laporkan (AUC 0,757, MCC 0,399)
adalah hasil evaluasi internal (split/CV) pada dataset gabungan DILIrank+LiverTox
yang mereka reproduksi dari Yang et al. (2024). HepaTwin mengikuti pola yang
persis sama (§1.2 UPSCALE.md): **held-out split/CV internal tetap wajib**
(itu bukan "external test", itu kebersihan ML dasar -- data latih tidak boleh
jadi data ukur performa akhir), tapi tidak ada dataset kedua dari luar yang
dikurasi kelompok riset lain untuk diuji silang.

**Konsekuensi metodologis yang jujur:** angka AUC yang dilaporkan (Arm A L1
0,7385, L2 0,7336) adalah performa pada partisi dari dataset gabungan yang
sama, bukan generalisasi yang divalidasi terhadap sumber data yang benar-benar
independen. Ini sesuai dengan keputusan Ketua Tim (K3, UPSCALE.md §2) dan
konsisten dengan cara model rujukan (Wibowo et al.) divalidasi -- bukan
standar yang lebih rendah dari paper acuan, tapi juga bukan jaminan yang
lebih kuat dari itu.

## 2. Ukuran dataset kecil

Arm A: 839 senyawa (setelah dedup InChIKey). Arm B: 1.253 senyawa. Keduanya
jauh di bawah skala dataset deep learning pada umumnya (ribuan-jutaan sampel).
Dropout & early stopping agresif (patience=30) dipertahankan sepanjang TU.7-9
justru karena kesadaran akan risiko overfitting pada skala ini.

## 3. Arm B (DILIrank+LiverTox) SIGNIFIKAN LEBIH BURUK dari Arm A -- temuan tak terduga

**Ini temuan paling penting dan paling berlawanan dengan ekspektasi** di
seluruh pipeline (lihat `07_comparison.md` untuk detail lengkap). UPSCALE.md
§3.3/§8 menduga Arm B (lebih besar, komposisi mirip dataset Wibowo et al.)
akan mendekati/melampaui Arm A. Hasil nyata: Arm A AUC 0,7385/0,7336 (L1/L2)
vs Arm B 0,6850/0,6672 -- **signifikan secara statistik** (Mann-Whitney U,
p<0,0001 di kedua skema), dikonfirmasi konsisten di GATNN-DNN **dan** baseline
RF terpisah.

Akar penyebab yang paling didukung bukti (audit `06_arm_b_construction.md`):
tingkat konflik label 18,6% pada 409 senyawa overlap DILIrank×LiverTox, dengan
94,7% konflik searah (DILIrank menandai positif, LiverTox menandai negatif,
untuk senyawa yang SAMA PERSIS). Skema `vLess-DILI-concern`-sebagai-positif
(gerbang B2) kemungkinan menyuntikkan noise label neto yang mengalahkan
manfaat ukuran sampel lebih besar. **Ini bukan bug pipeline** (diverifikasi:
mayoritas konflik pada nama identik, bukan salah resolusi SMILES) -- ini
karakteristik data yang genuinely butuh keputusan Farmasi (gerbang B2) untuk
diselesaikan, bukan sesuatu yang bisa "diperbaiki" lewat kode.

## 4. GNN vs tabular: hasil bercampur, bukan kesimpulan definitif

RF (ECFP4) dan GATNN-DNN nyaris seri di kedua arm (selisih AUC <0,015 di
semua kasus, dalam rentang 1 std). Berbeda dari temuan `dev-vedo` sebelumnya
(GNN generik kalah telak, gap 0,0535). Arsitektur GATv2Conv + edge feature
tampak lebih kompetitif dari GCN generik versi lama, tapi tidak cukup unggul
untuk jadi argumen kuat pemilihan arsitektur berbasis performa semata.
**Keputusan K1 (GATNN) tetap dipertahankan** atas dasar keputusan Ketua Tim
yang sudah dikonfirmasi sadar akan riwayat ini (lihat percakapan sesi
TU.12-13), bukan atas dasar keunggulan AUC yang meyakinkan.

## 5. Kalibrasi didemonstrasikan pada model 1-seed, bukan ensemble 5-seed

TU.10 (`10_calibration.md`) dan model produksi TU.14 memakai **satu** model
(seed=42, pre-registered dari daftar TU.9, bukan cherry-pick) untuk kalibrasi
dan ekspor produksi -- bukan ensemble/rata-rata dari 5 seed TU.9. Ini pilihan
pragmatis (ensembling 5 model butuh infrastruktur serving berbeda), bukan
keterbatasan fundamental, tapi berarti performa model produksi tunggal bisa
sedikit berbeda dari rata-rata 5-seed yang dilaporkan sebagai metrik utama.

## 6. Representasi amoxicillin-clavulanate -- fragmen tunggal (keputusan B4)

Pipeline standardisasi (`standardize.py`, `LargestFragmentChooser`) menolak
SMILES multi-fragmen. Amoxicillin-clavulanate direpresentasikan lewat
komponen amoxicillin saja di endpoint `edukasi_mendalam` (`simulation_
orchestrator.py`); komponen clavulanate (skor LiverTox tertinggi "A") masuk
Arm B secara terpisah sebagai entitas `livertox_only`. Skor yang ditampilkan
untuk mode edukasi amox-clav adalah **proksi dari komponen amoxicillin**,
bukan sinyal gabungan Augmentin yang sebenarnya -- didokumentasikan eksplisit
di kode & butuh keputusan Farmasi (gerbang B4) untuk penanganan jangka panjang.

## 7. Gerbang manusia B2-B5: seluruhnya masih PENDING REVIEW FARMASI

Atas instruksi pemilik repo (EXECUTION_PLAN_UPSCALE.md §14.1), gerbang B2
(skema label vLess), B3 (moot untuk Arm A), B4 (fragmen utama amox-clav), dan
B5 (nama 9 pola SMARTS) di-bypass dengan keputusan sementara AI supaya
pipeline bisa berjalan. **Tidak satu pun dari ini final** -- Definition of
Done (UPSCALE.md §11) tetap mensyaratkan tanda tangan Farmasi sebelum rilis
produksi sungguhan. Bukti konkret baru dari TU.12 (§3 di atas) memperkuat,
bukan melemahkan, urgensi review B2 secara khusus.

## 8. Tox21 (TU.16) dan FAERS (TU.17): TIDAK dikerjakan -- batasan waktu

Kedua stretch goal ini **tidak dikerjakan** dalam siklus kerja TU.0-TU.15.
Ini dinyatakan eksplisit sebagai **batasan waktu**, bukan disembunyikan atau
diklaim selesai. Keduanya secara eksplisit tidak memblokir Definition of Done
(UPSCALE.md §11 tidak mensyaratkan TU.16/17 selesai) dan tetap "menggunakan"
FAERS/Tox21 sesuai arahan awal tetap dianggap tidak terpenuhi untuk siklus
ini -- perlu dijadwalkan terpisah bila waktu kompetisi memungkinkan.

## 9. DeLong test diganti Mann-Whitney U (penyimpangan metodologis, dijelaskan)

UPSCALE.md §4.4/TU.13 meminta DeLong test, yang secara baku butuh 2 model
dibandingkan pada **sampel test yang identik**. Arm A dan Arm B punya sampel
senyawa yang berbeda, membuat DeLong tidak applicable secara statistik.
Mann-Whitney U dipakai sebagai gantinya (lihat `07_comparison.md`), valid
untuk 2 sampel independen -- penyimpangan ini didokumentasikan eksplisit,
bukan diam-diam diganti tanpa penjelasan.

## 10. Environment & reproduksibilitas

`.venv` proyek ini sempat korup sebagian di awal sesi kerja (file `.py`
hilang di beberapa package meski package besar seperti torch/rdkit utuh) --
diperbaiki lewat rebuild total sebelum TU.2 dimulai. Seluruh angka di laporan
ini dihasilkan SETELAH perbaikan tsb, dari environment yang terverifikasi
bekerja (`ml/requirements.txt` + `requirements.txt` root).
