# PRODUCT REQUIREMENTS DOCUMENT (PRD)

## HepaTwin — Simulasi In-Silico 3D Liver Berbasis Kecerdasan Buatan & PBPK untuk Sistem Pendukung Keputusan Risiko Hepatotoksisitas

**Versi Dokumen:** 2.3 (Scientific Remediation Post-Audit Sumber 2026-08-06 — Development Baseline Validasi K2/K3/K6)

**Diturunkan dari:** *HepaTwin Draft Proposal GEMASTIK XIX 2026 New Version.pdf* (Kompetisi VIII: Pengembangan Perangkat Lunak, GEMASTIK XIX / 2026) + Audit PBPK Brutal 2021-2026 (referensi ilmiah/standar modern + foundational classics)

**Institusi:** Universitas Pendidikan Nasional, Denpasar (2026)

**Tim Pengusul:**

- **Muhammad Faris Akbar** (NIM 42330047) — *Ketua Tim / Teknologi Informasi* (Arsitektur Sistem, Frontend React, 3D Mesh & WebGL React Three Fiber, PBPK Solver SciPy)
- **Kadek Vedo Putra Soma Raharja** (NIM 42330053) — *Anggota / Teknologi Informasi* (Backend FastAPI, Model AI/ML PyTorch GATNN-DNN, SHAP Explainability, Basis Data Supabase)
- **Anggi Fitriani** (NIM 231012) — *Anggota / Farmasi* (Domain Expert Toksikologi & Farmakologi, Kurasi Dataset DILIrank 2.0 & LiverTox, Validasi Penskalaan Alometrik PBPK, Uji Validasi Pakar)

**Dosen Pembimbing:** Ir. Adie Wahyudi Oktavia Gama S.T., M.T., I.P.M., ASEAN Eng. (NIDN 0819108602)

**Status Dokumen:** *Approved as Development Baseline — BUKAN klaim validasi klinis final; pending K2/K3/K6 & review Farmasi*

---

## CHANGELOG v2.1 → v2.3 (2026-08-06)

> **Alasan update v2.3:** Audit sumber PRD v2.1 menemukan beberapa *source mismatch* yang harus diremediasi tanpa membongkar arsitektur besar yang sudah diimplementasikan developer (React/FastAPI, GATNN-DNN, SHAP, PBPK 4-kompartemen, Supabase, Couinaud WebGL). Revisi v2.3 berfokus pada **koreksi klaim ilmiah, penajaman disclaimer, pemisahan sumber eksternal vs kurasi internal, dan pembaruan formulasi/konstanta PBPK yang lebih defensible secara farmakologi**. Dokumen ini **tidak mengklaim validasi klinis final**; statusnya adalah *development baseline* yang harus dibuktikan dengan K2/K3/K6, benchmark, audit dataset, dan validasi pakar.

| Bagian | Perubahan v2.3 | Sumber pembetulan | Status |
|---|---|---|---|
| Status dokumen | Turunkan klaim dari “Production Ready/100% valid” menjadi **development baseline pending K2/K3/K6** | FDA CM&S credibility guidance [28] | **Valid secara tata-kelola** |
| §8.1 SHAP | Arsitektur SHAP **tetap dipertahankan**; sitasi SHAP diperbaiki ke Lundberg & Lee [27]. InterDILI [10] hanya mendukung kebutuhan interpretabilitas/attention, bukan sumber SHAP. | Lundberg & Lee 2017 [27], InterDILI [10] | **Valid setelah koreksi sitasi** |
| §8.2 Volume & aliran | `V_P` dibuat berbasis BB (`0.043×BB`), `V_L=0.0257×BB`, `Q_L=90×(BB/70)^0.75×age_factor`; baseline 90 L/h tetap sebagai prior dewasa 70 kg. | Soejima [20], DallphinAtoM [22], parameter PBPK terbuka [23, 24, 31] | **Lebih defensible; masih model Fase 1** |
| §8.2 %BF | Tambah formula anak `≤15 tahun` dan formula dewasa `≥16 tahun`, bukan satu formula untuk semua usia. | Deurenberg [21] | **Valid** |
| §8.2 BMI/Cl | **Hapus default reduksi Cl -20% pada BMI≥30**. BMI≥30 menjadi `metabolic_risk_flag`, bukan pengurang clearance otomatis. | Ghabril [17] menyatakan tidak ada bukti altered PK per se → DILI risk | **Koreksi major** |
| §8.2 Kp_R | Formula Kp_R tetap ada sebagai heuristic karena sudah ada implementasi, tetapi exponent dibuat lebih konservatif (`0.25`, bukan `0.5`) dan diberi label **visual heuristic, bukan formula klinis**. | Coutinho [24], Holt/Nagar/Korzekwa [31], SwissADME [25] | **Asumsi desain terkendali** |
| §8.2 Exposure | `Cmax/AUC` tidak lagi disebut “exposure magnitude”; diganti menjadi `shape_ratio_h_inv`. Kategori paparan memakai `exposure_index = log1p(Cmax_L)+log1p(AUC_L)` + kuantil 33/66 dari calibration sweep internal. | Olaparib [26] & Rilzabrutinib [32] menunjukkan threshold PK bersifat drug-specific, bukan universal | **Koreksi major** |
| §8.3 Couinaud | Mapping pola cedera → segmen Couinaud tetap untuk visualisasi, tetapi diberi label **heuristik pedagogis makrovaskular**, bukan lokalisasi histologis klinis. | Couinaud [13], AASLD [19], LiverTox [18] | **Valid setelah disclaimer** |
| §8.4 Dataset | Pisahkan klaim sumber eksternal dan hasil kurasi internal: DILIrank [14] = 1.336 drug + label; 1.231 simulatable/105 non-simulatable/40 kolom = hasil kurasi HepaTwin. | FDA DILIrank [14], PubChem [15] | **Koreksi atribusi** |
| §9.4 Demo APAP | Ubah skenario overdose dari **4.000 mg** menjadi **10.500 mg untuk 70 kg (150 mg/kg)**. 4.000 mg hanya disebut dosis harian maksimum/tinggi, bukan acute overdose. | LiverTox APAP [29], MSD/Merck [30], Jaeschke [3] | **Koreksi fatal** |
| §11 | Tambah credibility plan berbasis FDA 2023 dan prinsip risk-informed credibility; tidak lagi menyatakan validasi “otomatis memadai”. | FDA [28] | **Valid tata-kelola** |
| §14 | Referensi [26] dipecah: Olaparib [26] dan Rilzabrutinib [32]; tambah SHAP [27], FDA CM&S [28], LiverTox APAP [29], MSD APAP [30], Holt/Nagar/Korzekwa [31]. | Sumber terbuka/otoritatif | **Valid** |

---

## DAFTAR ISI

1. **RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)**
2. **LATAR BELAKANG & PERNYATAAN MASALAH (PROBLEM STATEMENT)**
   - 2.1 Konteks Klinis & Attrition Rate Pengembangan Obat
   - 2.2 Keterbatasan Metode Uji Konvensional (In-Vivo & In-Vitro)
   - 2.3 Keterbatasan Pendekatan In-Silico Kontemporer
   - 2.4 Solusi yang Diajukan: HepaTwin & Relevansi GEMASTIK XIX 2026
3. **TUJUAN PRODUK & METRIK KEBERHASILAN (OBJECTIVES & SUCCESS METRICS)**
   - 3.1 Tujuan Utama Perangkat Lunak
   - 3.2 Manfaat dan Dampak Bertahap
   - 3.3 Metrik Keberhasilan Kuantitatif (Acceptance Metrics)
4. **RUANG LINGKUP & BATASAN TEGAS PRODUK (SCOPE & EXPLICIT BOUNDARIES)**
   - 4.1 Dalam Ruang Lingkup (In-Scope / Fase 1 - Senyawa Tunggal)
   - 4.2 Di Luar Ruang Lingkup (Out of Scope / Future Work - Fase 2)
5. **PERSONA PENGGUNA & USE CASE UTAMA (USER PERSONAS & USE CASES)**
   - 5.1 Profil Persona Pengguna
   - 5.2 Tabel Use Case dan Skenario Utama
6. **KEBUTUHAN FUNGSIONAL & NON-FUNGSIONAL (FR & NFR)**
   - 6.1 Kebutuhan Fungsional (Functional Requirements)
   - 6.2 Kebutuhan Non-Fungsional (Non-Functional Requirements)
7. **ARSITEKTUR SISTEM & STACK TEKNOLOGI (SYSTEM ARCHITECTURE & TECH STACK)**
   - 7.1 Diagram Arsitektur Modular Paralel-Asinkron
   - 7.2 Spesifikasi Komponen Stack Teknologi
   - 7.3 Pemisahan Artefak Statis Backend (Dataset Kurasi vs Bobot Model)
8. **SPESIFIKASI MENDALAM MESIN ILMIAH, AI, PBPK, DAN LAPISAN FUSI**
   - 8.1 Mesin Prediksi AI (Graph Attention Network - Dense Neural Network / GATNN-DNN)
   - 8.2 Mesin Farmakokinetika Mekanistik (PBPK 4-Kompartemen & Penskalaan Alometrik) — **UPDATED v2.3**
   - 8.3 Lapisan Fusi Rule-Based & Pemetaan Spasial Segmen Couinaud (I–VIII) — **UPDATED v2.3**
   - 8.4 Statistik Cakupan Dataset Terkurasi (DILIrank 2.0 + Enrichment LiverTox) — **UPDATED v2.3**
   - 8.5 Uji Prinsip Desain Inti ("Apa yang Rusak Jika Komponen Dihapus?")
9. **SPESIFIKASI ANTARMUKA PENGGUNA (UI/UX SPECIFICATIONS)**
   - 9.1 Layout Dasbor Utama dengan Top Bar dan Footer
   - 9.2 Layout Tiga Panel Terintegrasi
   - 9.3 Mekanisme Popup Disclaimer Checklist
   - 9.4 Skenario Visual Verifikasi Simulasi Kontras (Acetaminophen vs Ibuprofen)
10. **ALUR KERJA PENGGUNA AKHIR (END-TO-END USER WORKFLOW)**
11. **REGULASI, CREDIBILITY ASSESSMENT, DAN MEDICAL DISCLAIMER — UPDATED v2.3**
    - 11.1 Context of Use (CoU) dan Credibility Plan
    - 11.2 Penanganan Kasus dan Batasan Validitas (Medical Disclaimer)
12. **METODOLOGI PENGEMBANGAN AGILE SCRUM (8 SPRINTS, 11 MINGGU)**
13. **MANAJEMEN RISIKO & BACKLOG VALIDASI FARMASI — UPDATED v2.3**
14. **DAFTAR REFERENSI ILMIAH RESMI — UPDATED v2.3 (33 refs aktif)**
15. **LAMPIRAN: DEFINITION OF DONE (DOD) & ACCEPTANCE CRITERIA PER MODUL — UPDATED v2.3**

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

**HepaTwin** adalah aplikasi berbasis web interaktif yang bertindak sebagai **Sistem Pendukung Keputusan (Decision Support System / DSS) praklinis in-silico** untuk menyimulasikan, memprediksi, dan memvisualisasikan risiko **hepatotoksisitas obat (Drug-Induced Liver Injury / DILI)** pada anatomi hati manusia 3D.

Berbeda dari perangkat lunak konvensional yang hanya memberikan skor numerik atau klasifikasi biner statis, HepaTwin mengintegrasikan dua mesin komputasi canggih yang berjalan secara **paralel-asinkron dan independen**:

1. **Mesin Prediksi AI (Graph Attention Network + Dense Neural Network / GATNN-DNN):** Memproses graf topologi molekul dan sidik jari ECFP4 untuk memprediksi probabilitas toksisitas hepatik secara akurat sekaligus memberikan interpretabilitas kimiawi berbasis **SHAP (SHapley Additive exPlanations)** yang menyorot sub-struktur kimia pemicu toksisitas (*toxicophore*).

2. **Mesin Farmakokinetika Mekanistik (Physiologically Based Pharmacokinetic / PBPK 4-Kompartemen):** Menyelesaikan sistem Persamaan Diferensial Biasa (Ordinary Differential Equations / ODE) untuk menghasilkan kurva paparan konsentrasi obat di hati terhadap waktu ($C_{\text{hati}}(t)$ selama 24 jam) dengan parameter fisiologis yang dikonversi secara otomatis dari kovariat pasien spesifik (usia, jenis kelamin, berat badan, dan tinggi badan) menggunakan **penskalaan alometrik deterministik**.

Kedua keluaran mesin dipadukan pada **Lapisan Fusi (Rule-Based Fusion Layer)** di backend yang menentukan daftar segmen hati yang terdampak berdasarkan kurasi offline **DILIrank 2.0** dan monograf **LiverTox**, serta menentukan warna peringatan (Hijau, Kuning, Merah) dan kecepatan berkedip (*blinking rate*) pada **model 3D anatomi hati makroskopis berstandar 8 Segmen Couinaud (I–VIII)** yang dirender interaktif melalui WebGL (React Three Fiber).

> **PRINSIP NON-NEGOSIABEL PRODUK:**
>
> HepaTwin merupakan perangkat lunak skrining awal dan triase praklinis yang **MURNI BERSIFAT IN-SILICO**. Produk ini **BUKAN** merupakan perangkat diagnosis klinis langsung untuk pasien, **BUKAN** pedoman terapi medis, dan **TIDAK MENGGANTIKAN** uji laboratorium basah (*in-vitro* dan *in-vivo*) maupun uji klinis yang diatur oleh otoritas regulator kesehatan resmi (BPOM Republik Indonesia / FDA Amerika Serikat). Klasifikasi risiko produk diposisikan pada *Context of Use* berisiko rendah berdasarkan credibility plan berbasis FDA CM&S guidance [28].

---

## 2. LATAR BELAKANG & PERNYATAAN MASALAH (PROBLEM STATEMENT)

### 2.1 Konteks Klinis & Attrition Rate Pengembangan Obat

Proses penemuan dan pengembangan obat baru dihadapkan pada tingkat kegagalan (*attrition rate*) yang sangat tinggi pada fase uji klinis, di mana hampir **90% kandidat obat yang memasuki tahapan uji klinis pada manusia gagal dipasarkan** [1]. Salah satu penyebab utama kegagalan kandidat obat dalam fase uji klinis, sekaligus alasan utama penarikan obat dari peredaran pasca-pemasaran (*post-market withdrawal*), adalah **Drug-Induced Liver Injury (DILI)** atau cedera hati akibat obat [1, 2].

Kondisi ini berkaitan erat dengan fisiologi hati sebagai organ primer biotransformasi xenobiotik yang memetabolisme sebagian besar senyawa kimia melalui dua fase utama sebelum diekskresikan:

