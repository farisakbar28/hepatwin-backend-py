# Limitations & Batasan -- HepaTwin Mesin B (branch upscale)

Disusun TU.15, **diperbarui TU.22 (v3.0)** untuk merangkum seluruh temuan
TU.0-TU.22 termasuk revisi protokol validasi dari Ketua Tim
(`Panduan Training GATNN-DNN vs Konvensional.md`). Prinsip penulisan dokumen
ini: jujur apa adanya (Aturan Main #4/#5), tidak menyembunyikan kelemahan
demi presentasi yang lebih baik.

## 0. v3.0: Tahap 2 (nested CV + hold-out asli) sekarang jadi angka utama

K3 (tanpa external test) **dibalik** di v3.0 -- lihat UPSCALE.md §1.4. Angka
yang sekarang dianggap paling kredibel untuk laporan akhir adalah
`ml/reports/14_final_comparison.md` (evaluasi SATU KALI pada 167 senyawa
hold-out yang scaffold-disjoint dan tidak pernah disentuh proses tuning).
Angka Tahap 1 (CV internal seluruh data, `09c_arm_a_comparison.md`,
`07_comparison.md`) **tetap dipertahankan di laporan**, bukan dihapus --
diperlakukan sebagai konteks historis/proses, bukan lagi klaim performa utama.
AUC Tahap 2 (~0,64-0,69) lebih rendah dari Tahap 1 (~0,74-0,75) -- ini
**diprediksi dan diharapkan** (UPSCALE.md §13.7), bukan tanda kegagalan;
CV berulang di data yang sama secara wajar sedikit optimis dibanding ujian
pada data yang benar-benar belum pernah dilihat.

## 0.1 Insiden integritas ditemukan & diperbaiki selama persiapan TU.22

Saat menyiapkan hyperparameter final untuk TU.22, ditemukan bug: hyperparameter
GATNN-DNN yang di-*sample* di nested CV (TU.20) TIDAK PERNAH benar-benar
dikirim ke `train_gatnn()`/`GatnnDnn` -- keduanya memakai nilai hardcode,
membuat seluruh pencarian hyperparameter GATNN-DNN jadi no-op (baseline lain
tidak terpengaruh, sudah benar dari awal). Ini melanggar K9 (budget tuning
harus adil untuk semua model). **Diperbaiki** (kode + re-run penuh 10 fold
outer, ~70 menit), didokumentasikan lengkap di commit `fix(critical)` dan
`fix: perbarui TU.20/TU.21`. Angka final di dokumen ini SUDAH memakai hasil
yang terkoreksi. Kesimpulan utama (GATNN-DNN vs RF setara secara statistik)
**tidak berubah** setelah koreksi, tapi angka presisnya berubah -- keduanya
tetap dilaporkan demi transparansi proses, bukan cuma hasil akhirnya.

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

## 8. Status stretch goal: TU.16 selesai (hasil netral), TU.17 ditunda

**TU.16 (Tox21 multi-task auxiliary head): SUDAH dikerjakan dan selesai**
(lihat `08_tox21_ablation.md`) -- auxiliary head Tox21 terbukti **tidak
memberi manfaat signifikan** untuk AUC DILI (selisih dalam 1 std, MCC malah
sedikit turun). Dilaporkan apa adanya sebagai hasil netral, bukan dipoles.

**TU.17 (FAERS disproportionality signal): DITUNDA atas permintaan pemilik
repo** -- bukan batasan waktu murni, tapi keputusan sadar menunggu API key
openFDA resmi dari Ketua Tim (supaya bisa cover seluruh 1.253 obat Arm B
tanpa risiko kena limit harian API anonim). Kode & rencana implementasi sudah
disiapkan (lihat riwayat percakapan), tinggal dieksekusi begitu API key
tersedia. Tidak memblokir Definition of Done manapun.

## 9. DeLong test: valid & dipakai di TU.22, Mann-Whitney U tetap untuk Arm A vs Arm B

UPSCALE.md §4.4/TU.13 (Tahap 1) meminta DeLong test untuk Arm A vs Arm B --
tapi keduanya punya **sampel senyawa berbeda** (bukan model dibandingkan pada
test set yang sama), jadi DeLong secara statistik tidak applicable di sana.
**Mann-Whitney U** dipakai untuk kasus itu (lihat `07_comparison.md`), valid
untuk 2 sampel independen -- penyimpangan ini didokumentasikan eksplisit.

Di v3.0 (TU.22), DeLong test **benar-benar dipakai dan valid**: kelima model
(GATNN-DNN + 4 baseline) dievaluasi pada `holdout_set` yang **sama persis**,
jadi DeLong applicable sebagaimana mestinya (lihat `14_final_comparison.md`).

## 10.1 Kesimpulan akhir GNN vs tabular (TU.22, hold-out asli)

Pada `holdout_set` (167 senyawa, tidak pernah dilihat proses tuning):
GATNN-DNN AUC 0,6821, Random Forest 0,6914, LightGBM 0,6905 -- **semua
selisih dengan GATNN-DNN TIDAK signifikan** (DeLong p>0,46 untuk ketiganya).
GATNN-DNN cuma signifikan unggul dari Logistic Regression (p=0,0073). Ini
mengonfirmasi, dengan bukti paling kredibel yang tersedia (uji berpasangan
pada hold-out asli), kesimpulan yang konsisten di SEMUA tahap pengujian
sepanjang proyek ini: **GATNN-DNN dan model pohon (RF/LightGBM/XGBoost)
setara secara statistik** pada dataset sekecil ini (839-672 senyawa) --
bukan salah satu menang telak, dan CI 95% bootstrap yang lebar (~0,15-0,19)
di semua model jadi pengingat bahwa ukuran sampel hold-out (167) masih
kecil untuk klaim performa yang sangat presisi.

## 10. Environment & reproduksibilitas

`.venv` proyek ini sempat korup sebagian di awal sesi kerja (file `.py`
hilang di beberapa package meski package besar seperti torch/rdkit utuh) --
diperbaiki lewat rebuild total sebelum TU.2 dimulai. Seluruh angka di laporan
ini dihasilkan SETELAH perbaikan tsb, dari environment yang terverifikasi
bekerja (`ml/requirements.txt` + `requirements.txt` root).
