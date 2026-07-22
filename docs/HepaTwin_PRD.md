# Product Requirements Document (PRD)
## HepaTwin — Digital Twin Hati Berbasis AI untuk Simulasi Visual 3D Hepatotoksisitas Obat & Triase Praklinis In-Silico

**Versi Dokumen:** 1.0
**Diturunkan dari:** HepaTwin_Draft_Proposal_GEMASTIK_2026_Rev_2.docx
**Status:** Draft untuk pengembangan — selaras dengan proposal GEMASTIK XVIII/2026, Kompetisi VIII (Pengembangan Perangkat Lunak)
**Pemilik Produk:** Tim HepaTwin (Ketua Tim, AI/ML & 3D Engineer, Domain Expert Farmasi)

---

## 1. Ringkasan Eksekutif

HepaTwin adalah aplikasi web interaktif yang mensimulasikan dan memvisualisasikan **hepatotoksisitas obat (Drug-Induced Liver Injury / DILI)** dalam bentuk digital twin 3D hati, sekaligus berfungsi sebagai **alat bantu triase praklinis in-silico berbiaya rendah**. Produk ini memiliki dua mode utama:

1. **Mode Edukasi Mendalam** — dua senyawa flagship (Parasetamol & Amoxicillin-Clavulanate) dengan model PK/PD matematis dan visualisasi zonal 3D mendalam, ditujukan untuk pembelajaran farmakologi/toksikologi.
2. **Mode Triase Umum** — input SMILES bebas untuk sembarang senyawa, menghasilkan skor risiko DILI + explainability kimia + heatmap generik, ditujukan sebagai alat bantu prioritisasi awal bagi peneliti/lab riset berdaya terbatas.

**Prinsip non-negosiabel produk:** HepaTwin **BUKAN** pengganti uji toksisitas/klinis/keputusan regulasi. Ini harus tercermin dalam desain (disclaimer permanen), performa yang dilaporkan apa adanya, dan komunikasi produk di setiap titik sentuh pengguna.

---

## 2. Latar Belakang & Masalah yang Dipecahkan

### 2.1 Masalah
- Materi ajar DILI (Toksikologi Klinik, Farmakokinetika, Farmakologi Sistem Organ) hanya tersedia dalam bentuk statis (diagram 2D, gambar histopatologi, tabel angka), sehingga sulit membangun pemahaman visual-spasial-temporal mahasiswa.
- Software PK/PD komersial (DILIsym, NONMEM, Simcyp) berbiaya puluhan-ratusan juta rupiah/tahun, tidak terjangkau bagi banyak lab riset/pengajaran kampus.
- Platform anatomi 3D (BioDigital Human, VOKA) bersifat pre-set statis, tidak digerakkan oleh input dosis/senyawa dinamis.
- Model AI prediktif DILI yang ada berhenti pada skor numerik/klasifikasi biner tanpa jembatan ke pemahaman visual.
- Uji in vitro/in vivo mahal, lambat, dan tidak dapat diakses untuk pembelajaran massal maupun triase cepat.

### 2.2 Kesenjangan yang Diisi HepaTwin
Aplikasi web yang menggabungkan **dua lapisan komputasi dengan peran jelas**:
- Persamaan diferensial PK/PD untuk senyawa bermekanisme diketahui (Parasetamol).
- Skor klasifikasi AI sebagai penggerak visual utama untuk senyawa bermekanisme belum diketahui (Amoxicillin-Clavulanate & Mode Triase Umum).

Prinsip desain ini memastikan AI adalah **kebutuhan genuine**, bukan pelengkap kosmetik — dapat dibuktikan lewat uji "kalau komponen AI dihapus, apa yang rusak?" (lihat §8.5).

### 2.3 Relevansi
- SDG 4 (Quality Education) & SDG 3 (Good Health and Well-being).
- Selaras dengan Panduan Kurikulum Farmasi 2024 (APTFI) — outcome-based education, simulation-based learning (OSCE).
- Parasetamol adalah obat paling banyak dikonsumsi di Indonesia (~9.000 ton/tahun).

### 2.4 Batasan Klaim Manfaat Sosial (penting untuk tim produk)
Klaim manfaat menggunakan dua lapis: (a) **klaim kuat** — penghematan biaya lisensi software PK/PD komersial; (b) **klaim proksi** — disparitas infrastruktur riset Jawa vs luar Jawa (data BPS/PDDikti nasional), yang secara eksplisit dilabeli sebagai indikator **tidak langsung**, bukan data spesifik lab toksikologi Indonesia. Tim produk wajib mempertahankan pelabelan ini dalam semua materi produk/pemasaran agar tidak overclaim.

