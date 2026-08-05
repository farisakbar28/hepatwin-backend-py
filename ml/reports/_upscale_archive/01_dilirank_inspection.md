# 01 — Inspeksi DILIrank 2.0

**Sumber:** `ml/data/raw/Drug Induced Liver Injury Rank (DILIrank 2.0) Dataset  FDA.csv` (disediakan manual oleh pengguna, 2026-07-31)
**Metode inspeksi:** pembacaan langsung file + pencacahan baris per kategori (belum lewat pandas — lihat catatan lingkungan di bawah).

## Skema kolom (terverifikasi cocok dengan UPSCALE.md §3.1)

```
LTKBID, CompoundName, SeverityClass, LabelSection, vDILI-Concern, Comment
```

Baris 1 adalah judul dataset (`Drug Induced Liver Injury Rank (DILIrank) Dataset Ver 2.0 | FDA`), baris 2 adalah header kolom asli, data mulai baris 3.

## Distribusi kelas (`vDILI-Concern`, case-insensitive)

| Kelas | Jumlah | Ekspektasi UPSCALE.md §3.1 |
|---|---|---|
| vMost-DILI-concern | 217 | 217 ✅ |
| vLess-DILI-concern | 351 | 351 ✅ |
| vNo-DILI-concern | 414 | 414 ✅ |
| Ambiguous-DILI-concern | 354 | 354 ✅ |
| **Total** | **1.336** | **1.336** ✅ |

Cocok persis dengan angka yang didokumentasikan — dataset terverifikasi asli DILIrank 2.0, bukan versi lain/palsu.

**Catatan casing:** kolom `vDILI-Concern` tidak konsisten kapitalisasinya di file sumber (ditemukan varian `vMOST-DILI-concern` dan `vMost-DILI-concern` untuk kelas yang sama). Pipeline harmonisasi (TU.3) **wajib** membandingkan case-insensitive, jangan exact-match string.

## Temuan untuk gerbang B3 (amox-clav di DILIrank)

Dicari pola `moxicillin` dan `clavulan` (case-insensitive) di seluruh file:

- `Amoxicillin` (tunggal) — 1 baris, `vLess-DILI-concern`
- `clavulan*` (kombinasi apapun) — **0 baris ditemukan**

**Kesimpulan:** DILIrank 2.0 tidak mengandung entri kombinasi amoxicillin-clavulanate sama sekali — hanya amoxicillin tunggal. Artinya gerbang B3 **tidak relevan untuk Arm A** (TU.3/TU.4); pertanyaan itu baru relevan saat Arm B (TU.12), karena LiverTox memang punya monograf terpisah untuk "Amoxicillin-Clavulanate". Ini bukan keputusan yang di-bypass — ini fakta data yang mengeliminasi pertanyaannya untuk tahap ini.

## Catatan lingkungan (bukan bagian dari acceptance criteria TU.1, dicatat untuk transparansi)

`.venv/` proyek ini rusak sebagian: `pandas/__init__.py`, `pip/__init__.py`, `pip/__main__.py`, dan isi `_distutils_hack/` hilang (hanya folder `__pycache__` yang tersisa), sementara `torch/__init__.py` dan `setuptools/__init__.py` masih utuh. Ini korupsi yang sudah ada sebelum sesi ini (bukan hasil TU.0). Inspeksi di atas dilakukan lewat pembacaan file langsung karena `pandas.read_csv` tidak bisa dipanggil. TU.2 dan seterusnya butuh environment yang berfungsi (rdkit + pubchempy + jaringan) sebelum bisa dieksekusi sungguhan.
