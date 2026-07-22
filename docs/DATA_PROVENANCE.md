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
| DILIrank (training) | FDA LTKB (Chen et al., 2016, PRD §15) | ⬜ belum diunduh | `ml/data/raw/dilirank.xlsx` |
| Xu et al. 2015 (external test) | kurasi Peking University (PRD §15) | ⬜ belum diunduh | `ml/data/raw/xu2015.csv` |
| SMILES hasil resolusi nama | PubChem PUG-REST (layanan publik) | ⬜ belum dijalankan | `ml/data/interim/` |

> Deduplikasi WAJIB pakai blok-1 InChIKey (bukan SMILES string). Skrip lama
> `data_preparation/deduplicate_smiles.py` memakai metode yang SALAH (canonical
> SMILES + stereo) dan akan **dibongkar-ganti** di `ml/scripts/04_dedup_split.py`.

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