---

## 3. Tujuan Produk & Success Metrics

| # | Tujuan | Metrik Keberhasilan |
|---|---|---|
| 1 | Visualisasi 3D dua pola mekanisme DILI (hepatoselular dose-dependent & kolestatik idiosinkratik) | Kedua pola dapat ditampilkan, di-zoom makro→mikro, untuk dua senyawa flagship |
| 2 | Model AI hybrid (RDKit substruktur + GNN) untuk SMILES bebas | Model terlatih pada DILIrank, diuji pada external test set Xu et al. (2015) |
| 3 | Jembatan PK/PD matematis ke visual 3D, tervalidasi silang ke nomogram Rumack-Matthew | Kurva Cplasma(t) konsisten posisi relatif terhadap garis 150/200 nomogram |
| 4 | Explainability interpretable secara kimia/farmakologis | Output explainability berupa nama gugus kimia, bukan indeks fitur abstrak |
| 5 | Pelaporan performa model jujur & transparan | Angka aktual (akurasi, AUC, sensitivity, specificity, MCC) dilaporkan apa adanya, dibandingkan dengan baseline Mostafa et al. (2024) |
| 6 | Alat bantu pembelajaran & triase, akses tanpa instalasi | Deploy via 1 URL publik, waktu respons sesuai target NFR (§6.2) |
| 7 | Dampak empiris terukur pada pemahaman mahasiswa | Pre-test/post-test dengan 10–20 partisipan, hasil dilaporkan sebagai preliminary evidence |

**Target performa model (realistis, bukan jaminan):** AUC 0,75–0,85 pada external test set. Baseline pembanding jujur: RF/MLP sederhana hanya mencapai akurasi 0,631 dan MCC 0,245 (Mostafa, Howle, & Chen, 2024) — angka ini WAJIB dicantumkan di laporan/produk sebagai konteks, apa pun hasil aktual HepaTwin.

---

## 4. Ruang Lingkup (Scope)

### 4.1 Dalam Scope

| Aspek | Cakupan |
|---|---|
| Organ | Hati (liver) — fokus tunggal |
| Senyawa — Mode Edukasi Mendalam | Parasetamol (hepatoselular dose-dependent, jalur NAPQI-GSH) & Amoxicillin-Clavulanate (kolestatik idiosinkratik), dengan visualisasi zonal penuh (sentrilobuler / portal-periportal) |
| Senyawa — Mode Triase Umum | Input SMILES bebas untuk sembarang senyawa; keluaran skor risiko DILI + explainability substruktur + heatmap makro generik (bukan zonal spesifik) |
| Mekanisme toksisitas | DILI intrinsik dose-dependent (parasetamol) & idiosinkratik dose-independent (amoxicillin-clavulanate & Mode Triase, digerakkan skor AI) |
| Level visualisasi | Hybrid makro-mikro untuk dua flagship (zoom ke lobulus/area portal); heatmap makro generik untuk Mode Triase Umum |
| Platform | Aplikasi web (browser-based, tanpa instalasi) |
| Pengguna target | Primer: dosen & mahasiswa farmakologi/toksikologi. Sekunder: peneliti/lab riset kecil tanpa akses software PK/PD komersial |

### 4.2 Di Luar Scope (Visi Masa Depan — TIDAK dikerjakan pada versi ini)
- Organ lain (ginjal, jantung, paru-paru).
- Simulasi zonal penuh untuk senyawa di luar dua flagship.
- Prediksi pola mekanisme spesifik (hepatoselular vs kolestatik) untuk senyawa Mode Triase.
- Parameter farmakokinetik individual (farmakogenetik, kondisi pasien spesifik).
- Mekanisme toksisitas hati lain (autoimun, granulomatosa, dsb.).
- Simulasi tingkat subselular/molekuler.
- Aplikasi mobile native, VR/AR, atau desktop.
- Penggunaan sebagai alat regulator (BPOM/FDA) atau dasar keputusan persetujuan obat.

**Catatan Wajib untuk Tim Produk:** Batasan ini harus dikomunikasikan eksplisit di UI (disclaimer) dan di semua materi presentasi/pemasaran untuk menghindari overclaim.

---

## 5. Persona & Use Case

### 5.1 Persona Primer: Dosen & Mahasiswa Farmakologi/Toksikologi
- **Konteks penggunaan:** ruang kuliah (demo dosen via proyektor), laboratorium komputer, studi mandiri di laptop/tablet.
- **Use case:** Dosen mendemonstrasikan dua pola mekanisme DILI secara interaktif; mahasiswa eksplorasi mandiri hubungan dosis–konsentrasi metabolit–progresi kerusakan hati.