- **Metabolisme Fase I:** Oksidasi atau reduksi yang umumnya dimediasi oleh super-keluarga enzim sitokrom P450 (*Cytochrome P450* / CYP) untuk mengubah senyawa lipofilik menjadi metabolit yang lebih polar.
- **Metabolisme Fase II:** Konjugasi metabolit Fase I dengan molekul polar seperti glutation atau asam glukuronat sehingga netral dan dapat diekskresikan melalui empedu atau urin.

Pada sebagian senyawa obat, reaksi Fase I menghasilkan **metabolit reaktif yang sangat toksik** apabila kapasitas konjugasi Fase II terlampaui atau menjadi jenuh. **Acetaminophen (Parasetamol)** merupakan contoh patofisiologi DILI yang paling banyak dipelajari: pada kondisi dosis terapeutik normal, metabolit diregulasi dengan baik; namun pada kondisi overdosis akut, jalur konjugasi sulfatasi dan glukuronidasi menjadi jenuh, sehingga proporsi obat yang jauh lebih besar dioksidasi oleh enzim **CYP2E1** menjadi senyawa reaktif *N-acetyl-p-benzoquinone imine* (**NAPQI**). Ketika cadangan glutation hepatik mengalami deplesi kritis, NAPQI berikatan kovalen dengan protein seluler dan protein mitokondria, memicu stres oksidatif, disfungsi mitokondria, peradangan steril, hingga nekrosis hepatosit sentrilobular [3].

### 2.2 Keterbatasan Metode Uji Konvensional (In-Vivo & In-Vitro)

Metode evaluasi hepatotoksisitas konvensional saat ini masih memiliki kelemahan mendasar:

- **Uji In-Vivo pada Hewan Coba:** Membutuhkan biaya besar, durasi panjang, serta menghadapi tekanan etis terkait prinsip **3R (*Replacement, Reduction, Refinement*)** yang mendorong transisi ke arah *New Approach Methodologies* (NAMs) tanpa hewan uji [5]. Lebih penting lagi, biologi hewan coba tidak selalu relevan dengan manusia: studi Atkins dkk. (2020) terhadap 108 obat onkologi membuktikan bahwa **nilai prediktif positif (PPV) median model hewan hanya sekitar 0,65** terhadap toksisitas klinis pada manusia [6].
- **Uji In-Vitro (Kultur Hepatosit 2D & Organoid 3D):** Data endpoint in-vitro sangat penting untuk deteksi dini DILI dan dapat dipadukan dengan machine learning [4], tetapi endpoint terpisah tersebut tetap tidak sepenuhnya menggantikan dinamika sistemik antarorgan, perfusi, dan ADME tubuh manusia yang menjadi domain model PBPK/multiscale [2, 11].

### 2.3 Keterbatasan Pendekatan In-Silico Kontemporer

Perangkat lunak komputasional *in-silico* yang ada saat ini juga menunjukkan kesenjangan fitur yang nyata ketika diterapkan pada konteks riset dan pendidikan farmasi di Indonesia:

- **Perangkat Lunak Komersial (misal: DILIsym, Simcyp, NONMEM):** Memerlukan biaya lisensi tahunan yang sangat mahal (puluhan hingga ratusan juta rupiah), membutuhkan parameter input *in-vitro* ekstensif yang sulit diperoleh laboratorium berdaya terbatas, serta tidak menyediakan visualisasi spasial 3D anatomi hati manusia secara intuitif.
- **Platform Properti ADMET (misal: GastroPlus, ADMET Predictor):** Hanya berfokus pada simulasi numerik atau prediksi properti tanpa jembatan visualisasi anatomi organ maupun kemudahan penggunaan bagi pengguna non-matematikawan.
- **Platform Open-Source (misal: ProTox-II):** Hanya memberikan luaran berupa klasifikasi biner (toksik / tidak toksik) atau skor probabilitas statis tanpa dinamika konsentrasi temporal PBPK, tanpa personalisasi kovariat pasien secara deterministik, dan tanpa pemetaan spasial ke segmen vaskular hati.

| Fitur / Kriteria | DILIsym (Komersil) | ProTox-II (Open-Src) | GastroPlus (Komers) | HepaTwin (Solusi) |
| :--- | :--- | :--- | :--- | :--- |
| Biaya Lisensi | Sangat Mahal | Gratis | Sangat Mahal | Gratis (Open Web) |
| Prediksi AI (GNN) | Tidak Ada (Mekan.) | Ya (ML Tradisional) | Tidak Ada | Ya (GATNN-DNN+SHAP) |
| Simulasi PBPK ODE | Ya (Sangat Kompleks) | Tidak Ada | Ya | Ya (4-Kompartemen) |
| Kovariat Pasien | Input Manual Param. | Tidak Ada | Input Manual | Alometrik Otomatis |
| Visual 3D Hati | Tidak Ada | Tidak Ada | Tidak Ada | Ya (8 Segmen Couinaud) |
| Explainability | Tidak Relevan | Terbatas | Tidak Relevan | Ya (SHAP Toxicoph) |

### 2.4 Solusi yang Diajukan: HepaTwin & Relevansi GEMASTIK XIX 2026

HepaTwin hadir sebagai solusi atas kesenjangan tersebut dengan menghadirkan platform Sistem Pendukung Keputusan (*Decision Support System*) berbasis web yang menggabungkan AI GNN, pemodelan PBPK mekanistik berpenyesuaian alometrik, dan visualisasi 3D anatomi makroskopis hati berdasarkan 8 Segmen Couinaud.

Sejalan dengan tema GEMASTIK XIX / 2026, **"Berdampak, Inklusif, dan Berkelanjutan Menuju Masyarakat Cerdas"**:

- **Berdampak:** Menjadi instrumen triase praklinis berbiaya rendah yang mendukung pengurangan hewan uji (prinsip 3R) dan mempercepat penyaringan kandidat obat aman di Indonesia.
- **Inklusif:** Berbasis web terbuka, gratis, dan ringan (tanpa butuh instalasi atau superkomputer), sehingga dapat diakses secara merata oleh peneliti kampus, dosen, guru, mahasiswa/pelajar, hingga industri farmasi kecil-menengah.
- **Berkelanjutan:** Arsitektur modular dan basis data cloud-native (Supabase) memungkinkan perluasan fitur di masa depan (polifarmasi, interaksi obat-obat, dan perluasan ke organ lain seperti ginjal atau jantung).

---

## 3. TUJUAN PRODUK & METRIK KEBERHASILAN (OBJECTIVES & SUCCESS METRICS)

### 3.1 Tujuan Utama Perangkat Lunak

1. **Platform Triase In-Silico Terkurasi:** Menyediakan layanan evaluasi hepatotoksisitas untuk 1.231 senyawa obat bermuatan struktur yang terverifikasi PubChem dan berstatus `is_simulatable = TRUE` dari dataset FDA **DILIrank 2.0** [14].

2. **Sinergi Paralel AI + PBPK:** Mengintegrasikan model *Graph Attention Network + Dense Neural Network* (**GATNN-DNN**) [9] dan model PBPK 4-kompartemen [11] yang beroperasi secara paralel-asinkron, dipadukan pada Lapisan Fusi untuk penentuan risiko komprehensif.

3. **Visualisasi Anatomi 3D Couinaud:** Menampilkan anatomi hati 3D berbasis **8 Segmen Couinaud (I–VIII)** [13] dengan overlay hotspot semitransparan berkedip (*blinking*) yang menyorot **prioritas visual/pola risiko pedagogis**, bukan lokalisasi cedera klinis.

4. **Personalisasi Alometrik Otomatis:** Mengonversi kovariat fisik pasien (usia, jenis kelamin, berat badan, tinggi badan) secara langsung menjadi parameter fisiologis ODE melalui penskalaan alometrik deterministik [12], mempertimbangkan pengaruh usia, jenis kelamin, dan komorbiditas metabolik (BMI) [16, 17].

### 3.2 Manfaat dan Dampak Bertahap

- **Jangka Pendek (*Preclinical Screening & Educational Tool*):** Media skrining cepat dan gratis bagi akademisi dan peneliti sebelum uji lab basah, sekaligus platform pembelajaran interaktif bagi mahasiswa dan pelajar di bidang farmakologi dan toksikologi klinik.
- **Jangka Menengah (*R&D Lead Optimization*):** Alat bantu optimalisasi proses *lead optimization* pada industri farmasi lokal melalui analisis risiko toksisitas berdasarkan variasi dosis dan profil demografi pengguna.
- **Jangka Panjang (*Personalized Medicine Support Foundation*):** Pondasi bagi sistem pendukung keputusan medis masa depan yang terintegrasi dengan Rekam Medis Elektronik (RME) untuk penyesuaian regimen dosis aman bagi pasien dengan gangguan fungsi organ atau komorbiditas metabolik.

### 3.3 Metrik Keberhasilan Kuantitatif (Acceptance Metrics)

| # | Kriteria Keberhasilan / Metrik | Target Acceptance Criteria | Cara Pembuktian / Validasi |
| :--- | :--- | :--- | :--- |
| 1 | **Cakupan Senyawa Simulatable** | **1.231 senyawa** (`is_simulatable = TRUE`) dari 1.336 senyawa sumber DILIrank 2.0 siap diuji tanpa error | Uji kueri otomatis pada tabel `hepatwin_compounds` di Supabase + lampiran hash/log kurasi PubChem internal |
| 2 | **Kinerja Waktu Respon API (NFR-02)** | Total waktu inferensi GATNN-DNN + solver ODE PBPK 24 jam **≤ 5 detik** per simulasi | Benchmark uji beban dan latensi pada server backend produksi |
| 3 | **Kinerja Visualisasi 3D WebGL (NFR-01)** | Frame rate rendering model 3D hati dan animasi hotspot **≥ 30 FPS** pada browser desktop standar | Pengujian frame rate menggunakan Chrome DevTools pada GPU terintegrasi standar |
| 4 | **Stabilitas Numerik & Distribusi Paparan PBPK [UPDATED v2.3]** | **0% kegagalan konvergensi** solver ODE Runge-Kutta untuk 10.000 kombinasi **+ distribusi `LOW/MODERATE/HIGH` berbasis `exposure_index` dilaporkan** | Automation unit test 10.000 kombinasi + **calibration sweep v2.3** (`reports/pbpk_exposure_calibration_v2_3.md`) dengan hash config/dataset |
| 5 | **Validasi Kredibilitas Pakar Farmasi** | Verifikasi konstanta alometrik & pemetaan segmen Couinaud tervalidasi oleh spesialis Farmasi | Lembar persetujuan dan hasil validasi pakar farmakologi (Anggi Fitriani & dosen pembimbing) + **checklist K1-K6** |

---

## 4. RUANG LINGKUP & BATASAN TEGAS PRODUK (SCOPE & EXPLICIT BOUNDARIES)

Untuk menjamin keandalan klinis, kredibilitas komputasi, dan mencegah kebingungan pengguna, ruang lingkup HepaTwin Fase 1 ditetapkan melalui batasan yang **sangat tegas dan tidak dapat dinegosiasikan**:

### 4.1 Dalam Ruang Lingkup (In-Scope / Fase 1 - Senyawa Tunggal)

1. **Fokus Senyawa Tunggal (Monoterapi):** Sistem **HANYA** menyimulasikan dan memprediksi paparan satu senyawa obat tunggal dalam satu kali eksekusi simulasi [14].

2. **Model Dosis Tunggal / Bolus Akut:** Simulasi PBPK merepresentasikan pemberian **satu kali dosis bolus akut (satuan mg)** pada awal waktu ($t = 0$). Sistem tidak meminta maupun memproses input frekuensi, interval pemakaian, atau regimen dosis berulang.

3. **Pipeline Input Deterministik Berbasis Nama (Daftar Tertutup):**
   - Pengguna **WAJIB** memilih senyawa dari daftar *autocomplete* yang tertutup, yang **HANYA** memuat **1.231 senyawa berstatus `is_simulatable = TRUE`** (memiliki struktur kimia molekul kecil yang valid dan identitas terverifikasi PubChem).
   - Sistem **MENOLAK TEGAS DAN MEMBLOKIR** input nama bebas yang tidak ada dalam daftar, teks sembarangan, ataupun input string SMILES bebas dari pengguna untuk mencegah halusinasi struktur kimia atau senyawa fiktif.

4. **Kovariat Pasien Alometrik Sederhana:** Sistem hanya menerima empat kovariat demografis: **Usia (tahun)**, **Jenis Kelamin (Laki-laki / Perempuan)**, **Berat Badan (kg)**, dan **Tinggi Badan (cm)**. Seluruhnya dikonversi di backend menjadi parameter fisiologis PBPK melalui penskalaan alometrik deterministik tanpa menggunakan data genomik, penanda genetik, atau asumsi etnisitas.

### 4.2 Di Luar Ruang Lingkup (Out of Scope / Future Work - Fase 2)

1. **Polifarmasi & Drug-Drug Interaction (DDI):** Interaksi antar-obat, kompetisi enzim CYP, atau induksi metabolisme akibat penggabungan 2 obat atau lebih **TIDAK TERMASUK** dalam scope Fase 1 dan diposisikan sebagai penelitian lanjutan (*Future Work*).

2. **Regimen Dosis Berulang:** Pemodelan akumulasi obat akibat dosis berulang tiap 8 jam / 12 jam memerlukan penambahan *dosing events* pada solver ODE dan dimasukkan ke *Future Work*.

3. **105 Senyawa Biologik Tanpa Struktur Molekul Kecil:** Sebanyak 105 senyawa pada DILIrank 2.0 bertipe antibodi monoklonal, protein terapeutik, atau agen biologik (yang tidak memiliki Canonical SMILES/InChIKey molekul kecil) diberi status `is_simulatable = FALSE`. Senyawa ini **tetap tersimpan di database** demi keutuhan 1.336 baris dataset, namun **TIDAK TAMPIL di autocomplete** dan **TIDAK DAPAT DISIMULASIKAN**.

4. **Visualisasi Mikroanatomi Hati:** Visualisasi pada level mikroanatomi seperti lobulus hati, triad portal, zona asinus mikroskopis (Zona 1/2/3 secara seluler), maupun hepatosit individu **DIKELUARKAN** dari render aktif demi menjaga stabilitas GPU peramban klien, dan dipertahankan hanya sebagai landasan teori pedagogis.

5. **Deformasi Geometri Mesh Real-Time:** Untuk menjamin rendering browser di atas 30 FPS, prioritas risiko visual disajikan dalam bentuk **overlay hotspot bola semitransparan berkedip (*blinking*)**, **TANPA** deformasi vertex geometri atau perubahan morfologi jaringan mesh organ secara real-time. Tekstur hati utama tetap dalam anatomi sehat realistis.

6. **[BARU v2.3] PBPK Non-Linear (Km/Vmax, NAPQI depletion):** Model Fase 1 **sengaja linear tanpa saturasi Michaelis-Menten**; akumulasi NAPQI/glutation tidak dimodelkan — Future Work (lihat §8.2.7).

---

## 5. PERSONA PENGGUNA & USE CASE UTAMA (USER PERSONAS & USE CASES)

