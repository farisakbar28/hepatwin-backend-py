# Prompt Pencarian Dataset (untuk sesi Claude/LLM lain)

Salin-tempel blok di bawah ke sesi Claude baru (idealnya dengan web search aktif)
untuk membantu menemukan dua dataset yang dibutuhkan pipeline HepaTwin. Setelah
dapat jawabannya, taruh file dataset di `ml/data/raw/` dan jalankan pipeline
(lihat `ml/README.md`). Catat sumber + lisensi di `NOTICE.md` dan
`docs/DATA_PROVENANCE.md`.

---

Saya sedang membangun model prediksi **Drug-Induced Liver Injury (DILI)** untuk
proyek akademik. Saya butuh bantuan menemukan DUA dataset publik spesifik,
lengkap dengan URL unduhan resmi, lisensi/ketentuan penggunaan, dan deskripsi
format kolomnya. Tolong verifikasi lewat pencarian web, jangan menebak URL.

**Dataset 1 — DILIrank (untuk data latih)**
- Sumber: FDA Liver Toxicity Knowledge Base (LTKB), publikasi Chen et al. (2016).
- Isi: ~1.036 obat (versi asli) dengan klasifikasi tingkat kekhawatiran DILI
  (mis. vMost-DILI-Concern, vLess-DILI-Concern, vNo-DILI-Concern, Ambiguous).
- Catatan: dataset umumnya berisi NAMA obat, bukan SMILES. Itu tidak masalah —
  saya punya langkah resolusi nama→SMILES via PubChem.
- Ada juga "DILIrank 2.0" (~1.336 obat, Olubamiwa et al. 2025). Sebutkan bila
  tersedia, tapi tandai jelas ini versi berbeda (keputusan versi ada di tim saya).

**Dataset 2 — Xu et al. (2015) (untuk external test set independen)**
- Sumber: paper Xu et al. 2015 tentang prediksi DILI (deep learning), dataset di
  bagian supplementary. ~344–475 senyawa dengan label DILI biner.
- Tujuan: validasi eksternal yang benar-benar independen dari data latih.

**Yang WAJIB dihindari:**
- Dataset **NCTR** — jangan direkomendasikan. Ini sumber historis penyusun
  DILIrank, memakainya sebagai test menimbulkan kebocoran data (data leakage).

**Untuk tiap dataset, tolong berikan:**
1. URL unduhan resmi/langsung (halaman FDA LTKB, supplementary jurnal, atau repo
   resmi). Sertakan tanggal Anda memverifikasinya.
2. Lisensi / ketentuan penggunaan (boleh dipakai untuk riset akademik?).
3. Format file (xlsx/csv) dan nama kolom penting (kolom nama/SMILES + kolom label).
4. Cara sitasi yang benar (penulis, tahun, judul, DOI/jurnal).
5. Bila ada beberapa versi/mirror, sebutkan mana yang paling otoritatif.

**Konteks teknis (biar rekomendasinya pas):**
- Saya akan meng-standardisasi SMILES via RDKit dan men-deduplikasi Xu et al.
  terhadap DILIrank memakai blok-1 InChIKey (jadi sedikit tumpang tindih wajar).
- Saya hanya butuh: identitas senyawa (nama atau SMILES) + label DILI. Kolom lain
  boleh ada, akan saya abaikan.
- Prioritas: sumber publik yang stabil dan lisensinya jelas untuk penggunaan riset.
