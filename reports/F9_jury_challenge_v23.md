# F9 v2.3 -- Ringkasan Jury Challenge (Revisi D7 & D9 Pasca-Upgrade Mesin A)

Jawaban jujur, siap-pakai, untuk pertanyaan yang kemungkinan diajukan juri GEMASTIK terkait upgrade
Mesin A v2.3 dan revisi branch `fusion`.

---

### "Kenapa kategori paparan pakai kuantil internal, bukan ambang klinis?"

Karena ambang klinis yang bermakna untuk konsentrasi obat di hati bersifat **spesifik per-obat**, bukan
universal -- literatur PBPK yang kami kutip sendiri (Olaparib, Rilzabrutinib) menunjukkan ini eksplisit.
Memaksakan satu ambang klinis universal ke 1.231 senyawa yang sangat beragam akan jadi klaim yang tidak
bisa kami pertanggungjawabkan. Sebagai gantinya, kami memakai kuantil (p33/p66) dari distribusi
`exposure_index` atas sweep kalibrasi internal 1.728.324 sampel -- ini murni alat **triase relatif**
("obat ini menghasilkan paparan komputasional lebih tinggi dari 66% skenario lain yang kami uji"), bukan
klaim "aman secara klinis di bawah X mg/L". Field `exposure_category_source` di response secara eksplisit
berisi `"INTERNAL_DISTRIBUTIONAL_CALIBRATION"` -- kami tidak menyembunyikan sifat ini.

### "Apakah mengubah dosis/usia benar-benar mengubah hasil? (sekarang bisa dijawab dgn bukti R2)"

**Ya, sekarang terbukti dan terukur.** Versi sebelumnya (v2.1) punya bug: rasio Cmax/AUC yang dipakai
untuk kategori paparan matematis TIDAK bergantung dosis (kami temukan dan laporkan sendiri). Setelah
diperbaiki (v2.3, `exposure_index` berbasis magnitude bukan rasio), kami membuktikan lewat pengukuran
langsung: pada profil pasien tetap, menaikkan dosis dari 50mg ke 4000mg mengubah `exposure_index` dari
4.56 ke 13.08 (naik monoton) dan kategori dari LOW ke HIGH. Sweep 20.250 kombinasi pasien+dosis
menunjukkan 43.4% mencapai LOW, 34.4% MODERATE, 22.2% HIGH -- ketiganya benar-benar terpakai, bukan satu
kategori yang mendominasi. Usia dan BMI juga berpengaruh lewat parameter alometrik (Q_L, Cl_metabolism,
Kp_R) yang memengaruhi Cmax/AUC secara fisiologis, bukan lewat pergeseran ambang ad-hoc seperti versi
lama.

**Batasnya tetap ada:** `dili_score` (probabilitas AI) sendiri MURNI fungsi struktur molekul -- kovariat
pasien tidak pernah mengubahnya. Personalisasi HANYA lewat jalur PBPK/paparan. Ini kami nyatakan
eksplisit, bukan disembunyikan.

### "Kenapa laporan lama bilang hijau mustahil? Apa itu bug yang disembunyikan?"

Bukan disembunyikan -- justru sebaliknya, laporan itu KAMI TULIS SENDIRI dan kami tunjukkan sebagai jejak
audit. Riwayatnya: kami menemukan bug (`cmax_auc_ratio` dose-independent) lewat pengujian sistematis kami
sendiri (sweep 20.250 kombinasi, dilaporkan di `reports/_v21_archive/F2_exposure_reachability_finding.md`),
bukan ditemukan pihak luar. Kami laporkan apa adanya ke Ketua Tim, termasuk dampaknya ke DoD proyek. Ketua
Tim kemudian meng-upgrade mesin PBPK (v2.3) untuk mengatasi akar masalahnya. Kami uji ulang secara
independen (R2/R3, bukan asumsi) dan buktikan masalahnya benar-benar teratasi. Laporan lama TIDAK kami
hapus -- diarsipkan di `reports/_v21_archive/` sebagai bukti proses temuan-ke-perbaikan yang transparan.
**Riwayat kegagalan yang jujur dan terbukti diperbaiki lebih kredibel daripada klaim sempurna sejak awal.**

### "Bagaimana memastikan lapisan fusinya bukan machine learning?"

Sama seperti sebelumnya -- `fusion_service.py` adalah lookup dictionary 9-sel eksplisit, tidak berubah
oleh upgrade Mesin A sama sekali (diverifikasi `git diff` kosong). Dibuktikan otomatis lewat test
(`test_fusion_service_has_no_ml_imports`, parsing AST) yang memverifikasi tidak ada `import torch`/
`sklearn`/dst di file tersebut.

### "Kenapa BMI>=30 tidak otomatis membuat hasil jadi kuning/merah, padahal PRD menyebutnya?"

PRD v2.3 sendiri punya ketegangan internal di sini: teksnya bilang `metabolic_risk_flag` "hanya flag
naratif", tapi tabel matriksnya menuliskannya sebagai kondisi yang mengubah warna. Kami MENGUKUR dulu
dampaknya sebelum memutuskan (R4): mengaktifkan aturan itu akan membuat 44% dari seluruh kombinasi
pasien+dosis yang kami uji KEHILANGAN kemungkinan hijau secara permanen, apa pun obat dan dosisnya --
pola yang sama persis dengan bug yang baru saja kami perbaiki di siklus sebelumnya. Karena PRD ambigu dan
dampaknya besar, kami memilih jalur aman: tampilkan `metabolic_risk_flag` sebagai catatan informatif di
response (pasien/dokter tetap tahu ada risiko metabolik), TANPA otomatis mengubah warna, sampai Ketua Tim
dan Farmasi memutuskan definisi final. Ini keputusan yang bisa dijelaskan dengan angka, bukan tebakan.

### "Apa yang BELUM selesai di revisi ini?"

Lihat `reports/F9_limitations_fusion_v23.md` -- ringkasnya: (1) dua jalur eskalasi PRD masih menunggu
definisi final Farmasi (gerbang G1/G2); (2) `mapping_confidence` masih proksi turunan, kolom kurasi asli
belum ada di database; (3) kalibrasi p33/p66 belum diuji dengan variasi XLogP penuh; (4) anomali latensi
SHAP dari siklus sebelumnya belum terdiagnosis (tidak terkait upgrade Mesin A); (5) enam gerbang keputusan
manusia (G1-G5, K1-K6) masih menunggu ratifikasi eksplisit, bukan diputuskan sepihak oleh kami.