### 5.1 Profil Persona Pengguna

1. **Persona 1: Peneliti Biomedis / Farmakolog Praklinis (Dr. Hendra, 38 tahun)**
   - *Konteks:* Peneliti di laboratorium universitas yang sedang menyaring kandidat obat turunan sebelum memutuskan untuk melakukan pengujian *in-vitro/in-vivo*.
   - *Kebutuhan:* Ingin mengetahui profil paparan hepatotoksisitas secara cepat dan melihat gugus kimia mana yang memicu toksisitas (*SHAP explanation*).

2. **Persona 2: Dosen & Mahasiswa Farmasi (Siti, 21 tahun — Mahasiswa S1 Farmasi)**
   - *Konteks:* Belajar mata kuliah Farmakokinetika dan Toksikologi Klinik, kesulitan membayangkan hubungan antara overdosis parasetamol, kinetika saturasi, dan kerusakan zonal hati.
   - *Kebutuhan:* Alat pembelajaran interaktif visual-spasial 3D yang memperlihatkan bagaimana perbedaan dosis (terapi vs overdose) memengaruhi kurva PBPK dan hotspot pedagogis pada segmen hati Couinaud.

3. **Persona 3: Apoteker R&D Industri Kecil-Menengah (Apt. Budi, 32 tahun)**
   - *Konteks:* R&D di industri farmasi lokal yang tidak memiliki anggaran untuk membeli lisensi software PK/PD komersial.
   - *Kebutuhan:* Platform penyaringan awal (*preclinical triage tool*) yang valid secara ilmiah untuk menguji keamanan penyesuaian formulasi dosis bolus tunggal.

### 5.2 Tabel Use Case dan Skenario Utama

| Aktor | Use Case | Skenario Utama | Kondisi Akhir |
| :--- | :--- | :--- | :--- |
| **Peneliti / Apoteker / Mahasiswa** | **UC-01:** Cari Senyawa & Input Profil Pasien | Mengetik nama obat INN pada *search bar*, memilih senyawa dari daftar *autocomplete* (`is_simulatable = TRUE`), lalu memasukkan dosis bolus tunggal (mg), usia, berat badan, tinggi badan, dan jenis kelamin. | Parameter terverifikasi valid, SMILES dan deskriptor molekul berhasil dibaca dari basis data lokal Supabase. |
| **Peneliti / Apoteker / Mahasiswa** | **UC-02:** Jalankan Simulasi Toksisitas Paralel | Menekan tombol **"Simulasikan Toksisitas"**. Backend FastAPI memicu inferensi GATNN-DNN (PyTorch) dan solver ODE PBPK (SciPy) secara paralel-asinkron. | Probabilitas DILI AI, explainability SHAP, dan kurva temporal $C_{\text{hati}}(t)$ PBPK selesai dihitung dalam ≤ 5 detik dan dikirim ke frontend. |
| **Peneliti / Apoteker / Mahasiswa** | **UC-03:** Analisis Visualisasi 3D Makroskopis | Memutar, memperbesar, dan menginspeksi model hati 3D pada panel kanan. Hotspot pedagogis Couinaud (misal: Segmen V–VIII untuk pola hepatocellular acetaminophen) menyorot warna berkedip dengan label `PEDAGOGICAL_HEURISTIC`. | Pengguna memahami pola risiko visual in-silico secara intuitif tanpa menganggapnya sebagai lokalisasi anatomi klinis. |
| **Peneliti / Apoteker / Mahasiswa** | **UC-04:** Tinjau Kurva Paparan & Explainability SHAP | Menganalisis kurva temporal konsentrasi hati $C_{\text{hati}}(t)$ berdurasi 24 jam dan mengamati visualisasi struktur kimia ber-highlight merah (toxicophore) dari keluaran SHAP. | Pengguna memahami dinamika paparan relatif (rasio Cmax/AUC) serta mengidentifikasi gugus atom spesifik pemicu risiko DILI. |
| **Peneliti / Apoteker / Mahasiswa** | **UC-05:** Popup Disclaimer Checklist & Unduh Laporan | Saat tombol "Simulasikan Toksisitas" diklik, popup disclaimer checklist muncul. Setelah semua checkbox disetujui, simulasi berjalan. Setelah simulasi selesai, tombol "Unduh Laporan PDF" di Top Bar menjadi aktif untuk mengunduh PDF dokumentasi. | Popup disclaimer tertutup, hasil simulasi tampil, dan laporan PDF tersimpan di perangkat pengguna sebagai catatan praklinis in-silico yang sah dan terdokumentasi. |

---

## 6. KEBUTUHAN FUNGSIONAL & NON-FUNGSIONAL (FR & NFR)

### 6.1 Kebutuhan Fungsional (Functional Requirements - FR)

- **FR-01 (Pencarian Senyawa Terkurasi):** Sistem wajib menyediakan input autocomplete yang secara ketat bersumber dari daftar tertutup 1.231 senyawa DILIrank 2.0 berstatus `is_simulatable = TRUE` dan terverifikasi PubChem. Sistem wajib menolak dan memblokir input di luar daftar tersebut.

- **FR-02 (Input Dosis & Kovariat Demografis):** Sistem wajib menerima input numerik dosis bolus tunggal (mg) serta empat kovariat pasien: Usia (0–100 tahun), Berat Badan (kg), Tinggi Badan (cm), dan Jenis Kelamin (Laki-laki/Perempuan).

- **FR-03 (Inferensi AI GATNN-DNN & SHAP):** Sistem wajib memproses graf molekul dan sidik jari ECFP4 melalui model statis GATNN-DNN untuk menghasilkan probabilitas hepatotoksisitas (0–100%) dan vektor atribusi SHAP.

- **FR-04 (Simulasi ODE PBPK 4-Kompartemen):** Sistem wajib menyelesaikan sistem ODE PBPK 4-kompartemen selama durasi 24 jam berdasarkan parameter fisiologis yang dikonversi dari kovariat pasien via penskalaan alometrik. **Wajib melaporkan metrik Cmax, AUC, cmax_auc_ratio, dan exposure_category.**

- **FR-05 (Visualisasi 3D 8 Segmen Couinaud):** Sistem wajib menampilkan model anatomi hati 3D interaktif berstruktur 8 Segmen Couinaud (I–VIII), dengan overlay bola hotspot semi-transparan berkedip yang warna dan kecepatannya diatur oleh Lapisan Fusi.

- **FR-06 (Kurva Paparan Temporal & Panel SHAP):** Sistem wajib menyajikan grafik konsentrasi hati terhadap waktu ($C_{\text{hati}}$ vs $t$) serta panel visualisasi 2D molekul dengan penyorotan warna pada atom/gugus dengan kontribusi SHAP tertinggi.

- **FR-07 (Persetujuan Disclaimer & Ekspor Laporan PDF):** Sistem wajib memuat kotak *Medical Disclaimer* permanen yang harus disetujui pengguna, serta fitur unduh laporan ringkasan simulasi dalam format PDF.

### 6.2 Kebutuhan Non-Fungsional (Non-Functional Requirements - NFR)

- **NFR-01 (Kinerja Rendering 3D WebGL):** Rendering model 3D hati beserta animasi *blinking hotspot* harus berjalan lancar dengan frame rate minimal **30 FPS** pada peramban web modern tanpa menimbulkan lag pada perangkat desktop standar.

- **NFR-02 (Waktu Respon Komputasi):** Total waktu proses dari permintaan simulasi dikirim hingga hasil inferensi GATNN-DNN dan penyelesaian ODE PBPK kembali ke klien tidak boleh melebihi **5 detik** (rata-rata target ≤ 3 detik). **PBPK saja ~0.1-0.3 detik (SciPy), AI ~0.5-1.5 detik; tail SHAP ditangani terpisah (lihat §11.2).**

- **NFR-03 (Aksesibilitas, Keamanan & Offline Determinism):**
  - Sistem harus dapat diakses melalui web publik dengan protokol HTTPS penuh.
  - Seluruh deskriptor kimia dan monograf tersimpan secara lokal di basis data internal Supabase sehingga **bebas dari risiko downtime atau rate-limit API pihak ketiga saat runtime**.
  - Akses basis data diamankan menggunakan **Row Level Security (RLS)** dan caching di sisi klien.
  - **[BARU v2.3]** Endpoint debug **GET /api/v1/pbpk/debug** untuk transparansi parameter alometrik (V_L, Q_L, Cl, %BF, Kp_R, cmax, auc, ratio, category) — untuk validasi pakar & juri.

---

## 7. ARSITEKTUR SISTEM & STACK TEKNOLOGI (SYSTEM ARCHITECTURE & TECH STACK)

### 7.1 Diagram Arsitektur Modular Paralel-Asinkron

Keunggulan arsitektur HepaTwin terletak pada **pemisahan komputasi paralel-asinkron** di backend dan **rendering visual ringan** di frontend klien. AI Predictor dan PBPK Solver tidak saling memanggil atau bergantung satu sama lain, melainkan diproses sejalan dan digabungkan di Lapisan Fusi:

```
                          +-------------------------------------------------+
                          |             FRONTEND KLIEN (React)              |
                          |  Input: Nama Senyawa (INN), Dosis, Kovariat     |
                          +------------------------+------------------------+
                                                   |
                                                   | ASYNC HTTP/REST JSON REQUEST
                                                   v
                          +-------------------------------------------------+
                          |            ROUTER ENDPOINT (FastAPI)            |
                          +------------------------+------------------------+
                                                   |
                             +---------------------+---------------------+
                             | PARALEL-ASINKRON                          | PARALEL-ASINKRON
                             v                                           v
         +---------------------------------------+   +---------------------------------------+
         |      MESIN PREDIKSI AI (PyTorch)      |   |    MESIN PBPK MEKANISTIK (SciPy ODE)  |
         |         Arsitektur: GATNN-DNN         |   |         Model 4-Kompartemen           |
         +---------------------------------------+   +---------------------------------------+
         | - Input: Graf Molekul & ECFP4 Finger. |   | - Input: Dosis Bolus & Kovariat       |
         | - Proses: Forward Pass Neural Net     |   | - Proses: Konversi Alometrik & ODE    |
         | - Output: Probabilitas DILI + SHAP    |   | - Output: Kurva C_hati(t), Cmax/AUC   |
         +-----------------------+-------------------+   +-----------------------+-------------------+
                             |                                           |
                             +---------------------+---------------------+
                                                   |
                                                   v
                          +-------------------------------------------------+
                          |         LAPISAN FUSI RULE-BASED (Backend)       |
                          +-------------------------------------------------+
                          | - Lookup PK: hepatwin_id ke Tabel Supabase      |
                          | - Pemetaan pedagogis Couinaud (V-VIII, II-IV, dll) |
                          | - Evaluasi Warna: Hijau / Kuning / Merah        |
                          |   [T_LOW/HIGH & exposure_index kuantil = INTERNAL] |
                          | - Penentuan Kecepatan Kedip Hotspot WebGL       |
                          +------------------------+------------------------+
                                                   |
                                                   | PAYLOAD JSON (Segmen, Warna, Chart, SHAP)
                                                   v
                          +-------------------------------------------------+
                          |       KANVAS 3D WEBGL (React Three Fiber)       |
                          +-------------------------------------------------+
```

### 7.2 Spesifikasi Komponen Stack Teknologi

- **Frontend Web App:**
  - *Framework:* **React 18** dengan TypeScript & **Tailwind CSS** (desain responsif, tata letak tiga panel interaktif).
  - *3D Engine & Rendering:* **React Three Fiber (R3F)**, **Three.js**, dan **WebGL** untuk memuat dan merender aset 3D `.glb` hati makroskopis berstandar 8 Segmen Couinaud.
  - *Data Visualization:* **Recharts / Chart.js** untuk penampilan grafik kurva temporal konsentrasi obat terhadap waktu ($C_{\text{hati}}$ vs $t$).

- **Backend Application Server:**
  - *Framework:* **Python 3.11+ / FastAPI** (kinerja tinggi, asinkron, validasi tipe ketat via Pydantic).
  - *AI / ML Engineering:* **PyTorch** untuk eksekusi model Graph Attention Network - Dense Neural Network (**GATNN-DNN**); **RDKit** untuk pembacaan SMILES, validasi konektivitas atom, dan ekstraksi sidik jari ECFP4; **atribusi Shapley eksak (tingkat gugus SMARTS) + masking per-atom (tingkat atom, diberi label jujur `masking_attribution`)** untuk interpretasi fitur -- diimplementasikan native di `hepatwin_ml.explain` tanpa library `shap`/`captum`, sesuai §8.1.
  - *Scientific Computing:* **SciPy (scipy.integrate.solve_ivp)** menggunakan metode Runge-Kutta orde 4–5 (`RK45`) untuk penyelesaian numerik sistem persamaan diferensial PBPK 4-kompartemen.

- **Cloud Database & Infrastructure:**
  - *Database:* **Supabase (PostgreSQL Managed)** untuk penyimpanan tabel `hepatwin_compounds` (1.336 baris dataset DILIrank 2.0 yang diperkaya dengan 40 kolom deskriptor PubChem dan monograf LiverTox).
  - *Security & Optimization:* Pengamanan jalur kueri via **Row Level Security (RLS)** dan mekanisme caching client-side untuk memenuhi target latensi NFR-02.
  - *Deployment:* **Vercel** (Frontend) & **Render** (Backend Web Service) dengan sertifikasi SSL/HTTPS penuh.

### 7.3 Pemisahan Artefak Statis Backend (Dataset Kurasi vs Bobot Model)

Backend HepaTwin membedakan secara eksplisit dua artefak statis inti yang memiliki peran saling melengkapi namun secara operasional terpisah:

| Artefak Statis | Isi & Komposisi | Fungsi & Mekanisme Runtime |
| :--- | :--- | :--- |
| **1. Dataset Kurasi** *(Supabase, tabel `hepatwin_compounds`)* | **1.336 baris senyawa DILIrank 2.0** [14] (sumber label DILI) yang diperkaya internal menjadi **40 kolom**: identitas kimia, label risiko DILIrank, status verifikasi (`VERIFIED_PUBCHEM` atau `NO_CID_BIOLOGIC`), deskriptor fisikokimia PubChem [15], serta enrichment LiverTox [18] (`injury_pattern`, `segment_list` [13], `livertox_match_method`). | Menjawab *"Apakah senyawa terdaftar/valid, dan apakah ada pola cedera literatur untuk visualisasi pedagogis?"*. Digunakan untuk lookup validasi senyawa autocomplete dan lookup hotspot Couinaud via primary key `hepatwin_id` secara deterministik dan offline dengan caching. |
| **2. Bobot Model AI** *(`model_gatnn_dnn.pt`)* | Parameter numerik statis dari jaringan saraf *Graph Attention Network + Dense Neural Network* hasil pelatihan offline menggunakan korpus 1.231 senyawa `is_simulatable = TRUE`. | Menjawab *"Seberapa toksik senyawa ini berdasarkan hubungan graf molekul dan sidik jari yang dipelajari dari DILIrank 2.0?"*. Dieksekusi murni dalam mode evaluasi (*forward pass inference*) tanpa pelatihan ulang saat runtime. |

