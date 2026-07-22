# DATA_PROVENANCE.md — Buku Besar Asal-Usul Data

**Tujuan file ini:** mencatat **dari mana** setiap data/angka/parameter di sistem
berasal, supaya tidak pernah tertukar antara:

- 🟢 **Sumber sah** — dataset publik yang PRD perintahkan pakai, atau angka yang
  sudah ada di PRD/dokumen arsitektur.
- 🟡 **Engineer-sourced (sementara)** — data yang ditambahkan engineer dari
  internet/literatur untuk melepas kebuntuan, **BELUM** divalidasi domain-expert.
  Wajib ditandai di kode + response API, bukan hanya di file ini.
- 🔴 **Butuh Farmasi (masih kosong)** — sengaja dikosongkan, digembok
  `assert_ready()` / `validated_library()` sampai ada ACC tertulis.

**Konteks tim (2026-07-22):** tim belum memiliki anggota Farmasi. Untuk menjaga
proyek tetap berjalan, pekerjaan diprioritaskan ke jalur yang **tidak** menuntut
validasi Farmasi (Mesin B: dataset publik + model AI). Item yang menuntut
validasi ilmiah (Mesin A: konstanta PK/PD, nomogram, nama gugus) tetap digembok,
menunggu dosen pembimbing / kontak Fakultas Farmasi (PRD §12, §13 #1–2).

---

## 1. Dataset (Mesin B) — 🟢 SAH, bukan data karangan

Pemakaian dataset ini **diperintahkan** PRD §7, §8.4, §13 #3. Mengunduhnya dari
internet BUKAN "mengarang data Farmasi" — peran Farmasi di sini hanya verifikasi
lisensi (dicatat di `NOTICE.md`), bukan validasi angka.

| Data | Sumber | Status | Dipakai di |
|---|---|---|---|
| DILIrank **v2.0** (training) | FDA LTKB, Olubamiwa et al., *Drug Discovery Today* 2025;30(11):104485 | ✅ ditempatkan 2026-07-22 | `ml/data/raw/dilirank.csv` (1.336 baris: nama + label) |
| Xu et al. 2015 (external test) | Xu, Y. et al. "Deep learning for drug-induced liver injury." *J. Chem. Inf. Model.* 55(10):2085-2093 (2015) — ditarik via TDC (`tdc.single_pred.Tox(name='DILI')`), diekspor jadi CSV polos | ✅ ditempatkan 2026-07-22 | `ml/data/raw/xu2015.csv` (475 baris: smiles + label) |
| SMILES hasil resolusi nama (DILIrank) | PubChem PUG-REST (layanan publik) | 🔄 sedang dijalankan | `ml/data/interim/dilirank_smiles.csv` |

> Deduplikasi WAJIB pakai blok-1 InChIKey (bukan SMILES string). Skrip lama
> `data_preparation/deduplicate_smiles.py` memakai metode yang SALAH (canonical
> SMILES + stereo) dan **dibongkar-ganti** di `ml/scripts/04_dedup_split.py`.

### 1.1 Keputusan: DILIrank v2.0 (bukan v1) — `[DEVIASI]` diselesaikan 2026-07-22

PRD §7/§8.4/§15 menyebut DILIrank v1 (Chen et al. 2016, 1.036 obat). File yang
tersedia untuk tim adalah **v2.0** (1.336 obat: +300 obat baru 2010–2021, 49
direklasifikasi ulang; Olubamiwa et al. 2025). Ini persis item keputusan
tertunda #4 di dokumen Arsitektur Bagian I.

**Keputusan:** adopsi v2.0. **Alasan:** data lebih banyak & lebih mutakhir;
tim tidak memiliki akses mudah ke arsip v1 yang sudah digantikan FDA.

**Tindak lanjut yang BELUM dikerjakan** (bukan keputusan agent, perlu sesi
dokumentasi terpisah): PRD §7, §8.4, §15 idealnya disinkronkan menyebut v2.0 +
sitasi Olubamiwa et al. 2025, dan reklasifikasi 49 obat bisa dipakai sebagai
bahan diskusi "ketidakstabilan label DILI" di laporan akhir (per catatan
Arsitektur Bagian I #4).

### 1.2 Catatan: Xu et al. 2015 & keterkaitan historis NCTR

Deskripsi resmi TDC menyebut dataset Xu et al. 2015 "aggregated from U.S. FDA's
National Center for Toxicological Research". **Ini BUKAN pelanggaran AGENTS.md
§3.8** — larangan itu soal memakai NCTR **mentah** sebagai dataset (sirkular
dengan DILIrank yang historisnya juga dari NCTR). Xu et al. 2015 adalah dataset
tersendiri, dikurasi grup riset berbeda (bukan FDA), persis yang PRD §8.4
sanksi sebagai external test. Justru keterkaitan historis inilah alasan PRD
mewajibkan dedup InChIKey blok-1 (`04_dedup_split.py`) — sudah diantisipasi
dokumen Arsitektur §D.7 ("DILIrank dan Xu et al. sama-sama bersumber dari pool
obat yang beririsan").

TDC juga merekomendasikan **scaffold split + AUROC** untuk dataset ini — cocok
dengan desain `04_dedup_split.py` yang sudah dibangun independen dari TDC.

**Soal PyTDC:** dipakai SEKALI (versi ringan 0.4.1, terverifikasi tanpa
tiledbsoma/cellxgene-census yang membuat versi terbaru gagal build di Windows)
untuk menarik data lalu diekspor ke CSV polos. TIDAK menjadi dependensi
permanen — tidak masuk `requirements-dev.txt`, pipeline kita berjalan di atas
RDKit+pandas murni.

---

## 2. Konstanta ilmiah (Mesin A) — status per item

| Parameter | Nilai sekarang | Status | Catatan |
|---|---|---|---|
| F_ORAL, CL, V1, KA, KE (absorpsi) | terisi | 🟢 SAH | Sudah dari Morse et al. 2022, PRD §8.1 — tidak perlu Farmasi |
| k_in, k_elim, k_meta, k_gsh, gsh_initial, theta_thr | `None` | 🔴 kosong | Digembok `assert_ready()`, PRD §13 #1 |
| Parameter peluruhan nomogram 150/200 | `None` | 🔴 kosong | Digembok, PRD §13 #1 |
| Bentuk persamaan GSH (state ke-3 ODE) | belum didefinisikan | 🔴 kosong | Item validasi Farmasi |
| Nama farmakologis 9 gugus SMARTS | ada di `SMARTS_LIBRARY` | 🔴 belum tampil | `SMARTS_VALIDATED_BY_PHARMACY` kosong; nama tidak keluar ke user |

**Keputusan (2026-07-22):** konstanta 🔴 di atas **TIDAK diisi dari internet**,
walau dengan catatan. Alasan: nilai ini memberi makan simulasi deterministik yang
tampil otoritatif ke mahasiswa farmasi, dan catatan di file MD tidak ikut menempel
ke angkanya saat sampai ke UI (AGENTS.md §3.1, §10). Bila nanti benar-benar buntu,
jalur "provisional constants" harus: (a) bersumber dari primary source yang sudah
disitir PRD §15, (b) ditandai `validated_by_pharmacy=False` + `source` di **kode
dan response API**, (c) di belakang flag dev, tidak pernah aktif di demo/produksi.
Itu keputusan sadar terpisah, dicatat di sini bila/ketika diambil.

---

## 3. Log penambahan engineer-sourced (🟡)

Setiap kali engineer menambah data/angka dari luar PRD untuk melepas kebuntuan,
catat di tabel ini: tanggal, apa, sumber, di mana ditandai di kode.

| Tanggal | Item | Sumber | Ditandai di kode/API sebagai | Alasan |
|---|---|---|---|---|
| — | (belum ada) | — | — | — |

---

*Diperbarui setiap ada perubahan asal-usul data. Dibaca bersama `NOTICE.md`
(lisensi) dan `docs/AUDIT_TASKS.md` (status perbaikan).*