### 5.2 Persona Sekunder: Peneliti/Lab Riset Berdaya Terbatas
- **Konteks penggunaan:** sesi riset awal di lab kampus, tanpa akses software PK/PD komersial berlisensi mahal.
- **Use case:** Input SMILES senyawa kandidat riset → estimasi awal risiko DILI + substruktur kontributor → mempercepat diskusi prioritisasi sebelum uji in vitro/in vivo.

### 5.3 Kebutuhan Fungsional Ringkas (per persona)
1. Input dosis + pilihan senyawa flagship (Mode Edukasi Mendalam).
2. Input SMILES bebas (Mode Triase Umum).
3. Output skor risiko DILI.
4. Visualisasi 3D hati interaktif — pola zonal spesifik (flagship) atau heatmap generik (Triase).
5. Fitur zoom makro→mikro (flagship saja).
6. Panel data ilmiah real-time + disclaimer batas klaim yang **selalu tampil** (tidak dapat disembunyikan pada Mode Triase Umum).

---

## 6. Kebutuhan Non-Fungsional

| Kebutuhan | Target |
|---|---|
| Akses | Tanpa instalasi, via URL browser |
| Waktu respons — Mode Edukasi Mendalam | < 3 detik |
| Waktu respons — Mode Triase Umum | < 5 detik (komputasi GNN lebih berat) |
| Kompatibilitas browser | Chrome 100+, Firefox 100+, Safari 15+, Edge 100+ |
| Resolusi layar minimum | 1024×768 px (desktop/laptop disarankan) |
| Desain responsif | Desktop (≥1280px), Tablet (768–1279px), Mobile (≤767px) |
| Usability | Intuitif tanpa pelatihan khusus |

---

## 7. Arsitektur Sistem & Tech Stack

| Layer | Teknologi | Alasan |
|---|---|---|
| Frontend & UI | React.js + Tailwind CSS | State reaktif untuk update visual 3D real-time tanpa reload; Tailwind mempercepat pembangunan UI dasbor medis |
| 3D Rendering Engine | React Three Fiber (Three.js/WebGL) | Model 3D sebagai komponen React; perubahan warna/tekstur organ dipicu langsung oleh state React dari data AI |
| 3D Asset | Format `.glb` / `.gltf` | Ukuran kecil, mendukung PBR material, kompatibel penuh Three.js |
| Animasi Kamera | GSAP (GreenSock) | Interpolasi kamera halus untuk transisi zoom makro→mikro saat hotspot diklik |
| Backend & AI Engine | FastAPI (Python) | Ringan, cepat, otomatis menyediakan Swagger UI |
| AI/ML Model | Hybrid: fitur substruktur RDKit (SMARTS) + GNN (GCN/GAT, PyTorch Geometric) | Kombinasi explainability + daya prediksi lebih baik dari fitur tabular saja, mengikuti GeoDILI (Wu et al., 2023) & graph-attention (Wang et al., 2024) |
| Explainability | SHAP pada fitur substruktur RDKit | Atribusi fitur dapat dipetakan ke gugus kimia/farmakologis nyata |
| Dataset Training | DILIrank (FDA LTKB — 1.036 obat) | Dataset publik terbesar & paling otoritatif untuk prediksi DILI |
| Dataset External Test | Xu et al. (2015) — 344–475 senyawa | Validasi eksternal genuinely independen (kurasi grup riset berbeda) |
| Deployment | Vercel (frontend) + Railway (backend) | Sesuai rencana sprint plan proposal |

### 7.1 Diagram Alur Sistem (System Flow)
1. **INPUT (Frontend):** Pengguna pilih mode — (a) Mode Edukasi Mendalam: pilih senyawa + dosis; (b) Mode Triase Umum: input SMILES (validasi format di sisi client sebelum kirim).
2. **REQUEST:** Frontend React → HTTP POST ke endpoint FastAPI backend.
3. **PROCESSING (percabangan logika):**
   - Parasetamol → simulasi PK/PD (§8.1) sebagai penggerak utama, skor AI sebagai pendamping.
   - Amoxicillin-Clavulanate → model klasifikasi AI (§8.2) sebagai penggerak utama, dengan pemetaan zona portal/periportal.
   - Mode Triase Umum → model AI hybrid generalis (§8.3) → skor risiko DILI + substruktur kontributor, TANPA pemetaan zonal spesifik.