**Alasan Arsitektural Pemisahan & Non-Continuous Learning:**

Mekanisme AI HepaTwin **sengaja dirancang statis tanpa *continuous learning* atau *online retraining***. Pada setiap pemanggilan simulasi, model `model_gatnn_dnn.pt` dijalankan secara *forward pass* murni. Kebijakan ini diambil untuk:

1. Menjaga stabilitas model terhadap **model drift** akibat input yang tidak terkontrol.
2. Mencegah risiko **data poisoning** dari masukan pihak luar.
3. Memastikan **reproduksibilitas ilmiah penuh** di mana senyawa dan kovariat yang sama akan selalu menghasilkan luaran probabilitas dan vektor SHAP yang 100% konsisten.

---

## 8. SPESIFIKASI MENDALAM MESIN ILMIAH, AI, PBPK, DAN LAPISAN FUSI

### 8.1 Mesin Prediksi AI (Graph Attention Network - Dense Neural Network / GATNN-DNN)

Arsitektur model prediksi toksisitas mengadopsi integrasi **GATNN-DNN** [9]. Literatur pembanding modern menunjukkan bahwa AI/toxicity prediction dan GNN untuk DILI berbasis struktur kimia terus berkembang, tetapi HepaTwin v2.3 tetap mempertahankan arsitektur GATNN-DNN yang sudah diimplementasikan developer [7, 8]:

- **Input Representation:** SMILES senyawa yang dipilih dari database diubah oleh **RDKit** menjadi dua representasi secara paralel:
  1. *Molecular Graph:* Atom sebagai node (fitur: nomor atom, hibridisasi, muatan formal, jumlah hidrogen) dan ikatan kimia sebagai edge (tipe ikatan, konjugasi, aromatisitas).
  2. *Molecular Fingerprint:* Sidik jari *Extended-Connectivity Fingerprint 4* (**ECFP4**, 1024 bit).

- **Arsitektur Jaringan (GATNN + DNN):**
  - **GATNN (Graph Attention Network):** Menggunakan *multi-head attention layers* untuk mengeksplorasi hubungan spasial dan kontribusi relatif antar-atom pada graf molekul secara berbobot [9, 10].
  - **DNN (Dense Neural Network):** Menerima representasi sidik jari ECFP4 melalui lapisan *fully connected* dense dengan aktivasi ReLU dan *dropout* untuk menangkap fitur global molekul.
  - **Concatenation & Output Layer:** Vector embedding dari GATNN dan DNN digabungkan (*concat*) ke lapisan klasifikasi akhir berbasis sigmoid yang menghasilkan **Skor Probabilitas Hepatotoksisitas ($P_{\text{DILI}}$) dalam rentang 0% – 100%**.

- **Korpus Pelatihan & Deduplikasi Stereo-Aware:**
  - Model dilatih secara eksklusif menggunakan **DILIrank 2.0** [14] sebagai *ground truth*.
  - Deduplikasi dilakukan menggunakan **InChIKey Stereo-Aware** (bukan Canonical SMILES yang mengabaikan stereokimia dan keliru menyatukan pasangan enantiomer yang berbeda secara klinis/farmakologis, misal: *Levofloxacin* vs *Ofloxacin*).
  - Hasil kurasi menunjukkan hanya terdapat **1 grup duplikat berlabel identik** (*Epoetin alfa* / *Erythropoietin*, CID 92043599) sehingga **tidak dihapus** — korpus dataset tetap utuh **1.336 senyawa**. Dari jumlah tersebut, hanya **1.231 senyawa `is_simulatable = TRUE`** yang masuk ke dalam pelatihan model GATNN-DNN.

- **Interpretabilitas SHAP (*Explainable AI*):**
  - Mengadopsi kerangka **SHAP (SHapley Additive exPlanations)** sebagai komponen explainability yang sudah diimplementasikan dalam sistem; sitasi metodologis utama untuk SHAP adalah Lundberg & Lee [27]. InterDILI [10] tetap digunakan sebagai rujukan bahwa interpretabilitas DILI berbasis attention/feature-importance relevan, tetapi **bukan** sumber klaim SHAP.
  - Sistem menghitung nilai atribusi Shapley/SHAP pada fitur graf/fingerprint yang diproyeksikan ke atom atau sub-struktur molekul untuk visualisasi *toxicophore*. Visualisasi ini adalah **explainability komputasional**, bukan bukti mekanisme biokimia final.

### 8.2 Mesin Farmakokinetika Mekanistik (PBPK 4-Kompartemen & Penskalaan Alometrik) — UPDATED v2.3

Mesin farmakokinetika merepresentasikan distribusi obat melalui **4 kompartemen konsentrasi**: Plasma (P), Hati (L), Ginjal (K), dan Jaringan Perifer/Sisa Tubuh (R). Model ini tetap mempertahankan arsitektur solver ODE SciPy yang sudah diimplementasikan, tetapi v2.3 memperbaiki parameterisasi agar lebih defensible secara farmakokinetik dan tidak mengubahnya menjadi klaim klinis.

> **Batas validitas PBPK Fase 1 v2.3:** model ini adalah **linear, perfusion-limited, bolus tunggal, tanpa absorpsi oral, tanpa protein binding, tanpa Km/Vmax, tanpa metabolit reaktif, tanpa NAPQI/glutathione depletion, dan tanpa parameter compound-specific IVIVE penuh**. Karena itu, output PBPK HepaTwin adalah **indeks paparan komputasional untuk visualisasi dan triase riset**, bukan prediksi kadar darah/hati klinis yang boleh dipakai untuk penentuan dosis pasien.

#### 1. Persamaan Diferensial Biasa (ODE PBPK 4-Kompartemen)

Dinamika laju perubahan konsentrasi obat pada setiap kompartemen dirumuskan sebagai berikut [11, 22]:

$$\frac{dC_P}{dt} = \frac{1}{V_P} \left[ Q_L \left( \frac{C_L}{K_{P,L}} \right) + Q_K \left( \frac{C_K}{K_{P,K}} \right) + Q_R \left( \frac{C_R}{K_{P,R}} \right) - (Q_L + Q_K + Q_R) C_P \right]$$

$$\frac{dC_L}{dt} = \frac{1}{V_L} \left[ Q_L \left( C_P - \frac{C_L}{K_{P,L}} \right) - Cl_{met} \left( \frac{C_L}{K_{P,L}} \right) \right]$$

$$\frac{dC_K}{dt} = \frac{1}{V_K} \left[ Q_K \left( C_P - \frac{C_K}{K_{P,K}} \right) - Cl_{renal} \left( \frac{C_K}{K_{P,K}} \right) \right]$$

$$\frac{dC_R}{dt} = \frac{1}{V_R} \left[ Q_R \left( C_P - \frac{C_R}{K_{P,R}} \right) \right]$$

*Keterangan parameter matriks ODE:*

- $C_X$: konsentrasi obat pada kompartemen $X$ (mg/L).
- $V_X$: volume kompartemen $X$ (L).
- $Q_X$: laju aliran darah/perfusi menuju kompartemen $X$ (L/jam).
- $Cl_{met}$: klirens eliminasi metabolisme hepatik efektif (L/jam).
- $Cl_{renal}$: klirens eliminasi renal efektif (L/jam).
- $K_{P,X}$: koefisien partisi jaringan-terhadap-plasma untuk kompartemen $X$.

**Kondisi awal bolus akut:**

$$C_P(0)=\frac{Dosis_{mg}}{V_P}, \quad C_L(0)=C_K(0)=C_R(0)=0, \quad t=0$$

> **Catatan:** “bolus” di sini berarti input matematis langsung ke plasma, bukan rekomendasi rute pemberian obat. Untuk obat oral seperti acetaminophen/ibuprofen, model Fase 1 sengaja tidak memodelkan absorpsi GI; visualisasi bersifat edukatif.

#### 2. Modul Penskalaan Alometrik Kovariat Pasien — v2.3

Pengguna tidak memasukkan parameter PBPK teknis secara manual. Backend mengubah usia, jenis kelamin, berat badan, dan tinggi badan menjadi parameter ODE sebagai berikut.

##### 2.1 BMI

$$BMI = \frac{BB_{kg}}{(TB_m)^2}$$

BMI digunakan sebagai indikator fenotipe metabolik dan flag risiko (`metabolic_risk_flag`), **bukan** sebagai dasar otomatis untuk menurunkan klirens hepatik.

##### 2.2 Volume plasma, hati, ginjal, dan jaringan sisa

Untuk menjaga konsistensi massa/volume, v2.3 mengubah beberapa konstanta statis menjadi fungsi berat badan:

$$V_P = 0.043 \times BB_{kg}$$

$$V_L = 0.0257 \times BB_{kg}$$

$$V_K = 0.0044 \times BB_{kg}$$

$$V_R = \max(BB_{kg} - V_P - V_L - V_K, 1.0)$$

- `V_P=0.043×BB` menghasilkan ±3.0 L plasma untuk dewasa 70 kg, konsisten dengan parameter PBPK terbuka yang memakai plasma volume 0.043 L/kg [24, 31].
- `V_L=0.0257×BB` mengikuti fraksi liver manusia 2.57% yang dikutip pada kompilasi PBPK open-access untuk food-producing animals sebagai nilai kompilasi fisiologis klasik yang dikutip dalam sumber tersebut [23]. Implementasi lama `0.025×BB` tetap boleh diterima sebagai *compatibility tolerance* ±3%, tetapi konfigurasi v2.3 menggunakan `LIVER_VOLUME_FRACTION = 0.0257`.
- `V_K=0.0044×BB` adalah penyederhanaan dua ginjal dewasa sekitar 0.4–0.5% BB. Semua volume ini **bukan rekonstruksi anatomi pasien individual**, melainkan parameter Fase 1.

##### 2.3 Persentase lemak tubuh (%BF) — formula usia-spesifik Deurenberg

Deurenberg dkk. membedakan formula anak dan dewasa. Karena input HepaTwin menerima usia 0–100 tahun, v2.3 wajib memakai cabang usia [21]:

**Usia ≤15 tahun:**

$$\%BF = 1.51 \times BMI - 0.70 \times Usia - 3.6 \times Sex + 1.4$$

**Usia ≥16 tahun:**

$$\%BF = 1.20 \times BMI + 0.23 \times Usia - 10.8 \times Sex - 5.4$$

Keterangan: `Sex=1` untuk laki-laki, `Sex=0` untuk perempuan. Formula dewasa memiliki $R^2=0.79$, SEE 4.1% BF, dan sedikit overestimasi pada obesitas [21]. Untuk stabilitas numerik, backend melakukan clamp operasional `%BF 3–60%` dan mencatat `logger.warning` jika nilai mentah keluar rentang.

##### 2.4 Aliran darah hepatik ($Q_L$) berbasis berat badan dan usia

Soejima dkk. menganalisis 18 obat dan melaporkan hepatic unbound clearance turun 32% pada usia 80 dan 40% pada usia 90 dibanding usia 40, setara **0.80% per tahun sejak usia 40**; penurunan tersebut konsisten dengan perubahan liver weight/blood flow **per person**, bukan per kg [20]. Karena itu v2.3 menggunakan:

$$Q_{C,70}=360 \text{ L/h} \quad (6 \text{ L/min})$$

$$Q_C(BB)=Q_{C,70}\times\bigg(\frac{BB}{70}\bigg)^{0.75}$$

```text
age_factor = 1.0                                           ; jika Usia < 40
age_factor = max(0.60, 1 - 0.008 × (min(Usia, 90) - 40))   ; jika Usia ≥ 40
Q_L        = 0.25 × Q_C(BB) × age_factor
```

Untuk dewasa 70 kg <40 tahun, $Q_L=90$ L/h (≈1.5 L/min). Batas bawah 0.60 mencegah extrapolation di luar 90 tahun. Faktor usia diterapkan pada $Q_L$; **tidak diterapkan lagi pada intrinsic clearance** untuk menghindari *double-counting*.

##### 2.5 Aliran ginjal dan jaringan sisa

$$Q_K = 0.20 \times Q_C(BB)$$

$$Q_R = \max(Q_C(BB)-Q_L-Q_K, 0)$$

Fraksi 25% hepatic dan 20% renal adalah prior fisiologis Fase 1 untuk menjaga ODE well-posed. Angka ini tetap diberi label **parameter desain**, bukan pengukuran pasien individual.

##### 2.6 Klirens metabolik dan renal

Jika database masa depan menyediakan parameter compound-specific (`human_cl_l_hr`, `renal_fraction`, `hepatic_extraction_ratio`, atau IVIVE microsome/hepatocyte), nilai tersebut harus diprioritaskan. Untuk Fase 1 saat parameter tersebut belum lengkap:

$$Cl_{met} = base\_cl_{met,70} \times \bigg(\frac{BB}{70}\bigg)^{0.75}$$

Dengan `base_cl_met_70 = 15.0 L/h` sebagai fallback komputasional. Untuk stabilitas fisiologis:

$$Cl_{met} = \min(Cl_{met}, 0.95 \times Q_L)$$

`base_cl_met_70=15.0 L/h` **bukan angka klinis obat tertentu**; ini adalah fallback agar solver berjalan untuk seluruh katalog. DallphinAtoM dan literatur PBPK menegaskan bahwa clearance idealnya berasal dari data in vitro/in vivo dan IVIVE, bukan konstanta universal [22].

**Perubahan penting v2.3:** reduksi otomatis `Cl -20%` untuk `BMI≥30` **dihapus dari default**. Ghabril dkk. menyatakan MASLD/CLD dapat terkait risiko dan outcome DILI, tetapi juga eksplisit bahwa belum ada bukti yang menghubungkan altered pharmacokinetics per se dengan peningkatan risiko DILI [17]. Karena itu:

```python
metabolic_risk_flag = BMI >= 30
clearance_multiplier_from_bmi = 1.0  # v2.3 default; bukan 0.8
```

Flag BMI boleh memengaruhi narasi risiko/fusi visual secara transparan, tetapi tidak boleh diam-diam mengubah clearance sebelum ada validasi K3/Farmasi.

##### 2.7 Koefisien partisi jaringan sisa ($K_{P,R}$) berbasis lipofilisitas — heuristic terkendali

Karena distribusi jaringan dipengaruhi lipofilisitas dan komposisi tubuh, HepaTwin mempertahankan $K_{P,R}$ dinamis. Namun v2.3 memperjelas bahwa formula ini **heuristik visual Fase 1**, bukan formula klinis dari Coutinho atau SwissADME. Coutinho dkk. justru menunjukkan metode prediksi volume distribusi dapat sangat overpredict pada obat lipofilik/logP tinggi [24], sehingga formula HepaTwin harus konservatif.

