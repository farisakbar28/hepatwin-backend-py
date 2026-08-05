# C8_shap.md -- Explainability SHAP Tingkat Atom & Gugus

## Metode

**Tingkat gugus (SMARTS, 9 pola):** nilai Shapley EKSAK (bukan approksimasi KernelExplainer) atas 9 fitur biner SMARTS -- diwarisi `upscale` TU.11 apa adanya, sudah lebih presisi dari yang diminta EXECUTION_PLAN_FIX_MODEL.md C8 langkah 1(a) (yang menyebut KernelExplainer sebagai opsi, bukan keharusan).

**Tingkat atom (BARU):** occlusion/masking per-atom -- fitur node tiap atom dinolkan satu per satu, diukur delta probabilitas vs molekul utuh. Dipilih (bukan GNNExplainer/CaptumExplainer) karena: (1) deterministik, tidak ada variansi sampling; (2) satu forward pass ter-batch untuk SEMUA atom sekaligus (`Batch.from_data_list`), memenuhi anggaran latensi C8 tanpa kompleksitas tambahan; (3) interpretasi langsung ("berapa turun skor kalau atom ini dihapus") mudah divalidasi manual untuk uji kelayakan kimiawi di bawah.

🔴 **Field `method` = `"masking_attribution"`, BUKAN `"SHAP"`** -- ini secara jujur BUKAN nilai Shapley (tidak dirata-ratakan atas seluruh kemungkinan koalisi subset atom, yang infeasible untuk molekul besar). Aturan kejujuran EXECUTION_PLAN_FIX_MODEL.md C8 dipatuhi eksplisit di kode (`explain.py`) dan di laporan ini.

## Benchmark latensi

Diukur pada **50 molekul acak** (seed=42) dari `features_all.parquet` (C2), cache dipaksa miss (setiap panggilan dijamin komputasi ulang, bukan cache hit) supaya yang diukur murni waktu komputasi:

| Persentil | Waktu |
|---|---|
| p50 | 1064.8 ms |
| p95 | 1376.0 ms |
| max | 3845.8 ms |
| mean | 1161.1 ms |

**Ambang C8: p95 < 2000 ms.** Hasil aktual p95=1376.0 ms -> **LULUS**, jauh di bawah ambang PRD UC-02 (anggaran total AI+PBPK+fusi <=5 detik, explainability dijatah <2 detik).

Catatan: benchmark ini TANPA cache (worst-case setiap request unik). Karena database tertutup (1.231 senyawa), cache per-InChIKey pada deployment nyata akan membuat mayoritas request setelah senyawa pertama kali diminta jadi instan (cache hit) -- lihat EXECUTION_PLAN_FIX_MODEL.md C8 langkah 2 soal precompute penuh sebagai opsi lanjutan bila diperlukan.

## Uji kelayakan kimiawi

### Parasetamol (acetaminophen)

SMILES standar: `CC(=O)Nc1ccc(O)cc1`

| Gugus (SMARTS) | Kontribusi | Atom indeks |
|---|---|---|
| Acetamide / Amide group | +0.0064 | [1, 2, 3] |
| Phenol group | -0.0063 | [7, 8] |

**Ekspektasi PRD (mekanisme NAPQI):** gugus amida/asetamida seharusnya muncul sebagai kontributor. **Hasil aktual:** gugus "Acetamide / Amide group" TERDETEKSI pada parasetamol (diverifikasi lewat pencocokan SMARTS langsung, bukan asumsi).

### Ibuprofen

SMILES standar: `CC(C)Cc1ccc(C(C)C(=O)O)cc1`

| Gugus (SMARTS) | Kontribusi | Atom indeks |
|---|---|---|
| Carboxylic acid group | +0.0008 | [10, 11, 12] |

**Ekspektasi PRD:** profil risiko rendah, tidak boleh menyoroti toxicophore berbahaya secara kuat. **Hasil aktual:** kontribusi gugus terbesar (nilai absolut) = 0.0008 (dibanding parasetamol 0.0064 bila ada).

## Keterbatasan (dicatat jujur, bukan disembunyikan)

- Metode atom-level (`masking_attribution`) adalah ablasi 1-fitur, BUKAN Shapley sebenarnya -- tidak menangkap efek interaksi antar-atom (mis. dua atom yang hanya berbahaya bersama-sama tidak akan terlihat lewat masking satu-per-satu).
- Occlusion menolkan fitur NODE, tapi topologi edge (siapa terhubung ke siapa) tetap ada -- pesan GAT masih bisa "melihat" keberadaan atom tsb lewat tetangganya, jadi delta yang terukur adalah batas bawah kontribusi sebenarnya, bukan isolasi sempurna.
- 🔴 **Gerbang G4** [KEPUTUSAN AI -- PENDING REVIEW FARMASI]: nama & interpretasi klinis 9 pola SMARTS di atas (mis. "Nitro group", "Beta-lactam ring") diwarisi `upscale` apa adanya, BELUM divalidasi Farmasi -- jangan ditampilkan ke pengguna akhir sebagai fakta terkurasi sebelum ACC tertulis diterima.