4. **RESPONSE (JSON):** Contoh Mode Triase:
```json
{
  "input_smiles": "...",
  "mode": "triase_umum",
  "DILI_score": 0.58,
  "model_confidence_note": "skor berbasis model riset, bukan hasil uji klinis",
  "explainability": ["gugus X", "gugus Y"],
  "visual_pattern": "heatmap_generik"
}
```
5. **RENDERING:** Frontend update state React → perubahan visual 3D real-time; pola zonal spesifik (flagship) atau heatmap makro generik (Triase); hotspot interaktif zoom ke mikro (flagship saja).
6. **PANEL DATA ILMIAH & DISCLAIMER:** Menampilkan nilai numerik real-time + teks disclaimer permanen pada Mode Triase Umum: *"Skor ini adalah estimasi awal berbasis model riset (AUC eksternal ~0,75–0,85), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat."*

---

## 8. Spesifikasi Model Ilmiah & AI

### 8.1 Model PK/PD — Parasetamol

**Langkah 1 — Model absorpsi oral (turunan Cplasma(t) dari dosis):**
Model kompartemen tunggal, absorpsi order-satu:

```
dAgut(t)/dt = − ka × Agut(t),   Agut(0) = F × Dose
dCplasma(t)/dt = (ka × Agut(t)) / Vd − ke × Cplasma(t)
```

Solusi closed-form:
```
Cplasma(t) = (F × Dose × ka) / (Vd × (ka − ke)) × (e^(−ke×t) − e^(−ka×t))
```

Parameter acuan awal (Morse, Stanescu, Atkinson, & Anderson, 2022 — 116 sukarelawan dewasa sehat):
- F (bioavailabilitas oral) = 86%
- CL (klirens sistemik) = 24,0 L/jam/70kg
- V1 (volume distribusi kompartemen sentral) = 43,5 L/70kg
- t½ absorpsi = 12 menit → ka ≈ 3,47 jam⁻¹
- Lag time absorpsi = 5,3 menit (**belum dimasukkan ke persamaan** — batasan model)
- ke = CL/Vd ≈ 0,55 jam⁻¹

⚠️ **Batasan model yang WAJIB didokumentasikan ke pengguna/juri:** Morse et al. (2022) menggunakan model dua-kompartemen; HepaTwin menyederhanakan menjadi satu-kompartemen. V1 dipakai sebagai pendekatan Vd (bukan Vss sebenarnya). Ini penyederhanaan yang wajar untuk tujuan edukasi, bukan cacat yang disembunyikan.

**Langkah 2 — Persamaan PK (konsentrasi obat di hati):**
```
dCliver(t)/dt = kin × Cplasma(t) − kelim × Cliver(t)
```

**Langkah 3 — Persamaan PD (produksi metabolit toksik NAPQI):**
```
d[NAPQI]/dt = kmeta × Cliver(t) − kGSH × [GSH](t) × [NAPQI](t)
```

**Kondisi pemicu visual:** ketika `[NAPQI](t) / [GSH]0 > θ_threshold` → memicu visual nekrosis pada zona sentrilobuler (Zone 3).

**Klarifikasi ilmiah wajib:** Rasio NAPQI/GSH adalah konstruk mekanistik riset praklinis, TIDAK terukur real-time secara klinis. Alat klinis riil adalah **nomogram Rumack-Matthew** (Rumack & Matthew, 1975; revisi Rumack et al., 1981) — garis "200" dan "150", tetap menjadi standar konsensus AS/Kanada hingga kini (Dart et al., 2023). HepaTwin membedakan kedua hal secara eksplisit di UI: rasio NAPQI/GSH = penggerak visual mikroskopis; nomogram Rumack-Matthew = panel referensi klinis paralel.

**Validasi silang:** Cplasma(t) pada rentang waktu 4–24 jam pasca-konsumsi untuk berbagai skenario dosis harus jatuh pada posisi konsisten relatif terhadap garis 150/200 nomogram.

🔴 **Action item kritis sebelum implementasi:** Nilai k_in, k_elim, k_meta, k_GSH, θ_threshold WAJIB divalidasi oleh anggota tim Farmasi dari literatur primer (Chiew et al., 2023; Du et al., 2024) sebelum masuk kode backend. Parameter kalibrasi nomogram (150/200) juga wajib diverifikasi ke sumber primer.

### 8.2 Model untuk Senyawa Idiosinkratik — Amoxicillin-Clavulanate