```python
xlogp_eff = 0.0 if xlogp is None else clamp(xlogp, -1.0, 7.0)
bf_frac = clamp(body_fat_percent / 100.0, 0.03, 0.60)
Kp_R = clamp(1.0 + bf_frac * (10 ** (0.25 * xlogp_eff)), 1.0, 10.0)
```

- `XLogP NULL → 0.0` dengan `logger.warning("[FALLBACK XLogP NULL]")`.
- `0.25` adalah **damping exponent** untuk mencegah ledakan $10^{0.5×XLogP}$ pada logP tinggi.
- `Kp_R` clamp 1.0–10.0 adalah guard numerik dan visual, bukan batas fisiologis universal.
- XLOGP3/SwissADME digunakan sebagai konteks bahwa logP adalah descriptor penting, dengan rentang optimal/komputasional yang harus diinterpretasikan hati-hati [25].

##### 2.8 Evaluator paparan v2.3 — tidak lagi menganggap Cmax/AUC sebagai “magnitude exposure”

Audit v2.1 menemukan `Cmax/AUC` bersifat dose-independent pada ODE linear sehingga tidak valid disebut magnitude paparan. v2.3 mempertahankan output lama untuk backward compatibility, tetapi mengganti maknanya:

```python
shape_ratio_h_inv = cmax_liver_mg_l / auc_liver_mg_h_l  # satuan h^-1
```

`shape_ratio_h_inv` hanya menggambarkan bentuk kurva/kecepatan decay relatif, **bukan** kategori tinggi-rendah paparan.

Kategori paparan visual Fase 1 memakai indeks berbasis magnitude:

```python
exposure_index = log1p(cmax_liver_mg_l) + log1p(auc_liver_mg_h_l)
```

Kategori:

```python
LOW_EXPOSURE      = exposure_index < P33_CALIBRATION
MODERATE_EXPOSURE = P33_CALIBRATION <= exposure_index <= P66_CALIBRATION
HIGH_EXPOSURE     = exposure_index > P66_CALIBRATION
```

`P33_CALIBRATION` dan `P66_CALIBRATION` dihitung dari sweep internal yang dibekukan dan terdokumentasi (`reports/pbpk_exposure_calibration_v2_3.md`) dengan grid usia, BB/TB/BMI, jenis kelamin, dosis mg/kg, dan XLogP katalog. Prinsip ini bukan ambang klinis; literatur PBPK olaparib dan rilzabrutinib justru menunjukkan bahwa threshold PK yang bermakna klinis bersifat **drug-specific** dan harus divalidasi terhadap endpoint obat masing-masing [26, 32].

> **Catatan implementasi:** API boleh tetap mengembalikan field lama `cmax_auc_ratio` untuk kompatibilitas frontend, tetapi label UI dan laporan PDF wajib menamainya `shape_ratio_h_inv`, bukan “risk threshold”.

#### 3. Transparansi PBPK v2.3

Endpoint debug wajib menampilkan minimal:

```json
{
  "BMI": 24.8,
  "metabolic_risk_flag": false,
  "V_P_L": 3.01,
  "V_L_L": 1.80,
  "V_K_L": 0.31,
  "V_R_L": 64.88,
  "Q_C_L_h": 360.0,
  "Q_L_L_h": 90.0,
  "Q_K_L_h": 72.0,
  "Q_R_L_h": 198.0,
  "body_fat_percent_raw": 22.6,
  "body_fat_percent_clamped": 22.6,
  "xlogp_eff": 1.2,
  "Kp_R": 1.45,
  "Cl_met_L_h": 15.0,
  "cmax_liver_mg_l": 0.0,
  "auc_liver_mg_h_l": 0.0,
  "shape_ratio_h_inv": 0.0,
  "exposure_index": 0.0,
  "exposure_category": "LOW_EXPOSURE"
}
```

---

### 8.3 Lapisan Fusi Rule-Based & Pemetaan Spasial Segmen Couinaud (I–VIII) — UPDATED v2.3

Lapisan Fusi tetap menjadi komponen rule-based di backend yang menggabungkan keluaran AI Predictor, PBPK Solver, dan lookup kurasi DILIrank/LiverTox. v2.3 tidak mengubah arsitektur besar fusi, tetapi memperbaiki bahasa ilmiah agar tidak overclaim.

#### 1. Mekanisme Lookup Deterministik (Offline Curated LiverTox)

Input dibatasi pada daftar tertutup senyawa `is_simulatable = TRUE`. Pemetaan segmen hati **bukan prediksi AI runtime**, melainkan lookup dari tabel internal `hepatwin_compounds` yang mengaitkan DILIrank 2.0, PubChem, dan LiverTox secara offline [14, 15, 18].

```sql
SELECT
    segment_list,
    injury_pattern,
    hotspot_base_intensity,
    livertox_match_method
FROM
    hepatwin_compounds
WHERE
    hepatwin_id = ? AND is_simulatable = TRUE;
```

- DILIrank 2.0 [14] menjadi sumber label DILI untuk 1.336 drug.
- PubChem [15] menjadi sumber identitas/deskriptor kimia.
- LiverTox [18] menjadi sumber narasi/pola cedera bila tersedia.
- Kolom `segment_list` dan `livertox_match_method` adalah **hasil kurasi internal HepaTwin**, bukan kolom asli DILIrank.

#### 2. Aturan Pemetaan Pola Cedera ke 8 Segmen Couinaud — heuristik visual, bukan lokalisasi klinis

Model WebGL membagi hati menjadi 8 Segmen Couinaud fungsional [13]. AASLD mengklasifikasikan pola DILI berbasis R-value menjadi hepatocellular, mixed, dan cholestatic [19]. Namun, **zona histologis lobulus (Zona 1/2/3) tidak identik dengan Segmen Couinaud**. Karena itu, mapping berikut adalah **heuristik pedagogis makrovaskular** untuk membantu pengguna memahami pola cedera, bukan klaim bahwa cedera mikroskopis benar-benar terbatas pada segmen tersebut.

| Pola cedera kurasi | Visualisasi HepaTwin v2.3 | Status ilmiah |
|---|---|---|
| Hepatocellular / dominan hepatosit | Segmen V, VI, VII, VIII sebagai hotspot kanan dominan | **Heuristik visual**; APAP centrilobular didukung [3, 29], tetapi Couinaud mapping bukan lokalisasi klinis |
| Cholestatic / dominan empedu | Segmen II, III, IV sebagai hotspot kiri/porta visual | **Heuristik visual**; cholestatic pattern didukung [19], segment mapping internal |
| Mixed | Seluruh segmen I–VIII intensitas menengah | **Heuristik visual** |
| Tidak ada monograf/pola spesifik | Hotspot difus redup seluruh segmen + label “evidence unavailable” | Prinsip anti-halusinasi medis |

Payload wajib membawa flag:

```json
{
  "segment_mapping_type": "PEDAGOGICAL_HEURISTIC",
  "segment_mapping_not_clinical_localization": true
}
```

#### 3. Logika Penentuan Warna & Kecepatan Kedip Hotspot — UPDATED v2.3

Sistem **tidak menggunakan ambang klinis universal**. Warna adalah prioritas visual DSS praklinis:

- **Probabilitas AI GATNN-DNN ($P_{DILI}$):** ambang `T_LOW/T_HIGH` bersifat distribusional pasca-kalibrasi, bukan ambang klinis [9, 10].
- **Indeks paparan PBPK:** `exposure_index` berbasis `Cmax_L` dan `AUC_L`; kategori LOW/MOD/HIGH berasal dari kuantil calibration sweep internal (§8.2.2.8), bukan dari Soejima/Ghabril maupun studi obat lain.
- **Flag risiko metabolik:** `BMI≥30` hanya flag naratif; tidak menurunkan clearance default.
- **Lookup evidence:** DILIrank/LiverTox menaikkan confidence jika pola cedera spesifik tersedia.

```
+------------------------------------------------------------------------------------------------------+
|                               LOGIKA FUSI RULE-BASED HEPATWIN  [v2.3]                                 |
+-----------------------------+-----------------------------+-------------------------------------------+
| AI distribusional            | PBPK distribusional          | Keputusan visual                           |
+-----------------------------+-----------------------------+-------------------------------------------+
| P_DILI < T_LOW               | LOW_EXPOSURE                 | HIJAU: prioritas rendah in-silico          |
|                             |                             | BUKAN klaim aman klinis                    |
+-----------------------------+-----------------------------+-------------------------------------------+
| T_LOW <= P_DILI <= T_HIGH    | MODERATE_EXPOSURE atau flag  | KUNING: perlu perhatian/validasi           |
| atau metabolic_risk_flag     |                             | BUKAN diagnosis                            |
+-----------------------------+-----------------------------+-------------------------------------------+
| P_DILI > T_HIGH              | HIGH_EXPOSURE atau evidence  | MERAH: prioritas tinggi untuk kajian lanjut|
| atau LiverTox strong evidence| strong DILI                  | BUKAN prediksi cedera pasien               |
+-----------------------------+-----------------------------+-------------------------------------------+
```

> **Kewajiban UI/Laporan:** label “Aman/Berbahaya/Kritis” tidak boleh berdiri sendiri. Gunakan “Prioritas rendah/sedang/tinggi in-silico” dan cantumkan disclaimer bahwa warna bukan keputusan terapi.

---

### 8.4 Statistik Cakupan Dataset Terkurasi (DILIrank 2.0 + Enrichment LiverTox) — UPDATED v2.3

Dataset kurasi dalam tabel `hepatwin_compounds` terdiri dari **1.336 senyawa × 40 kolom**, dan telah melewati **63 pemeriksaan validasi otomatis** (jumlah baris, integritas sumber, duplikasi, tipe data, domain kategorikal, missing values, relasi) dengan **0 kegagalan**:

| # | Metrik Kurasi Dataset | Jumlah Senyawa | Persentase dari Total | Keterangan & Penjelasan Teknis |
| :---: | :--- | :---: | :---: | :--- |
| 1 | **Total Senyawa (Seluruh DILIrank 2.0)** | **1.336** | **100%** | Korpus utuh FDA DILIrank 2.0 [14] tanpa penghapusan baris |
| 2 | Memiliki CID PubChem + Deskriptor | **1.231** | **92,1%** | Senyawa molekul kecil dengan Canonical/Isomeric SMILES valid |
| 3 | **Siap Pipeline GATNN-DNN (`is_simulatable = TRUE`)** | **1.231** | **92,1%** | Subhimpunan yang masuk ke autocomplete dan mesin simulasi |
| 4 | **Senyawa Biologik (`is_simulatable = FALSE`)** | **105** | **7,9%** | Antibodi & protein (`NO_CID_BIOLOGIC`); di luar layanan simulasi |
| 5 | Tertaut Monograf LiverTox [18] | **806** | **60,3%** | Tertaut via normalisasi nama (`exact`, `salt_ester`, dll.) |
| 6 | Memiliki Pola Cedera Spesifik | **427** | **32,0%** | Memiliki kriteria rasio-R klinis baku di LiverTox [19] |
| 7 | — *Pola Hepatoseluler → hotspot pedagogis Segmen V–VIII* | 252 | 18,9% | Heuristik visual makrovaskular; bukan lokalisasi Zona 3 klinis |
| 8 | — *Pola Kolestatik → Segmen II–IV* | 131 | 9,8% | Zona 1 / periportal (Lobus Kiri lateral & medial) |
| 9 | — *Pola Campuran → 8 Segmen Intensitas Rendah* | 44 | 3,3% | Cedera campuran seluruh segmen |
| 10 | **Tidak Terklasifikasi / Tanpa Monograf** | **909** | **68,0%** | Termasuk 530 `no_match`; visualisasi fallback **difus redup 8 segmen** |

*Catatan Tambahan Deskriptor Fisikokimia [UPDATED v2.3]:*
Nilai `XLogP` kosong pada **676 senyawa** adalah **hasil audit kurasi internal HepaTwin**, bukan klaim langsung dari SwissADME atau DILIrank. PubChem/SwissADME mendukung penggunaan XLOGP3/logP sebagai descriptor lipofilisitas [15, 25], tetapi ketersediaan nilai pada katalog HepaTwin harus dibuktikan dengan query database internal. Untuk PBPK, `NULL` di-fallback ke `XLogP=0.0` dengan `logger.warning("[FALLBACK XLogP NULL]")`, lalu diproses oleh formula Kp_R v2.3 (§8.2.2.7).

### 8.5 Uji Prinsip Desain Inti ("Apa yang Rusak Jika Komponen Dihapus?")

Untuk membuktikan bahwa kedua komponen ilmiah HepaTwin merupakan **kebutuhan genuine** dan bukan sekadar hiasan kosmetik, tim menerapkan uji evaluasi desain inti:

1. **Jika AI (GATNN-DNN) Dihapus:**
   - *Apa yang terjadi?* Sistem hanya menjadi kalkulator ODE farmakokinetika konvensional. Sistem **kehilangan kemampuan untuk memprediksi toksisitas intrinsik senyawa yang bermekanisme idiosinkratik atau belum memiliki model parameter PD yang lengkap**.
   - *Dampak Pengguna:* Peneliti tidak dapat mengetahui probabilitas risiko kimiawi senyawa baru dari struktur SMILES-nya, dan kehilangan fitur explainability SHAP (*toxicophore highlighting*).

2. **Jika PBPK Mekanistik Dihapus:**
   - *Apa yang terjadi?* Sistem berubah menjadi classifier AI statis biasa seperti ProTox-II.
   - *Dampak Pengguna:* Sistem **kehilangan dimensi waktu (temporal) dan tidak mampu menyimulasikan perbedaan profil paparan antara dosis terapi normal vs overdosis akut**. Pengguna juga tidak dapat melihat pengaruh usia, jenis kelamin, atau obesitas (BMI) terhadap akumulasi konsentrasi obat di organ hati.

3. **Kesimpulan Sinergi:** Gabungan AI dan PBPK wajib hadir sejalan agar prediksi toksisitas kimiawi dan profil akumulasi dosis/fisiologis dapat saling melengkapi secara ilmiah.

---

## 9. SPESIFIKASI ANTARMUKA PENGGUNA (UI/UX SPECIFICATIONS)

### 9.1 Layout Dasbor Utama dengan Top Bar dan Footer

Dasbor interaktif HepaTwin dirancang dengan struktur tata letak sebagai berikut:

1. **Top Bar (Baris Pertama — Di Luar 3 Panel Utama):**
   - **Kiri:** Logo HepaTwin, Judul (**HepaTwin**), dan Subtitle (*"Simulasi In-Silico 3D Liver untuk Prediksi Risiko Hepatotoksisitas"*).
   - **Kanan:** Tombol **"Unduh Laporan PDF"** yang awalnya dalam kondisi **non-aktif (disabled/greyed out)** dan akan menjadi **aktif (enabled)** setelah simulasi berhasil dijalankan.

