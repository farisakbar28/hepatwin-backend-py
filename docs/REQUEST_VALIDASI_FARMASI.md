# Permintaan Validasi Farmasi — HepaTwin

**Status:** Draft, disusun agent (T0.8), menunggu dikirim oleh Ketua Tim ke
anggota/kontak Farmasi (dosen pembimbing / Fakultas Farmasi — PRD §12).
**Dasar:** PRD §13 item #1, #2 · PRD §12.

**Konteks singkat:** HepaTwin punya dua mesin komputasi. **Mesin B** (skor
risiko DILI dari struktur kimia) sudah selesai dan berjalan dengan data publik
— tidak butuh Farmasi. **Mesin A** (simulasi PK/PD parasetamol) dan **nama
gugus kimia** di panel penjelasan (explainability) sengaja dikosongkan dan
digembok kode, menunggu 5 item di bawah ini. Sistem akan menolak berjalan
(gagal jelas, bukan diam-diam salah) sampai validasi ini diterima.

**Mohon dikirim sekaligus** (bukan bertahap), supaya tidak ada bolak-balik.

---

## 1. Konstanta kinetika hati/NAPQI/GSH (KRITIS)

Dibutuhkan nilai + satuan + sitasi sumber primer untuk tiap konstanta berikut
(dipakai dalam sistem persamaan diferensial simulasi kerusakan hati akibat
parasetamol, PRD §8.1 langkah 2–3):

| Konstanta | Arti | Satuan (perkiraan, mohon dikoreksi bila salah) |
|---|---|---|
| `k_in` | Laju masuk parasetamol dari plasma ke kompartemen hati | 1/jam |
| `k_elim` | Laju eliminasi parasetamol dari kompartemen hati | 1/jam |
| `k_meta` | Laju metabolisme parasetamol di hati → NAPQI (via CYP2E1) | 1/jam |
| `k_gsh` | Laju reaksi detoksifikasi NAPQI oleh glutathione (GSH) | L/(mmol·jam) |
| `gsh_initial` | Konsentrasi awal GSH hati sebelum paparan | mmol |
| `theta_thr` | Ambang rasio [NAPQI]/[GSH]₀ yang memicu visual nekrosis sentrilobuler | rasio (tanpa satuan) |

**Referensi yang sudah disebut PRD §15 sebagai kandidat sumber** (mohon
konfirmasi/koreksi, atau berikan sumber primer yang lebih tepat):
Chiew et al. (2023); Du et al. (2024).

## 2. Bentuk eksplisit persamaan GSH

PRD §8.1 langkah 3 menuliskan produksi NAPQI:
```
d[NAPQI]/dt = k_meta · Cliver(t) − k_GSH · [GSH](t) · [NAPQI](t)
```
tetapi **tidak** menuliskan eksplisit persamaan untuk `d[GSH]/dt` (laju
perubahan GSH itu sendiri) — dibutuhkan sebagai state ketiga sistem ODE.

**Pertanyaan untuk Farmasi:** apakah bentuk berikut sudah benar secara
farmakologis (asumsi sintesis GSH de novo diabaikan selama krisis akut)?
```
d[GSH]/dt = − k_GSH · [GSH](t) · [NAPQI](t)
```
Atau apakah perlu ditambah suku sintesis/regenerasi GSH? Mohon konfirmasi atau
berikan bentuk yang benar + sitasi.

## 3. Parameter kalibrasi nomogram Rumack-Matthew (garis 150 & 200)

Sistem butuh parameter peluruhan garis referensi klinis nomogram (untuk
membandingkan kurva Cplasma(t) hasil simulasi terhadap standar klinis,
PRD §8.1 validasi silang). Dokumen arsitektur mengusulkan bentuk peluruhan
`anchor × 2^(-(t-4)/4)` (paruh waktu referensi 4 jam) tapi **ini belum
diverifikasi ke sumber primer** — jangan dianggap final.

**Mohon:** parameter kalibrasi resmi + sitasi ke sumber primer (Rumack &
Matthew 1975; revisi Rumack et al. 1981; atau konsensus terkini seperti Dart
et al. 2023 yang sudah disebut PRD §15).

## 4. Nama farmakologis 9 gugus kimia (SMARTS)

Sistem punya 9 pola struktur kimia yang dipakai sebagai fitur model (dan
tetap dipakai untuk prediksi apa pun keputusannya). Yang dibutuhkan adalah
**ACC (persetujuan) tertulis per item** bahwa nama farmakologisnya benar,
supaya boleh ditampilkan ke pengguna di panel penjelasan hasil prediksi:

| # | Nama internal saat ini | Pola SMARTS | ACC nama ini benar? (Y/N + koreksi bila perlu) |
|---|---|---|---|
| 1 | Phenol group | `c1ccccc1O` | |
| 2 | Acetamide / Amide group | `C(=O)N` | |
| 3 | Carboxylic acid group | `C(=O)O` | |
| 4 | Sulfonamide group | `S(=O)(=O)N` | |
| 5 | Beta-lactam ring | `C1C(=O)NC1` | |
| 6 | Primary amine | `[NX3;H2,H3]` | |
| 7 | Nitro group | `N(=O)=O` | |
| 8 | Thiazole ring | `c1scnc1` | |
| 9 | Piperazine | `C1CNCCN1` | |

**Catatan penting untuk Farmasi:** ini nama gugus kimia generik (bukan spesifik
ke satu obat) — dipakai lintas senyawa apa pun yang diinput pengguna di Mode
Triase. Mohon dicek apakah nama di kolom 2 sudah istilah farmakologis yang
tepat untuk pola SMARTS di kolom 3, atau perlu diganti istilah lain.

## 5. Pola histologis kolestatik Amoxicillin-Clavulanate

PRD §8.2 menyebutkan pola kolestatik idiosinkratik untuk Amoxicillin-Clavulanate,
dengan visual di area portal/periportal + struktur saluran empedu. **Mohon
validasi/verifikasi:** deskripsi pola histologis yang benar secara farmakologis
untuk mekanisme DILI kolestatik senyawa ini, supaya visualisasi 3D (dikerjakan
tim frontend) akurat secara medis.

---

## Yang TIDAK perlu Farmasi (agar tidak ada kebingungan)

- Model skor risiko DILI (Mesin B) — sudah terlatih & berjalan dengan data
  publik (DILIrank, Xu et al. 2015), tidak menunggu apa pun dari Farmasi.
- Parameter absorpsi oral parasetamol (F, CL, V1, ka, ke) — sudah dari Morse
  et al. (2022), sudah terisi di kode.

## Format balasan yang memudahkan

Boleh balas per item di atas (tidak harus dokumen formal), yang penting per
konstanta/nama ada: **nilai/keputusan + satuan (bila relevan) + sumber
sitasi**. Contoh:
```
k_in = 0.8 /jam (sumber: [nama, tahun, judul/DOI])
```

---

**Setelah balasan diterima:** tim BE akan mengisi nilai ke
`app/services/pkpd_engine.py` (`PD_CONSTANTS`) dan
`app/chem/smarts_library.py` (`SMARTS_VALIDATED_BY_PHARMACY`), dengan sitasi
dicantumkan di kode. Sistem otomatis lulus gerbang begitu semua item lengkap.

**Rekomendasi tenggat (isi manual):** ______________________
**Eskalasi bila lewat tenggat:** dosen pembimbing / kontak Fakultas Farmasi
(PRD §12).