- Mekanisme belum sepenuhnya dipahami (diduga reaksi imuno-alergik terkait variasi genetik) → **tidak dapat** direpresentasikan sebagai persamaan diferensial deterministik.
- Skor klasifikasi model AI hybrid (§8.3) adalah **penggerak visual utama** (bukan estimasi pendamping seperti pada parasetamol).
- Pemetaan zonal portal/periportal khusus untuk senyawa ini (berbeda dari Mode Triase Umum yang tanpa pemetaan zonal spesifik).
- Skema warna & lokasi anatomis berbeda dari parasetamol: area portal/periportal + struktur saluran empedu (bukan zona sentrilobuler); tingkat keparahan visual mengikuti skor probabilistik AI, bukan kurva konsentrasi-waktu.

### 8.3 Arsitektur Model AI Hybrid — Mode Triase Umum (Input SMILES Bebas)

**Komponen:**
1. **Lapisan struktural:** fitur substruktur RDKit berbasis notasi SMARTS (untuk explainability).
2. **Lapisan graf molekuler:** representasi graf (atom = node, ikatan kimia = edge) diproses via GCN/GAT (1–2 layer, PyTorch Geometric).
3. **Penggabungan:** kedua lapisan digabung (concatenated) sebelum lapisan klasifikasi akhir, mengikuti pola InterDILI (Lee & Yoo, 2024).

**Target performa & baseline pembanding jujur:**
- Target realistis: AUC 0,75–0,85 pada external test set.
- Rentang literatur riset: AUC 0,71–0,94 tergantung arsitektur/skema validasi.
- Baseline RF/MLP sederhana (Mostafa, Howle, & Chen, 2024): akurasi 0,631, MCC 0,245 — **wajib dicantumkan** sebagai pembanding di laporan akhir, apa pun hasil HepaTwin.

⚠️ **Prinsip pelaporan:** Angka performa AKTUAL (akurasi, AUC, sensitivity, specificity, MCC pada external test set) wajib dilaporkan apa adanya, termasuk jika di bawah target.

### 8.4 Strategi Validasi Eksternal & Deduplikasi (Skema Dua-Tahap)

| Tahap | Dataset | Peran |
|---|---|---|
| Training | DILIrank (Chen et al., 2016) | Dataset publik terbesar/otoritatif |
| External test | Xu et al. (2015), 344–475 senyawa | Independen, dikurasi grup riset berbeda (Peking University), tidak dilihat selama training |

**Deduplikasi wajib:** Sebelum dipakai sebagai test set, SMILES kanonik (via RDKit) pada dataset Xu et al. dicocokkan dengan DILIrank; senyawa tumpang tindih dihapus dari salah satu set — untuk mencegah data leakage semu.

**Dataset yang SENGAJA tidak dipakai:** NCTR — karena merupakan salah satu sumber historis penyusun DILIrank (risiko data leakage).

**Keterbatasan metodologis yang diakui secara eksplisit:** Skema InterDILI asli menggunakan 4 dataset gabungan sebagai training dan DILIrank sebagai test (arah berkebalikan). HepaTwin memakai variasi lebih sederhana (DILIrank sebagai training, Xu et al. sebagai test) karena keterbatasan kapasitas tim — ini harus dinyatakan eksplisit di laporan akhir sebagai batasan yang disadari, bukan disembunyikan.

### 8.5 Lapisan Explainability

- **Tidak** menggunakan indeks bit fingerprint abstrak (mis. "fitur ke-247").
- Menggunakan fitur substruktur kimia (SMARTS/RDKit) + atribusi SHAP → hasil dapat dinyatakan dalam istilah farmakologis dikenal (mis. "cincin beta-laktam pada amoxicillin").
- Berlaku untuk dua senyawa flagship maupun Mode Triase Umum.
- 🔴 Validasi akhir pemetaan gugus kimia → istilah farmakologis WAJIB dilakukan bersama anggota tim Farmasi (dan idealnya dosen pembimbing/kontak Fakultas Farmasi).

### 8.6 Uji "Apa yang Rusak Jika AI Dihapus?" (Prinsip Desain Inti)
- **Parasetamol:** visualisasi tetap dapat berjalan dari persamaan PK/PD saja; AI adalah pelengkap estimasi risiko.
- **Amoxicillin-Clavulanate & seluruh senyawa Mode Triase Umum:** tanpa AI, **tidak ada dasar kalkulasi visual sama sekali** — tidak ada model mekanistik pengganti tersedia.

Ini adalah argumen inti diferensiasi produk dan harus tercermin di semua materi presentasi.

---