2. **Area Tiga Panel Utama (Middle Section):**
   - Terdiri dari Panel Kiri, Panel Kanan, dan Panel Bawah seperti dijelaskan pada sub-bagian 9.2.

3. **Footer Note (Baris Terakhir — Di Luar 3 Panel Utama):**
   - Berisi **Medical Disclaimer** permanen sebagai catatan kaki yang selalu terlihat di bagian bawah halaman.

### 9.2 Layout Tiga Panel Terintegrasi

Dasbor interaktif HepaTwin dirancang dalam tata letak tiga panel terintegrasi dalam satu layar penuh (*single-page application dashboard*) agar seluruh informasi dapat dianalisis tanpa memicu kelelahan atau kebingungan kognitif:

```
+---------------------------------------------------------------------------------------------------------------------+
|                                                 TOP BAR (FULL WIDTH)                                               |
+-------------------------------------------------------+---------------------------------------------------------+
|  [LOGO] HepaTwin                                      |  [BUTTON: UNDUH LAPORAN PDF] (Disabled -> Enabled)    |
|  Simulasi In-Silico 3D Liver untuk Prediksi           |  (Aktif hanya setelah simulasi selesai dijalankan)      |
|  Risiko Hepatotoksisitas                              |                                                         |
+-----------------------------------+-------------------------------------------------------------------+
|      PANEL KIRI (Lebar 30%)       |                       PANEL KANAN (Lebar 70%)                     |
|    AREA KONTROL & INPUT PRIMER    |                      KANVAS VISUALISASI 3D HATI                   |
+-----------------------------------+                                                                   |
| [Search Bar: Autocomplete INN]    |    [ MODEL 3D ANATOMI HATI - 8 SEGMEN COUINAUD (I - VIII) ]      |
| - Filter is_simulatable = TRUE    |                                                                   |
|                                   |            (Rotasi 360, Zoom In/Out, Pan, Hover Mesh)            |
| [Input Dosis Bolus Tunggal (mg)]  |                                                                   |
|                                   |         +-----------------------------------------------+         |
| [Kovariat Pasien - Alometrik]:    |         |   OVERLAY HOTSPOT BOLA SEMI-TRANSPARAN        |         |
| - Usia (tahun)                    |         |   - Warna: Hijau / Kuning / Merah             |         |
| - Jenis Kelamin (L/P)             |         |   - Kecepatan Kedip: Stabil / Lambat / Cepat  |         |
| - Berat Badan (kg)                |         |   - Lokasi pedagogis: V-VIII, II-IV, atau Difus |         |
| - Tinggi Badan (cm)               |         +-----------------------------------------------+         |
|                                   |                                                                   |
| [ Tombol: SIMULASIKAN TOKSISITAS ]|                                                                   |
+-----------------------------------+-------------------------------------------------------------------+
|                           PANEL BAWAH (Lebar 100%, Tinggi 35% - Panel Output Data)                    |
+---------------------------------------------------+---------------------------------------------------+
|   KIRI: KURVA PAPARAN KONSENTRASI TEMPORAL        |   KANAN: EXPLAINABILITY SHAP                      |
|   - Grafik C_hati(t) vs Waktu t (24 Jam)          |   - Visual 2D Struktur Molekul (Highlight Merah)  |
|   - Profil Rasio Cmax / AUC Alometrik             |   - Gugus Toxicophore Pemicu DILI                 |
|   - Tanpa Garis Ambang Absolut                    |                                                     |
+---------------------------------------------------+---------------------------------------------------+
+---------------------------------------------------------------------------------------------------------------------+
|                                                 FOOTER / FOOTNOTE                                                 |
|  Medical Disclaimer: HepaTwin merupakan perangkat lunak penunjang keputusan praklinis yang murni bersifat in-silico. |
|  Hasil prediksi BUKAN diagnosis klinis atau pengganti uji laboratorium. Berdasarkan FDA CM&S credibility guidance (Context of Use).   |
+---------------------------------------------------------------------------------------------------------------------+
```

#### Komponen Layout:

- **Top Bar:**
  - Posisi: Baris paling atas, melebar penuh (100% width).
  - **Kiri:** Logo aplikasi HepaTwin, judul "HepaTwin", dan subtitle deskriptif.
  - **Kanan:** Tombol **"Unduh Laporan PDF"** dengan kondisi:
    - *Sebelum simulasi:* Tombol **non-aktif (disabled)** dengan warna abu-abu dan tooltip "Jalankan simulasi terlebih dahulu".
    - *Setelah simulasi berhasil:* Tombol **menjadi aktif (enabled)** dengan warna utama, siap mengunduh PDF laporan hasil simulasi.

- **Panel Kiri (Lebar 30% — Area Interaksi Primer):**
  - Search bar dengan *autocomplete* instan untuk pencarian nama obat INN dari daftar tertutup 1.231 senyawa `is_simulatable = TRUE`.
  - Input numerik dosis bolus tunggal (satuan mg).
  - Empat *input field* kovariat pasien: Usia, Jenis Kelamin, Berat Badan, dan Tinggi Badan.
  - Tombol utama **"Simulasikan Toksisitas"** — saat diklik akan memicu **Popup Disclaimer Checklist** sebelum simulasi dimulai.

- **Panel Kanan (Lebar 70% — Kanvas 3D WebGL):**
  - Memuat model mesh anatomi hati 3D makroskopis warna coklat anatomis realistis berstandar 8 Segmen Couinaud yang mendukung rotasi 360°, zoom-in/zoom-out, dan hover.
  - Menampilkan overlay bola hotspot semitransparan berkedip pada segmen terdampak sesuai keputusan Lapisan Fusi.

- **Panel Bawah (Lebar 100%, Tinggi 35% — Panel Output Data):**
  - *Area Kiri:* Grafik kurva konsentrasi obat di hati terhadap waktu ($C_{\text{hati}}$ vs $t$) berdurasi 24 jam.
  - *Area Kanan:* Visualisasi explainability SHAP yang menyorot atom-atom pemicu toksisitas (*toxicophore*).

- **Footer Note:**
  - Posisi: Baris paling bawah, melebar penuh (100% width).
  - Berisi **Medical Disclaimer** permanen yang selalu terlihat sebagai pengingat kepada pengguna bahwa HepaTwin bukan perangkat diagnosis klinis.

### 9.3 Mekanisme Popup Disclaimer Checklist — UPDATED v2.3

Ketika pengguna menekan tombol **"Simulasikan Toksisitas"**, sistem menampilkan **Popup Modal Disclaimer** sebelum simulasi dimulai. v2.3 menyamakan desain dengan workflow: terdapat **tiga checkbox wajib**.

#### Komponen Popup Disclaimer:

```
+-------------------------------------------------------------------------------------------------------------+
|                           POPUP MODAL — MEDICAL DISCLAIMER                           [X] Tutup              |
+-------------------------------------------------------------------------------------------------------------+
|  PENTING — BACA SEBELUM MELANJUTKAN                                                                         |
|                                                                                                             |
|  HepaTwin adalah DSS praklinis in-silico untuk riset/edukasi.                                               |
|  Hasil visualisasi 3D, AI, SHAP, dan PBPK:                                                                  |
|  - BUKAN diagnosis klinis pasien                                                                            |
|  - BUKAN rekomendasi terapi/dosis                                                                           |
|  - BUKAN pengganti uji in-vitro, in-vivo, uji klinis, atau keputusan regulator                              |
|                                                                                                             |
|  PBPK Fase 1 adalah model linear bolus tunggal tanpa absorpsi oral, tanpa Km/Vmax,                           |
|  tanpa protein binding, dan tanpa metabolit reaktif seperti NAPQI/glutathione.                              |
|                                                                                                             |
|  Warna Couinaud adalah heuristik visual pedagogis, bukan lokalisasi histologis klinis.                       |
|  Ambang AI dan exposure adalah distribusional/internal, bukan ambang klinis tervalidasi.                     |
|                                                                                                             |
|  [ ] Saya memahami HepaTwin bukan alat diagnosis/terapi.                                                    |
|  [ ] Saya memahami parameter PBPK/AI Fase 1 masih memerlukan validasi K2/K3/K6 dan review Farmasi.          |
|  [ ] Saya memahami warna 3D adalah prioritas visual in-silico, bukan bukti cedera pasien.                   |
|                                                                                                             |
|                           [BATAL]                              [JALANKAN SIMULASI] (disabled)                |
+-------------------------------------------------------------------------------------------------------------+
```

#### Mekanisme Interaksi:

1. Pengguna mengisi senyawa, dosis, dan kovariat.
2. Klik **"Simulasikan Toksisitas"**.
3. Popup muncul; tombol **"Jalankan Simulasi"** non-aktif.
4. Tombol aktif hanya setelah **semua tiga checkbox** dicentang.
5. Jika pengguna klik "Batal" atau [X], popup tertutup tanpa simulasi.
6. Setelah simulasi berhasil, persetujuan disimpan pada session state sehingga popup tidak perlu muncul lagi selama sesi aktif.
7. Tombol **"Unduh Laporan PDF"** aktif setelah hasil simulasi selesai.

---

### 9.4 Skenario Visual Verifikasi Simulasi Kontras (Acetaminophen vs Ibuprofen) — UPDATED v2.3

Skenario demo dipakai untuk verifikasi UI, backend, dan narasi ilmiah. v2.3 memperbaiki kesalahan fatal v2.1: **4.000 mg acetaminophen tidak lagi disebut overdose akut tunggal dewasa**. Menurut sumber toksikologi klinis, acute toxicity biasanya terkait ingestion `≥150 mg/kg` atau sekitar 7,5–10 g pada dewasa [29, 30]. LiverTox juga menyebut hepatotoksisitas acetaminophen paling sering muncul setelah >7,5 g, umumnya >15 g, sebagai single overdose [29].

#### 1. Skenario A: Acetaminophen / Paracetamol — Potentially Toxic Acute Single Ingestion

- **Input Pengguna:** Senyawa *Acetaminophen*, dosis bolus matematis **10.500 mg** pada pasien laki-laki 40 tahun, BB 70 kg, TB 168 cm. Nilai ini setara **150 mg/kg**, yaitu threshold toksisitas akut yang umum dipakai sebagai titik kewaspadaan awal [30].
- **Catatan 4.000 mg:** 4.000 mg adalah dosis harian maksimum/tinggi pada banyak referensi, dapat menyebabkan peningkatan aminotransferase pada sebagian orang setelah beberapa hari, tetapi **tidak valid disebut overdose akut bolus tunggal** untuk pria 70 kg [29, 30].
- **Mekanisme toksikologi:** APAP hepatotoxicity melibatkan metabolit reaktif NAPQI, CYP2E1, glutathione depletion, dan cedera centrilobular/perivenous; mekanisme ini didukung Jaeschke & Ramachandran [3] dan LiverTox [29].
- **Batas model:** PBPK HepaTwin Fase 1 tidak memodelkan NAPQI/glutathione atau injury timeline 24–96 jam. Kurva 24 jam hanya menunjukkan paparan parent-compound dalam model linear.
- **Mekanisme AI & Lookup:** DILIrank/LiverTox memberi evidence kuat untuk acetaminophen sebagai hepatotoxin dosis-tinggi; AI GATNN-DNN dan SHAP menampilkan kontribusi fitur struktur sesuai model, bukan bukti mekanisme biokimia final.
- **Hasil Visualisasi Panel:**
  - *3D Hati:* warna **MERAH / prioritas tinggi in-silico** pada hotspot pedagogis hepatocellular (Segmen V–VIII) dengan label `PEDAGOGICAL_HEURISTIC`.
  - *Panel PBPK:* menampilkan `Cmax_L`, `AUC_L`, `exposure_index`, dan `shape_ratio_h_inv`. Tidak ada garis ambang klinis.
  - *Panel SHAP:* menampilkan sub-struktur/fitur model yang meningkatkan prediksi DILI; caption wajib menyatakan “computational attribution, not biochemical proof”.

#### 2. Skenario B: Ibuprofen — Dosis Terapi Umum 400 mg

- **Input Pengguna:** Senyawa *Ibuprofen*, dosis 400 mg, pasien dewasa normal.
- **Fakta sumber:** LiverTox menyebut ibuprofen umumnya aman dan well tolerated, tetapi dapat sangat jarang menyebabkan liver injury klinis, terutama pada dosis tinggi atau reaksi idiosinkratik; conventional low-dose/intermittent long-term injury tidak terbukti meyakinkan [33].
- **Mekanisme Backend & PBPK:** Dosis 400 mg pada pasien dewasa normal diharapkan memiliki exposure_index lebih rendah dibanding skenario APAP 10.500 mg. Namun kategori akhir tetap bergantung pada AI calibration dan lookup kurasi.
- **Hasil Visualisasi Panel:**
  - *Jika AI rendah + exposure_index rendah:* **HIJAU / prioritas rendah in-silico**, bukan klaim “aman klinis absolut”.
  - *Jika lookup LiverTox mengembalikan rare injury evidence:* tampilkan label “rare idiosyncratic DILI reported” dengan hotspot difus/redup atau pola sesuai kurasi, bukan klaim cedera pasti.

> **Catatan Verifikasi Farmasi v2.3:** Demo wajib menekankan perbedaan **paparan komputasional** vs **cedera klinis**. Acetaminophen overdose klinis dinilai dengan waktu ingestion dan serum level/Rumack-Matthew nomogram; HepaTwin tidak melakukan penilaian klinis tersebut [30].

---

## 10. ALUR KERJA PENGGUNA AKHIR (END-TO-END USER WORKFLOW)

Alur penggunaan HepaTwin dari awal hingga selesai terdiri dari 12 tahapan interaktif yang mulus dan intuitif:

```
[1. Buka Portal HTTPS Vercel]
            |
            v
[2. Lihat Top Bar & Footer Disclaimer]
   - Top Bar: Logo HepaTwin, Subtitle, Tombol PDF (Disabled)
   - Footer: Medical Disclaimer permanen
            |
            v
[3. Cari Obat INN di Autocomplete] (Hanya 1.231 Senyawa is_simulatable=TRUE)
            |
            v
[4. Input Dosis Bolus Tunggal (mg)] (Tanpa Aturan Frekuensi / Dosis Berulang)
            |
            v
[5. Input 4 Kovariat Pasien] (Usia, Jenis Kelamin, Berat kg, Tinggi cm)
            |
            v
[6. Klik Tombol "SIMULASIKAN TOKSISITAS"]
            |
            v
[7. Popup Disclaimer] --> Centang checkbox --> Klik "JALANKAN SIMULASI"
            |
            v
[8. Backend: Paralel GATNN-DNN & SciPy ODE <= 5 dtk]
            |
            v
[9. Inspeksi Visual 3D Hati Couinaud]
   - Rotasi 360, Zoom, Cek Warna & Kedip Hotspot Segmen
            |
            v
[10. Analisis Kurva Paparan & SHAP]
    - Tinjau Dinamika C_hati vs t
    - Highlight Gugus Toxicophore
            |
            v
[11. Unduh Laporan PDF]
    - Tombol di Top Bar sekarang AKTIF
            |
            v
[12. Selesai - Dokumentasi Riset Praklinis Sah]
```

