# F9 -- Ringkasan Jury Challenge (D7 & D9)

Jawaban jujur, siap-pakai, untuk pertanyaan yang kemungkinan diajukan juri GEMASTIK terkait branch `fusion`.

---

### "Kenapa ambang warna (0.30/0.70) diubah dari PRD?"

Kalibrator produksi (Platt scaling) mengunci rentang keluaran `dili_score` ke sekitar [0.43, 0.77] --
angka 0.30 dan 0.70 di PRD berasal dari asumsi desain awal SEBELUM kalibrasi final ditentukan (C7).
Kami TIDAK mengubah kalibrasi (keputusan Ketua Tim, model tetap dipakai apa adanya) -- sebagai gantinya
kami menurunkan ulang ambang warna dari distribusi `dili_score` NYATA atas seluruh 1.231 senyawa katalog
(bukan test set -- menghindari kebocoran data). Metode yang dipakai (pemetaan-balik lewat fungsi
kalibrator yang sama) mempertahankan MAKSUD desain PRD asli: proporsi relatif skor terhadap ambang lama,
bukan angka arbitrer baru.

### "Apakah mengubah usia/berat pasien benar-benar mengubah hasil?"

**Jujur: tergantung.** `dili_score` (probabilitas AI) murni fungsi struktur molekul (SMILES) -- kovariat
pasien TIDAK memengaruhinya sama sekali, terverifikasi lewat 1.231 forward pass yang tidak menerima
parameter pasien. Personalisasi HANYA lewat jalur farmakokinetik (PBPK -> `exposure_category`). Namun
kami menemukan (lewat pengukuran, bukan dugaan) bahwa untuk kombinasi dosis/pasien REALISTIS, sistem
PBPK linear kami membuat rasio Cmax/AUC hampir selalu di atas ambang "HIGH" -- artinya pada rentang
dosis wajar, mengubah usia/berat pasien SERINGKALI tidak mengubah `exposure_category` (karena sudah
HIGH sejak awal). Ini keterbatasan nyata yang belum terselesaikan, didokumentasikan eksplisit di
`reports/F9_limitations_fusion.md`, bukan disembunyikan. Mengubah DOSIS pada rentang ekstrem (mis.
overdosis vs dosis sangat kecil) tetap mengubah `dose_per_kg`, yang bisa mendominasi keputusan HIGH.

### "Bagaimana memastikan lapisan fusinya bukan machine learning?"

`fusion_service.py` adalah lookup dictionary 9-sel eksplisit (`(AiRiskBand, ExposureRiskLevel) ->
(risk_level, visual_color, blinking_speed)`) -- tidak ada pembobotan yang dipelajari, tidak ada
training, tidak ada parameter yang di-fit dari data (ambangnya diturunkan MANUAL dari analisis
distribusi, bukan dioptimasi lewat gradient descent atau algoritma pembelajaran apa pun). Dibuktikan
otomatis lewat test (`test_fusion_service_has_no_ml_imports`, parsing AST) yang memverifikasi tidak ada
`import torch`/`sklearn`/`tensorflow`/dst di file tersebut -- gagal build/CI bila ada yang menambahkannya
di masa depan.

### "Apakah warna HIJAU benar-benar bisa muncul untuk pengguna akhir?"

**Jujur: sebagian.** Kami membuktikan SECARA STRUKTURAL bahwa matriks fusi menghasilkan HIJAU untuk
kombinasi (AI_LOW, LOW_EXPOSURE) -- termasuk untuk senyawa ASLI dengan skor AI terendah di katalog
(Calcitonin salmon). TAPI kami juga menemukan (dan mengukur, bukan menduga) bahwa `LOW_EXPOSURE` sendiri
praktis tidak terjangkau untuk kovariat pasien realistis manapun yang kami uji (0 dari 20.250 kombinasi),
karena akar masalah TERPISAH di `exposure_evaluator.py` (di luar cakupan yang boleh kami ubah tanpa
keputusan Farmasi). Jadi: **HIJAU ada di dalam sistem dan bisa dipicu, tapi belum terbukti muncul lewat
input pasien apa pun yang sudah kami coba** -- ini pekerjaan lanjutan yang jelas kami tandai untuk tim,
bukan klaim selesai yang kami sembunyikan kegagalannya.

### "Kenapa ada bug di `affected_segments` yang tidak pernah ditemukan sebelumnya?"

Kode lama memisah string segmen dengan koma, padahal seluruh data produksi memakai titik-koma. Tidak
tertangkap sebelumnya karena test unit memakai data mock buatan sendiri (memakai koma), bukan data asli
dari database -- test hanya memeriksa field ITU ADA, bukan ISINYA benar. Ini pengingat metodologis:
test yang memakai data sintetis bisa melewatkan bug format data nyata. Kami memperbaikinya begitu
ditemukan (F4) dan memperbarui seluruh fixture test agar mencerminkan format data produksi sesungguhnya.

### "Apa yang BELUM selesai di branch ini?"

Lihat `reports/F9_limitations_fusion.md` -- ringkasnya: (1) `LOW_EXPOSURE` praktis tidak terjangkau
(perlu revisi Farmasi, gerbang K3, sekarang mendesak); (2) satu anomali latensi SHAP ~9.5 detik belum
tereproduksi/dijelaskan; (3) enam gerbang keputusan (K1-K6) masih menunggu ratifikasi manusia, bukan
diputuskan sepihak oleh agen.