## 9. Spesifikasi UI/UX

### 9.1 Layout Tiga Zona
- **Zona Kiri (Input/Kontrol):** Toggle Mode Edukasi Mendalam ↔ Mode Triase Umum di bagian atas; form pemilihan senyawa/slider dosis (mode edukasi) atau text field SMILES (mode triase); tombol "Simulasikan"; indikator status koneksi backend AI.
- **Zona Kanan (Canvas 3D):** Model 3D hati (Three.js) melayang bebas tanpa kontainer kotak, tampilan default model utuh, hotspot interaktif, toggle makro/mikro (dua flagship) atau heatmap generik (Mode Triase).
- **Zona Bawah (Dashboard):** Konten adaptif sesuai mode/senyawa; **selalu** menyertakan teks disclaimer batas klaim (tidak dapat disembunyikan pada Mode Triase Umum).

### 9.2 Skema Warna Heatmap
- Hijau = risiko rendah, Kuning = risiko sedang, Merah = risiko tinggi.

### 9.3 Alur Penggunaan (User Flow)
1. Buka URL aplikasi.
2. Pilih mode (Edukasi Mendalam / Triase Umum).
3. Edukasi Mendalam: pilih senyawa dari dropdown + atur dosis (slider/mg per kg). Triase Umum: input SMILES pada text field.
4. Klik "Simulasikan".
5. Amati perubahan visual 3D (pola sentrilobuler / portal-periportal / heatmap generik).
6. Untuk flagship: klik hotspot untuk zoom-in ke model mikro.
7. Pantau panel data ilmiah + disclaimer.
8. Reset via tombol "Reset" atau ganti mode/senyawa/SMILES.

### 9.4 Persyaratan Screenshot/Mockup Minimum (untuk deliverable proposal, relevan sebagai acceptance criteria desain)
1. Halaman utama dengan toggle mode.
2. Pola sentrilobuler (parasetamol) + panel nomogram Rumack-Matthew.
3. Pola portal/periportal (amoxicillin-clavulanate) + panel explainability gugus kimia.
4. Mode Triase Umum: input SMILES + heatmap generik + disclaimer.

---

## 10. Rencana Evaluasi Dampak Pengguna

| Komponen | Rancangan |
|---|---|
| Desain studi | One-group pretest-posttest design, sesi demo terbimbing di kelas/lab komputer |
| Partisipan | 10–20 mahasiswa Farmasi yang sedang/telah menempuh Farmakologi/Toksikologi |
| Instrumen | Kuesioner pemahaman konsep (5–10 soal), mencakup mekanisme dose-dependent & idiosinkratik, sebelum & sesudah sesi |
| Prosedur | (1) Pre-test 10 menit → (2) Sesi penggunaan HepaTwin 20–30 menit (variasi dosis, dua senyawa) → (3) Post-test → (4) Kuesioner usability singkat |
| Metrik dampak | Selisih skor pre/post-test; skor persepsi kemudahan & kebermanfaatan (deskriptif) |
| Pelaporan | Bagian Progress & Aspek Inovasi proposal, sebagai *preliminary evidence*, bukan validasi statistik formal |

---

## 11. Rencana Pengembangan (Sprint Plan)

| Sprint | Durasi | Target Output |
|---|---|---|
| Sprint 0 — Fondasi | 1 minggu | Setup repo, konfigurasi React + FastAPI, integrasi model 3D hati (.glb) pertama ke Three.js/WebGL, uji koneksi API |
| Sprint 1 — Data & AI Engine Dasar | 3 minggu | Preprocessing DILIrank; unduh & deduplikasi SMILES Xu et al. (2015) sebagai external test set; training model hybrid RDKit + GNN (GCN/GAT); integrasi SHAP; evaluasi performa aktual pada external test set; deployment endpoint FastAPI |
| Sprint 2 — PK/PD Integration | 1 minggu | Implementasi model absorpsi oral (Cplasma(t)); persamaan diferensial PK/PD parasetamol di backend; kalibrasi nomogram Rumack-Matthew; integrasi output ke JSON response |
| Sprint 3 — 3D Visual Dual-Pattern & Mode Triase | 2 minggu | Heatmap shader pola sentrilobuler & portal/periportal; heatmap makro generik Mode Triase; animasi hotspot; zoom GSAP ke mikro; input field SMILES + validasi format |
| Sprint 4 — Dashboard & UX | 1 minggu | Panel data ilmiah adaptif (gauge, mini chart, panel nomogram, panel explainability, disclaimer permanen); desain responsif; UX testing internal |
| Sprint 5 — Evaluasi Dampak | 1 minggu | Pelaksanaan pre-test/post-test; pengumpulan & analisis hasil |
| Sprint 6 — Integrasi & Testing | 1 minggu | End-to-end testing kedua mode; bug fixing; optimasi performa (termasuk waktu respons Mode Triase); deployment ke Vercel + Railway |
| Sprint 7 — Finalisasi | 1 minggu | Validasi akhir tim Farmasi/dosen pembimbing; penyusunan laporan akhir (termasuk performa apa adanya); persiapan demo |