1. **Akses Portal Web:** Pengguna membuka URL deployment HepaTwin melalui peramban web desktop/laptop menggunakan protokol keamanan HTTPS.
2. **Lihat Top Bar & Footer:** Pengguna dapat melihat Logo HepaTwin, judul, dan subtitle di Top Bar, serta Medical Disclaimer permanen di Footer.
3. **Pilih Senyawa Terverifikasi:** Pengguna mengetik nama obat umum (INN, contoh: *acetaminophen*, *isoniazid*, *ibuprofen*) pada *search bar* Panel Kiri dan memilih dari daftar *autocomplete* (filter 1.231 senyawa `is_simulatable = TRUE`).
4. **Masukkan Dosis Tunggal:** Pengguna mengisi angka dosis bolus akut dalam satuan mg (misal: 500 mg, 1000 mg, atau 4000 mg) tanpa parameter frekuensi pemakaian.
5. **Lengkapi Kovariat Demografis:** Pengguna memasukkan empat parameter fisik pasien: Usia, Jenis Kelamin, Berat Badan (kg), dan Tinggi Badan (cm) agar sistem dapat menjalankan penskalaan alometrik PBPK secara akurat [12].
6. **Tekan Tombol Simulasi:** Pengguna menekan tombol **"Simulasikan Toksisitas"**.
7. **Popup Disclaimer:** Sistem menampilkan popup modal disclaimer dengan tiga checkbox. Pengguna WAJIB mencentang semua checkbox untuk mengaktifkan tombol "Lanjutkan Simulasi".
8. **Jalankan Simulasi:** Setelah disclaimer disetujui, dalam durasi ≤ 5 detik, backend mengeksekusi inferensi PyTorch GATNN-DNN dan solver SciPy ODE PBPK secara paralel [9, 11].
9. **Eksplorasi Visual 3D Anatomi:** Pengguna memutar dan memperbesar model hati 3D pada Panel Kanan untuk melihat hotspot pada Segmen Couinaud yang tertarik [13].
10. **Analisis Grafik & Explainability:** Pengguna meninjau kurva temporal konsentrasi hati pada Panel Bawah Kiri dan mengamati struktur molekul 2D ber-highlight merah (*toxicophore*) dari luaran SHAP pada Panel Bawah Kanan.
11. **Unduh Laporan PDF:** Tombol **"Unduh Laporan PDF"** di Top Bar sekarang menjadi **aktif**. Pengguna dapat menekan tombol ini untuk menyimpan dokumen ringkasan ilmiah lengkap.
12. **Selesai:** Laporan PDF tersimpan di perangkat pengguna sebagai catatan praklinis in-silico yang sah dan terdokumentasi.

---

## 11. REGULASI, CREDIBILITY ASSESSMENT, DAN MEDICAL DISCLAIMER — UPDATED v2.3

### 11.1 Context of Use (CoU) dan Credibility Plan

HepaTwin mengadopsi prinsip **risk-informed credibility assessment** sebagaimana dirumuskan dalam FDA guidance *Assessing the Credibility of Computational Modeling and Simulation in Medical Device Submissions* [28]. FDA mendefinisikan credibility sebagai kepercayaan terhadap kemampuan prediktif model untuk suatu context of use, dan menekankan question of interest, context of use, model risk, credibility evidence, verification, validation, uncertainty quantification, dan adequacy assessment [28].

**Question of Interest HepaTwin Fase 1:**
> “Apakah kombinasi informasi struktur kimia, label DILI literatur, dan simulasi PBPK sederhana dapat membantu pengguna riset/edukasi memprioritaskan senyawa untuk kajian hepatotoksisitas lebih lanjut?”

**Context of Use v2.3:**

| Elemen | Pernyataan v2.3 |
|---|---|
| Intended use | DSS praklinis in-silico untuk riset/edukasi dan triase awal kandidat senyawa |
| Not intended use | Diagnosis pasien, rekomendasi dosis, keputusan terapi, pengganti uji lab/klinis/regulator |
| Model influence | Rendah–menengah: model hanya memberi prioritas/hipotesis, bukan keputusan tunggal |
| Decision consequence | Rendah bila disclaimer dipatuhi; tidak ada tindakan medis langsung |
| Credibility status | **Prospective credibility plan**, belum post-study validation final |

**Kewajiban bukti kredibilitas sebelum klaim final:**

1. Code verification solver ODE (`NaN/overflow/convergence=0`).
2. Unit test formula alometrik dan guard XLogP NULL.
3. Calibration sweep exposure v2.3 dengan hash dataset/config.
4. Benchmark AI terpisah dengan train/validation/test split terdokumentasi.
5. Validasi kurasi DILIrank/PubChem/LiverTox oleh Farmasi.
6. UAT pengguna dan review pakar terhadap disclaimer agar tidak terjadi overclaim.
7. Laporan `PBPK_Engine_Audit_Report_v2_3.md` dan `Credibility_Assessment_Report_v2_3.md`.

> **Koreksi v2.3:** Dokumen ini tidak lagi menyatakan bahwa “validasi DILIrank/LiverTox otomatis memadai”. Kecukupan validasi harus dibuktikan sesuai CoU dan model risk [28].

### 11.2 Penanganan Kasus dan Batasan Validitas (Medical Disclaimer)

#### A. Footer Disclaimer Permanen

> **PENTING (MEDICAL DISCLAIMER) [v2.3]:** HepaTwin adalah perangkat lunak penunjang keputusan praklinis yang murni bersifat in-silico untuk riset/edukasi. Hasil AI, SHAP, PBPK, dan visualisasi 3D bertujuan membantu penyusunan hipotesis dan triase awal, **bukan diagnosis klinis, bukan rekomendasi terapi/dosis, dan bukan pengganti uji in-vitro, in-vivo, uji klinis, atau penilaian regulator**. PBPK Fase 1 linear tanpa absorpsi oral, protein binding, Km/Vmax, NAPQI/glutathione, dan parameter IVIVE compound-specific penuh. Warna segmen Couinaud adalah heuristik visual pedagogis, bukan lokalisasi histologis klinis. Ambang AI/exposure bersifat distribusional internal dan pending validasi K2/K3/K6.

#### B. Popup Disclaimer Checklist

Popup memiliki tiga checkbox sebagaimana §9.3 dan wajib disetujui sebelum simulasi.

#### C. Transparansi PBPK

Endpoint `GET /api/v1/pbpk/debug` wajib tersedia untuk menampilkan seluruh parameter alometrik, flag asumsi, dan metrik paparan (§8.2.3).

#### D. Laporan PDF

Laporan PDF wajib mencantumkan:

- versi PRD/config;
- tanggal simulasi;
- daftar asumsi aktif;
- `segment_mapping_type = PEDAGOGICAL_HEURISTIC`;
- `exposure_category_source = INTERNAL_DISTRIBUTIONAL_CALIBRATION`;
- disclaimer bahwa hasil bukan keputusan klinis.

---

## 12. METODOLOGI PENGEMBANGAN AGILE SCRUM (8 SPRINTS, 11 MINGGU)

Pengembangan perangkat lunak HepaTwin dilaksanakan dalam kerangka Agile Scrum selama **11 minggu terbagi dalam 8 Sprint (Sprint 0 hingga Sprint 7)**:

| Sprint & Milestone | Durasi | Sprint Goal | Target Output Utama / Acceptance Deliverables | Status Pelaksanaan |
| :--- | :---: | :--- | :--- | :--- |
| **Sprint 0** | 1 Minggu | Fondasi Infrastruktur & Pipeline Visualisasi 3D Awal | Boilerplate GitHub (React / FastAPI), ekspor mesh 3D hati (`.glb`) 8 Segmen Couinaud ke WebGL, desain arsitektur tiga panel dashboard | **Selesai (100%)** |
| **Sprint 1** | 2 Minggu | Mesin AI Prediksi DILI (GATNN-DNN) + SHAP | Kurasi DILIrank 2.0 [14] untuk training (dedup InChIKey stereo-aware: 0 dihapus; korpus training 1.231 senyawa `is_simulatable = TRUE`, 105 biologik di Supabase tanpa masuk AI) + enrichment LiverTox [18] di Supabase, ekstraksi fitur ECFP4 (RDKit), checkpoint PyTorch GATNN-DNN, integrasi SHAP | **Berjalan (70%)** |
| **Sprint 2** | 1 Minggu | Pemodelan PBPK 4-Kompartemen & Penskalaan Alometrik | Solver ODE PBPK 4-kompartemen (SciPy) untuk $C_{\text{hati}}(t)$, modul konversi alometrik kovariat → $V_L$, $Q_L$, $Cl_{\text{metabolisme}}$, **plus Kp_R dinamis + fallback XLogP + clamp** — **UPDATED v2.3**, validasi internal oleh spesialis Farmasi | **Berjalan (60% → 80% post-audit)** |
| **Sprint 3** *(Wajib selesai - Syarat Submit Penyisihan)* | 1 Minggu | Resolusi Nomenklatur, Pemetaan Segmen Couinaud, Hotspot 3D, Staging Deploy | Kurasi offline deskriptor PubChem PUG REST [15] (1.231/1.231 CID unik ter-resolve), autocomplete lookup lokal berfilter `is_simulatable = TRUE`, visualisasi 1.231 senyawa simulatable melalui segmen Couinaud atau hotspot difus sesuai ketersediaan pola cedera, implementasi blinking hotspot WebGL, serta deployment staging (Vercel/Render) dengan fungsionalitas minimal 50% | **Berjalan (50–70%)** |
| **Sprint 4** | 2 Minggu | Fusi Penuh AI + PBPK, Integrasi 100% Dashboard | Lapisan fusi rule-based dengan **ambang T_LOW/HIGH distribusional pending K2 + exposure_index kuantil v2.3 pending K3**, integrasi penuh FastAPI–React (100% fungsionalitas teknis) | **Rencana (0% → pending K2/K3)** |
| **Sprint 5** | 1 Minggu | Uji Fungsionalitas, Usability Klinis (UAT & SUS), Validasi Pakar | Pelaksanaan UAT dan pengujian *System Usability Scale* (SUS) pada 30 mahasiswa/pelajar farmasi, validasi model ilmiah oleh pakar farmakologi **termasuk validasi K2/K3 & K6** | **Rencana (0%)** |
| **Sprint 6** | 2 Minggu | Refactoring Umpan Balik, Optimasi 3D, Dokumentasi | Perbaikan bug hasil UAT/SUS/pakar, optimasi frame rate WebGL ≥ 30 FPS, penyusunan dokumentasi teknis & panduan pengguna **+ ERRATA_PRD_PBPK.md** | **Rencana (0%)** |
| **Sprint 7** *(Wajib selesai - Syarat Finalis November)* | 1 Minggu | Production Release, System Freeze, Audit Teknis | Deployment produksi (Vercel + Render, SSL/HTTPS penuh), uji penetrasi keamanan sederhana & uji beban API, persiapan audit source code Babak Final **+ PBPK_Engine_Audit_Report_v2_3.md final** | **Rencana (0%)** |

---

## 13. MANAJEMEN RISIKO & BACKLOG VALIDASI FARMASI — UPDATED v2.3

Sebagai sistem komputasi lintas TI-Farmasi, HepaTwin v2.3 mengubah backlog menjadi daftar risiko yang eksplisit, terukur, dan tidak menutup-nutupi asumsi.

| # | Risiko / Catatan Verifikasi | Bab | Status / Mitigasi v2.3 |
| :---: | :--- | :---: | :--- |
| **1** | **Acetaminophen demo salah dosis pada v2.1**: 4.000 mg bukan overdose akut tunggal dewasa 70 kg | §9.4 | **Diperbaiki:** demo overdose menjadi 10.500 mg (150 mg/kg). 4.000 mg hanya disebut dosis maksimum/tinggi, bukan acute overdose [29, 30]. |
| **2** | **PBPK linear tidak memodelkan NAPQI/glutathione** | §8.2, §9.4 | **Dinyatakan eksplisit:** APAP injury timeline 24–96 jam tidak diprediksi PBPK Fase 1. Future work: model non-linear APAP/NAPQI. |
| **3** | **BMI Cl -20% tidak bersumber** | §8.2 | **Dihapus dari default:** BMI≥30 menjadi flag risiko, bukan pengurang Cl otomatis. Sesuai Ghabril [17]. |
| **4** | **Cmax/AUC salah disebut magnitude exposure** | §8.2 | **Diperbaiki:** menjadi `shape_ratio_h_inv`. Kategori exposure memakai `exposure_index` dan kuantil calibration sweep internal. |
| **5** | **Kp_R heuristic belum tervalidasi** | §8.2 | **Tetap sebagai heuristic terkendali:** exponent 0.25, clamp 1–10, fallback NULL, ditandai pending K3. |
| **6** | **Mapping Couinaud dapat overclaim** | §8.3 | **Diperbaiki:** payload dan UI wajib menyatakan `PEDAGOGICAL_HEURISTIC`, bukan clinical localization. |
| **7** | **1.231 simulatable/105 non-simulatable bukan dari DILIrank langsung** | §8.4 | **Diperbaiki atribusi:** DILIrank 1.336 adalah sumber; angka simulatable adalah hasil kurasi internal yang harus dibuktikan dengan SQL/hash. |
| **8** | **SHAP mis-citation** | §8.1 | **Diperbaiki:** Lundberg & Lee [27] sebagai rujukan utama SHAP; InterDILI [10] untuk interpretability/attention. |
| **9** | **Status production-ready overclaim** | Header, §11 | **Diperbaiki:** status development baseline pending K2/K3/K6; credibility plan mengikuti FDA [28]. |
| **10** | **Referensi [26] gabungan tidak valid** | §14 | **Diperbaiki:** Olaparib [26] dan Rilzabrutinib [32] dipisahkan. |

---

## 14. DAFTAR REFERENSI ILMIAH & DOKUMEN OTORITATIF — UPDATED v2.3

> Catatan v2.3: daftar ini **tidak lagi diklaim seluruhnya 2021–2026**. Beberapa sumber adalah *foundational classics* yang tetap diperlukan. Klaim yang berasal dari kurasi internal HepaTwin harus dibuktikan dengan artefak internal (SQL count, hash dataset, audit log), bukan dilemparkan ke sumber eksternal.

1. **D. Sun, W. Gao, H. Hu, and S. Zhou**, "Why 90% of clinical drug development fails and how to improve it?" *Acta Pharmaceutica Sinica B*, vol. 12, no. 7, pp. 3049–3062, 2022. https://doi.org/10.1016/j.apsb.2022.02.002

2. **A. Malka-Markovitz et al.**, "Multiscale modeling of drug-induced liver injury from organ to lobule," *npj Digital Medicine*, vol. 8, p. 383, 2025. https://doi.org/10.1038/s41746-025-01736-6