**Catatan:** Sprint 1 diperpanjang dari 2 → 3 minggu (kompleksitas dataset eksternal + GNN). Total durasi bertambah 1 minggu dari rencana awal. Pertimbangkan paralelisasi Sprint 1 & Sprint 2 (PK/PD tidak bergantung pada model AI generalis) jika waktu terbatas.

---

## 12. Pembagian Peran Tim

| Peran | Program Studi | Tanggung Jawab |
|---|---|---|
| Project Manager / Full-stack Web Developer (Ketua Tim) | Teknologi Informasi | Arsitektur sistem React + FastAPI, integrasi API termasuk endpoint Mode Triase Umum |
| AI/ML Engineer & 3D Developer | Teknologi Informasi | Model prediktif hybrid (RDKit + GNN via PyTorch Geometric), explainability (SHAP), strategi validasi eksternal, implementasi React Three Fiber |
| Domain Expert (Farmasi) | Farmasi | Validasi parameter PK/PD, kalibrasi nomogram Rumack-Matthew, kurasi dataset, verifikasi pemetaan explainability, penyusunan disclaimer, koordinasi evaluasi dampak |

Tim berencana melibatkan dosen pembimbing (dan idealnya kontak tambahan di Fakultas Farmasi) untuk membantu validasi ilmiah secara paralel, agar tidak menjadi bottleneck.

---

## 13. Risiko & Item Aksi Kritis (Backlog Validasi)

| # | Item | Penanggung Jawab | Prioritas |
|---|---|---|---|
| 1 | Validasi nilai konstanta PK/PD (k_in, k_elim, k_meta, k_GSH, θ_threshold) dan parameter absorpsi oral (F, CL, V1, ke) dari literatur primer sebelum implementasi kode | Anggota Farmasi | KRITIS |
| 2 | Validasi pola histologis kolestatik amoxicillin-clavulanate & pemetaan gugus kimia ke istilah farmakologis yang benar | Anggota Farmasi | KRITIS |
| 3 | Unduh & verifikasi lisensi/format dataset Xu et al. (2015); laksanakan deduplikasi SMILES kanonik terhadap DILIrank sebelum training | Anggota IT (AI/ML) | KRITIS |
| 4 | Uji kelayakan implementasi GNN (GCN/GAT via PyTorch Geometric) dalam timeline Sprint 1; siapkan fallback ke model fitur-tabular saja jika tidak layak, dan revisi klaim novelty sesuai kondisi aktual | Anggota IT (AI/ML) | KRITIS |
| 5 | Lengkapi sitasi data BPS/PDDikti (URL laporan, tahun akses) atau hapus argumen proksi jika dinilai terlalu lemah | Farmasi + Ketua Tim | TINGGI |
| 6 | Verifikasi ulang seluruh referensi baru Rev 1 & Rev 2 ke sumber primer | Anggota Farmasi | TINGGI |
| 7 | Laksanakan evaluasi dampak pre-test/post-test sebelum deadline penyisihan; isi hasil aktual (termasuk performa model pada external test set) | Semua Anggota | KRITIS |
| 8 | Screenshot/mockup UI untuk KEDUA mode, minimal 4 gambar | Anggota IT | TINGGI |
| 9 | Konfirmasi ketentuan lomba (format proposal, kriteria penilaian, status deployment publik vs klausul "belum dipublikasikan") saat sosialisasi resmi 20 Juli 2026 | Ketua Tim | KRITIS |
| 10 | Video demo (YouTube unlisted) mendemonstrasikan KEDUA mode | Semua Anggota | TINGGI |

### 13.1 Pertanyaan Terbuka yang Berdampak pada Scope/Timeline
- Apakah ada perubahan kriteria penilaian divisi PPL 2026?
- Apakah library open-source pihak ketiga (Three.js, R3F, scikit-learn, PyTorch, PyTorch Geometric, RDKit, SHAP) diperbolehkan tanpa pembatasan?
- Apakah deployment demo publik selama pengembangan berbenturan dengan klausul "belum pernah dipublikasikan" pada Surat Pernyataan Keaslian Karya?
- Apakah sampel evaluasi dampak 10–20 partisipan dianggap memadai oleh juri?
- Bobot penilaian aspek inovasi vs dampak nyata — memengaruhi framing narasi presentasi.
- Risiko klaim "alat bantu triase praklinis" dianggap overclaim tanpa validasi eksternal kuat — ekspektasi ambang performa minimum dari juri?

---

## 14. Disclaimer & Batasan Etis (Non-Negotiable — Wajib Diimplementasikan di Produk)

1. HepaTwin adalah **alat bantu triase/prioritisasi awal**, BUKAN pengganti uji toksisitas/klinis (mengacu Madden, Enoch, Paini, & Cronin, 2020 — tidak ada metode in-silico tunggal yang menggantikan pengujian pada endpoint toksikologi kompleks).
2. Disclaimer permanen pada Mode Triase Umum: teks *"Skor ini adalah estimasi awal berbasis model riset (AUC eksternal ~0,75–0,85), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat."* — **tidak boleh dapat disembunyikan** oleh pengguna.
3. Kontribusi terhadap prinsip 3Rs (Replacement, Reduction, Refinement) bersifat **komplementer**, satu dari kombinasi berbagai teknik triase, bukan pengganti uji hewan/klinis formal.
4. Klaim manfaat sosial proksi (disparitas infrastruktur Jawa vs luar Jawa) harus selalu dilabeli eksplisit sebagai **indikator tidak langsung**.
5. Performa model harus selalu dilaporkan sebagai angka aktual pada test set eksternal — dilarang melaporkan angka target/proyeksi sebagai hasil final.

---

## 15. Referensi Ilmiah Kunci (untuk Tim Pengembang)

Ringkasan rujukan yang menjadi dasar spesifikasi teknis di dokumen ini (daftar pustaka lengkap tersedia di proposal asli):
- **DILI umum & epidemiologi:** Hosack, Damry, & Biswas (2023); Leise, Poterucha, & Talwalkar (2014); Allison et al. (2023).
- **Parasetamol/NAPQI:** Chiew et al. (2023); Du et al. (2024); Morse, Stanescu, Atkinson, & Anderson (2022, model PK).
- **Nomogram Rumack-Matthew:** Rumack & Matthew (1975); Rumack, Peterson, Koch, & Amara (1981); Dart et al. (2023, konsensus terkini).
- **Amoxicillin-clavulanate:** LiverTox/NIDDK; Allison et al. (2023).
- **Model AI DILI (arsitektur hybrid):** Wu et al. (2023, GeoDILI); Wang et al. (2024, graph-attention); Lee & Yoo (2024, InterDILI).
- **Dataset:** Chen et al. (2016, DILIrank); Xu et al. (2015, external test set).
- **Baseline performa jujur:** Mostafa, Howle, & Chen (2024).
- **Prinsip in-silico komplementer:** Madden, Enoch, Paini, & Cronin (2020).
- **Preseden "liver twin":** Dichamp et al. (2023).
- **Kurikulum farmasi:** APTFI (2024).

---

## 16. Lampiran: Definisi Selesai (Definition of Done) per Fitur

| Fitur | Kriteria Selesai |
|---|---|
| Model PK/PD Parasetamol | Persamaan terimplementasi, parameter tervalidasi Farmasi, konsisten dengan nomogram Rumack-Matthew pada rentang 4–24 jam |
| Model AI Hybrid (Triase) | Terlatih pada DILIrank, dievaluasi pada Xu et al. (2015) ter-deduplikasi, angka performa aktual tercatat & dilaporkan |
| Explainability | Output berupa nama gugus kimia yang tervalidasi Farmasi, bukan indeks numerik |
| Visualisasi 3D | Kedua pola zonal (flagship) + heatmap generik (Triase) berfungsi, zoom makro-mikro responsif |
| Disclaimer UI | Selalu tampil pada Mode Triase Umum, tidak dapat disembunyikan pengguna |
| Evaluasi Dampak | Pre/post-test terlaksana dengan 10–20 partisipan, hasil tercatat di laporan |
| Deployment | Aplikasi dapat diakses via 1 URL publik, waktu respons sesuai target NFR |

---

*Dokumen ini adalah PRD turunan proposal HepaTwin Rev 2 dan wajib disinkronkan ulang setiap kali proposal direvisi (mis. setelah sosialisasi resmi GEMASTIK 20 Juli 2026 mengonfirmasi ketentuan lomba).*