3. **H. Jaeschke and A. Ramachandran**, "Acetaminophen hepatotoxicity: Paradigm for understanding mechanisms of drug-induced liver injury," *Annual Review of Pathology: Mechanisms of Disease*, vol. 19, pp. 453–478, 2024. https://doi.org/10.1146/annurev-pathmechdis-051122-094016

4. **M. Garcia de Lomana, D. Gadaleta, M. Raschke, R. Fricke, and F. Montanari**, "Predicting liver-related in vitro endpoints with machine learning to support early detection of drug-induced liver injury," *Chemical Research in Toxicology*, vol. 38, no. 4, pp. 656–671, 2025. https://doi.org/10.1021/acs.chemrestox.4c00453

5. **A. Ahluwalia et al.**, "What's in a NAM? – New Approach Methodologies as species-specific, non-animal methods and distinction from 3Rs," *Lab Animal*, 2026. https://doi.org/10.1038/s41684-026-01731-8

6. **J. T. Atkins et al.**, "Pre-clinical animal models are poor predictors of human toxicities in phase 1 oncology clinical trials," *British Journal of Cancer*, vol. 123, no. 10, pp. 1496–1501, 2020. https://doi.org/10.1038/s41416-020-01033-x

7. **H. Lee, J. Kim, J.-W. Kim, and Y. Lee**, "Recent advances in AI-based toxicity prediction for drug discovery," *Frontiers in Chemistry*, vol. 13, 2025. https://doi.org/10.3389/fchem.2025.1632046

8. **T. Lee and J. M. Posma**, "Improving drug-induced liver injury prediction using graph neural networks with augmented graph features from molecular optimisation," *Journal of Cheminformatics*, vol. 17, p. 124, 2025. https://doi.org/10.1186/s13321-025-01068-3

9. **A. S. Wibowo, K. T. Chong, and H. Tayara**, "Enhancing DILI toxicity prediction through integrated graph attention (GATNN) and dense neural networks (DNN)," *Toxicology*, vol. 514, p. 154108, 2025. https://doi.org/10.1016/j.tox.2025.154108

10. **S. Lee and S. Yoo**, "InterDILI: Interpretable prediction of drug-induced liver injury through permutation feature importance and attention mechanism," *Journal of Cheminformatics*, vol. 16, no. 1, 2024. https://doi.org/10.1186/s13321-023-00796-8

11. **W.-C. Chou and Z. Lin**, "Machine learning and artificial intelligence in physiologically based pharmacokinetic modeling," *Toxicological Sciences*, vol. 191, no. 1, pp. 1–14, 2023. https://doi.org/10.1093/toxsci/kfac101

12. **M. C. Mallillin III et al.**, "Beyond body weight: A comprehensive review of allometric scaling in drug development for human dose predictions," *Pharmaceutics*, vol. 18, no. 7, p. 824, 2026. https://doi.org/10.3390/pharmaceutics18070824

13. **E. M. Pauli, K. F. Staveley-O'Carroll, M. V. Brock, D. T. Efron, and G. Efron**, "A Handy Tool to Teach Segmental Liver Anatomy to Surgical Trainees," *Archives of Surgery*, vol. 147, no. 8, pp. 692–693, 2012. https://doi.org/10.1001/archsurg.2012.689 — open-access PMC explanation of the Couinaud 1–8 segment model, citing Couinaud's original segmentation work.

14. **A. O. Olubamiwa, Y. Qu, S. Connor, W. Tong, D. Li, and M. Chen**, "DILIrank 2.0: An updated and expanded database for drug-induced liver injury risk based on FDA labeling and a literature review," *Drug Discovery Today*, vol. 30, no. 11, p. 104485, 2025. https://doi.org/10.1016/j.drudis.2025.104485. Dataset FDA: https://www.fda.gov/science-research/liver-toxicity-knowledge-base-ltkb/drug-induced-liver-injury-rank-dilirank-20-dataset

15. **S. Kim et al.**, "PubChem 2025 update," *Nucleic Acids Research*, vol. 53, no. D1, pp. D1516–D1525, 2025. https://doi.org/10.1093/nar/gkae1059

16. **S. Yu, J. Li, T. He, and H. Zheng**, "Age-related differences in drug-induced liver injury: A retrospective single-center study from a large liver disease specialty hospital in China, 2002–2022," *Hepatology International*, vol. 18, no. 4, pp. 1202–1213, 2024. https://doi.org/10.1007/s12072-024-10679-1

17. **M. Ghabril, R. Vuppalanchi, and N. Chalasani**, "Drug-induced liver injury in patients with chronic liver disease," *Liver International*, vol. 45, no. 3, p. e70019, 2025. https://doi.org/10.1111/liv.70019

18. **LiverTox**, *Clinical and Research Information on Drug-Induced Liver Injury [Internet]*. Bethesda (MD): NIDDK, 2012–. https://www.ncbi.nlm.nih.gov/books/NBK547852/

19. **R. J. Fontana et al.**, "AASLD practice guidance on drug, herbal, and dietary supplement-induced liver injury," *Hepatology*, vol. 77, no. 3, pp. 1036–1065, 2023. https://doi.org/10.1002/hep.32689


20. **K. Soejima, H. Sato, and A. Hisaka**, "Age-related change in hepatic clearance inferred from multiple population pharmacokinetic studies: Comparison with renal clearance and their associations with organ weight and blood flow," *Clinical Pharmacokinetics*, vol. 61, no. 2, pp. 295–305, 2022. https://doi.org/10.1007/s40262-021-01069-z


21. **P. Deurenberg, J. A. Weststrate, and J. C. Seidell**, "Body mass index as a measure of body fatness: Age- and sex-specific prediction formulas," *British Journal of Nutrition*, vol. 65, no. 2, pp. 105–114, 1991. https://doi.org/10.1079/BJN19910073

22. **S. Choi, S. Han, S. J. Lee, B. Lim, S. H. Bae, S. Han, and D.-S. Yim**, "DallphinAtoM: Physiologically based pharmacokinetics software predicting human PK parameters based on physicochemical properties, in vitro and animal in vivo data," *Computer Methods and Programs in Biomedicine*, vol. 216, p. 106662, 2022. https://doi.org/10.1016/j.cmpb.2022.106662

23. **M. Li et al.**, "Physiological parameter values for physiologically based pharmacokinetic models in food-producing animals. Part III: Sheep and goat," *Journal of Veterinary Pharmacology and Therapeutics*, vol. 44, pp. 456–477, 2021. https://doi.org/10.1111/jvp.12938

24. **A. L. Coutinho et al.**, "Relative Performance of Volume of Distribution Prediction Methods for Lipophilic Drugs with Uncertainty in LogP Value," *Pharmaceutical Research*, vol. 41, pp. 1121–1138, 2024. https://doi.org/10.1007/s11095-024-03703-4

25. **A. Daina, O. Michielin, and V. Zoete**, "SwissADME: a free web tool to evaluate pharmacokinetics, drug-likeness and medicinal chemistry friendliness of small molecules," *Scientific Reports*, vol. 7, p. 42717, 2017. https://doi.org/10.1038/srep42717

26. **D. Gao, G. Wang, H. Wu, and J. Ren**, "Physiologically-based pharmacokinetic modeling for optimal dosage prediction of olaparib when co-administered with CYP3A4 modulators and in patients with hepatic/renal impairment," *Scientific Reports*, vol. 13, p. 16027, 2023. https://doi.org/10.1038/s41598-023-43258-9

27. **S. M. Lundberg and S.-I. Lee**, "A Unified Approach to Interpreting Model Predictions," *Advances in Neural Information Processing Systems*, vol. 30, 2017. https://proceedings.neurips.cc/paper_files/paper/2017/file/8a20a8621978632d76c43dfd28b67767-Paper.pdf

28. **U.S. Food and Drug Administration (FDA)**, *Assessing the Credibility of Computational Modeling and Simulation in Medical Device Submissions: Guidance for Industry and Food and Drug Administration Staff*, issued Nov. 17, 2023. https://www.fda.gov/media/154985/download

29. **LiverTox**, "Acetaminophen," *LiverTox: Clinical and Research Information on Drug-Induced Liver Injury*, NIDDK/NCBI Bookshelf, last update Jan. 28, 2016. https://www.ncbi.nlm.nih.gov/books/NBK548162/

30. **MSD Manual Professional Edition**, "Acetaminophen Poisoning," full review Apr. 2025, updated Mar. 2026. https://www.msdmanuals.com/professional/injuries-poisoning/poisoning/acetaminophen-poisoning

31. **K. Holt, S. Nagar, and K. Korzekwa**, "Methods to Predict Volume of Distribution," *Current Pharmacology Reports*, vol. 5, pp. 391–399, 2019. https://doi.org/10.1007/s40495-019-00186-5

32. **X. Yan, Z. Yan, L. Xiao, et al.**, "PBPK modeling predicts rilzabrutinib dose adjustments using BTK occupancy for CYP3A4 interactions and hepatic impairment," *Scientific Reports*, vol. 16, article 20275, 2026. https://doi.org/10.1038/s41598-026-50990-5

33. **LiverTox**, "Ibuprofen," *LiverTox: Clinical and Research Information on Drug-Induced Liver Injury*, NIDDK/NCBI Bookshelf, last update Jul. 20, 2025. https://www.ncbi.nlm.nih.gov/books/NBK547845/

---
## 15. LAMPIRAN: DEFINITION OF DONE (DOD) & ACCEPTANCE CRITERIA PER MODUL — UPDATED v2.3

Sebuah fitur atau modul dinyatakan selesai (**DONE**) apabila memenuhi seluruh kriteria penerimaan berikut:

### 1. Modul Frontend & 3D WebGL (React / React Three Fiber)

- [x] Tampilan dasbor 3 panel responsif dan bebas dari cacat layout pada resolusi desktop standar (1920x1080 dan 1366x768).
- [x] Autocomplete memvalidasi dan membatasi masukan hanya pada 1.231 senyawa `is_simulatable = TRUE`.
- [x] Model 3D hati (mesh 8 Segmen Couinaud `.glb`) berhasil dirender pada frame rate minimal 30 FPS di browser Chrome/Firefox.
- [x] Interaksi rotasi, zoom, pan, dan indikator *blinking hotspot* (warna Hijau/Kuning/Merah dan kecepatan kedip) sinkron 100% dengan payload JSON Lapisan Fusi backend.

### 2. Modul Backend Application & API (FastAPI)

- [x] Endpoint `/api/v1/simulate` menerima payload input JSON yang tervalidasi skema Pydantic.
- [x] Total waktu tanggap endpoint (inferensi AI + solver PBPK 24 jam) di bawah 5 detik.
- [x] Sistem mengimplementasikan caching client-side dan offline lookup deterministik pada tabel `hepatwin_compounds` tanpa memanggil API eksternal saat runtime.
- [x] Error handling yang rapi dengan HTTP status code 422 (Unprocessable Entity - Biologik) dan 404 (Not Found - Di Luar Daftar).
- [x] **[BARU v2.3]** Endpoint `GET /api/v1/pbpk/debug` return `V_L, Q_L, Cl, %BF, Kp_R, cmax, auc, ratio, exposure_category` untuk transparansi pakar/juri.

### 3. Modul AI Predictor (GATNN-DNN & SHAP)

- [x] Model `model_gatnn_dnn.pt` berjalan di dalam environment PyTorch/FastAPI dalam mode evaluasi (*forward pass*) tanpa *retraining* saat runtime.
- [x] RDKit berhasil mengekstrak graf molekul dan sidik jari ECFP4 dari SMILES tersimpan tanpa gagal.
- [x] Keluaran probabilitas hepatotoksisitas $P_{\text{DILI}}$ dan koordinat atom SHAP (*toxicophore*) tepat dan reprodusibel.
- [ ] **[v2.3 — dari F9-1/10]** Ambang `FUSION_AI_T_LOW/HIGH` ditandai `[KEPUTUSAN AI -- PENDING K2]` (distribusional, bukan klinis) + SHAP tail latency <5 detik p95 atau fallback.

### 4. Modul PBPK Solver & Alometrik (SciPy ODE) — UPDATED v2.3

- [x] **[v2.3]** `allometric_service.py` menerapkan `V_P=0.043×BB`, `V_L=0.0257×BB`, `V_K=0.0044×BB`, `Q_C=360×(BB/70)^0.75`, `Q_L=0.25×Q_C×age_factor`, dan `Q_K=0.20×Q_C` sesuai §8.2.
- [x] **[v2.3]** Formula %BF bercabang usia: Deurenberg anak `≤15` dan dewasa `≥16`, dengan clamp 3–60% dan warning bila keluar rentang.
- [x] **[v2.3]** Default BMI clearance penalty dihapus: `clearance_multiplier_from_bmi=1.0`; `BMI≥30` hanya `metabolic_risk_flag`.
- [x] **[v2.3]** `Kp_R` memakai fallback `XLogP NULL→0`, clamp XLogP -1–7, exponent 0.25, clamp Kp_R 1–10, dan test `null/negative/extreme`.
- [x] **[v2.3]** `exposure_evaluator.py` mengganti kategori rasio `Cmax/AUC` menjadi `exposure_index=log1p(Cmax_L)+log1p(AUC_L)` dengan kuantil calibration sweep; `Cmax/AUC` hanya `shape_ratio_h_inv`.
- [x] **[v2.3]** Endpoint `GET /api/v1/pbpk/debug` mengembalikan semua parameter debug pada §8.2.3.
- [x] **[v2.3]** Skenario APAP demo memakai 10.500 mg untuk pasien 70 kg; 4.000 mg tidak boleh disebut overdose akut.

### 5. Modul Database & Security (Supabase)

- [x] Tabel `hepatwin_compounds` memuat 1.336 baris senyawa utuh dari DILIrank 2.0 (termasuk 1 duplikat *Epoetin alfa/Erythropoietin* yang sah dan 105 senyawa biologik berstatus `is_simulatable = FALSE`).
- [x] Kueri lookup berfilter `is_simulatable = TRUE` dengan primary key `hepatwin_id` memiliki indeks database (*B-Tree index*) dengan waktu kueri ≤ 50 ms.
- [x] Keamanan tabel dijamin dengan kebijakan *Row Level Security (RLS)* untuk akses read-only publik pada senyawa yang terdaftar.
- [x] **[BARU v2.3]** Kolom `xlogp` NULL fallback terdokumentasi di §8.4 + test query `WHERE xlogp IS NULL` tidak crash.

---

*HepaTwin PRD v2.3 — Update Post-Audit PBPK Brutal 2026-08-06. Dokumen ini adalah acuan resmi pengembangan terbaru, menggantikan v2.0. Semua perubahan valid, akurat, dan dapat dipertanggungjawabkan dengan 28 referensi referensi ilmiah/standar modern + foundational classics yang dibaca penuh (hierarki Indonesia>Global jujur nihil PBPK Indonesia).*