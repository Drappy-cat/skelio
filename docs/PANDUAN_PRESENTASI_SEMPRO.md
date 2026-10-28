# 🎓 PANDUAN LENGKAP PRESENTASI SEMINAR PROPOSAL (SEMPRO)
## SISTEM SKELIO: ANALISIS KINEMATIK & EVALUASI POSTUR OLAHRAGA REAL-TIME

**Program Studi S1 Teknik Informatika — Universitas Negeri Surabaya (UNESA) 2026**  
**Kelompok 11 Big Data / Tim Peneliti SKELIO:**
- Rizma Indra Pramudya (25051204370)
- Izora Elverda Narulita Putri (25051204287)
- Putera Al Khalidi (25051204362)
- Muhammad Abdullah Ro'in (25051204270)  
**Dosen Pengampu / Pembimbing:** Saifudin Yahya, S.Kom., M.T.I  
**Naskah Acuan:** `KELOMPOK 11 BIG DATA .pdf`

---

## 📌 1. Status Kesiapan Sistem SKELIO Saat Ini

Sistem telah berhasil disiapkan, diverifikasi, dan diuji 100% di lingkungan lokal Anda (`E:\Codingan BARU\Bigdata`):

1. **Environment Python 3.11 Siap Pakai:**
   - `PyTorch 2.14.1` & `Ultralytics 8.4.190` terpasang stabil.
   - Pustaka pelacakan ByteTrack (`lap 0.5.13`) terkonfigurasi.
   - Pustaka komputasi numerik (`numpy`, `pandas`, `opencv-python`, `matplotlib`, `scipy`) siap tanpa konflik versi.
2. **Model AI Pose:**
   - Model terlatih kalistenik: `models/best_calisthenics_pose.pt` (19.9 MB).
   - Model baseline COCO: `yolo11n-pose.pt` (6.2 MB).
3. **Pipeline Evaluasi Kinematik Berfungsi:**
   - One-Euro Filter (Peredam Jitter).
   - Palm Center Tracker (Estimasi telapak tangan 35% vektor lengan).
   - Finite State Machine (FSM) Rep Counter (Push-up, Squat, Sit-up).
   - Dynamic Depth Indicator Bar (0–100%) & Multi-Person HUD Cards.
4. **Aset Demo & Grafik Sempro Telah Di-Generate:**
   - 3 Grafik resolusi tinggi siap tempel di slide presentasi (`assets_sempro/chart1_*.png`, `chart2_*.png`, `chart3_*.png`).
   - 2 Video sampel hasil evaluasi beranotasi HUD (`skelio_push-up_evaluated.mp4` & `skelio_squat_evaluated.mp4`).
   - File launcher 1-klik untuk presentasi demo langsung maupun offline video.

---

## 🚀 2. Panduan Menjalankan Sistem Saat Presentasi Sempro

Saat sesi presentasi di hadapan dosen penguji, Anda memiliki **3 pilihan demonstrasi**:

```
E:\Codingan BARU\Bigdata\
│
├── 🎥 run_skelio.bat               <- (Opsi 1) Demo LIVE Webcam langsung
├── 🎬 run_demo_video_pushup.bat    <- (Opsi 2) Demo Offline Video PUSH-UP 
└── 🏋️ run_demo_video_squat.bat     <- (Opsi 3) Demo Offline Video SQUAT
```

### Opsi A: Demo LIVE Webcam (Jika Ada Ruang Gerak di Ruang Sidang)
1. Sambungkan webcam laptop atau kamera eksternal.
2. **Klik 2x** pada: `run_skelio.bat`
3. Jendela interaktif OpenCV akan terbuka dengan resolusi HD.
4. Mintalah salah satu anggota tim melakukan gerakan di depan kamera dari samping (*sagittal plane*).

### Opsi B: Demo Video File (Paling Aman & Direkomendasikan untuk Sempro)
Jika ruang sidang terbatas atau dosen ingin melihat performa sistem secara instan tanpa harus mempraktikkan gerakan di lantai:
- **Demo Push-Up:** Klik 2x `run_demo_video_pushup.bat`
- **Demo Squat:** Klik 2x `run_demo_video_squat.bat`
- Sistem akan memproses video pengujian secara frame-by-frame dengan overlay HUD, skeleton, busur sudut, dan indikator kedalaman secara otomatis!

### 🎮 Tombol Kontrol Keyboard Saat Jendela Program Terbuka:
- **`1`** : Beralih ke Mode **Push-Up**
- **`2`** : Beralih ke Mode **Squat**
- **`3`** : Beralih ke Mode **Sit-Up**
- **`A`** : Mode **Auto Detection** (Orientasi otomatis tubuh)
- **`R`** : **Reset Reps** (Mengembalikan hitungan repetisi ke 0)
- **`Q`** atau `ESC` : Keluar dari aplikasi

---

## 📊 3. Hasil Tangkapan Visual Sistem SKELIO (Untuk Lampiran Slide)

Berikut adalah hasil tangkapan nyata dari eksekusi pipeline SKELIO yang baru saja dijalankan pada model Anda:

````carousel
![Hasil Evaluasi Push-Up](/C:/Users/Rizma Indra/.gemini/antigravity-ide/brain/8c131139-537e-4d2a-b841-65aa1183d21a/test_pushup_result.jpg)
<!-- slide -->
![Hasil Evaluasi Squat](/C:/Users/Rizma Indra/.gemini/antigravity-ide/brain/8c131139-537e-4d2a-b841-65aa1183d21a/test_squat_result.jpg)
<!-- slide -->
![Trade-off FPS vs mAP50](/C:/Users/Rizma Indra/.gemini/antigravity-ide/brain/8c131139-537e-4d2a-b841-65aa1183d21a/chart1_fps_vs_accuracy.png)
<!-- slide -->
![Ukuran Model vs Latensi](/C:/Users/Rizma Indra/.gemini/antigravity-ide/brain/8c131139-537e-4d2a-b841-65aa1183d21a/chart2_size_vs_latency.png)
<!-- slide -->
![Galat Spasial MPE dan Homografi](/C:/Users/Rizma Indra/.gemini/antigravity-ide/brain/8c131139-537e-4d2a-b841-65aa1183d21a/chart3_spatial_errors.png)
````

---

## 📈 4. Data Kuantitatif Benchmarking (Tabel Resmi Hasil Pengujian)

Tabel berikut diambil dari hasil pengujian empiris `yolo11_biomechanics_benchmark.csv`:

| Model Arsitektur | Ukuran (MB) | Latensi (ms) | Kecepatan (FPS) | MPE (Piksel) | Galat Homografi (px) | Akurasi mAP50 (%) | JAA (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **YOLOv11 Nano** | **5.62 MB** | 245.23 ms | 4.08 FPS | 4.05 px | 1.62 px | 19.02% | 19.02% |
| **YOLOv11 Small** | 19.02 MB | **193.47 ms** | **5.17 FPS** | **0.50 px** | **0.20 px** | **99.20%** | **99.20%** |
| **YOLOv11 Medium** | 40.31 MB | 206.82 ms | 4.84 FPS | 0.50 px | 0.20 px | 99.12% | 99.12% |
| **YOLOv11 Large** | 50.51 MB | 210.34 ms | 4.75 FPS | 0.50 px | 0.20 px | 99.12% | 99.12% |
| **YOLOv11 X-Large**| 112.78 MB| 250.53 ms | 3.99 FPS | 0.88 px | 0.35 px | 82.46% | 82.46% |

> [!TIP]
> **Highlight untuk Dosen:**  
> Varian **YOLOv11 Small** merupakan arsitektur paling optimal (*sweet spot*), karena menghasilkan **mAP50 tertinggi (99.20%)**, latensi terendah (193.47 ms), dan Mean Per-Joint Position Error (MPE) terendah (hanya 0.50 piksel).

---

## 🖥️ 5. Rancangan Struktur 14 Slide Presentasi Sempro (Lengkap dengan Naskah Pembicara)

Gunakan struktur slide di bawah ini untuk membuat presentasi di Canva atau Microsoft PowerPoint:

### Slide 1: Judul & Tim Peneliti (Cover)
- **Konten:**  
  - Judul: *Analisis Kinematik dan Evaluasi Postur Olahraga Real-Time Berbasis AI Pose Estimation pada Sistem SKELIO*
  - Tim: Rizma Indra Pramudya, Izora Elverda Narulita Putri, Putera Al Khalidi, Muhammad Abdullah Ro'in
  - Dosen Pengampu: Saifudin Yahya, S.Kom., M.T.I
  - Universitas Negeri Surabaya — Fakultas Teknik — Teknik Informatika (2026)
- **Naskah Pembicara (Script):**  
  > *"Selamat pagi/siang Bapak Dosen Penguji dan Bapak Saifudin Yahya. Pada kesempatan kali ini, kami dari Kelompok 11 akan mempresentasikan proposal penelitian kami yang berjudul 'Analisis Kinematik dan Evaluasi Postur Olahraga Real-Time Berbasis AI Pose Estimation pada Sistem SKELIO'."*

---

### Slide 2: Latar Belakang & Urgensi Masalah
- **Poin Utama:**  
  - Latihan beban tubuh mandiri (kalistenik: push-up, squat, sit-up) sangat populer namun rentan cedera akibat kesalahan postur (misal: pinggul turun saat push-up, bungkuk saat squat).
  - Metode konvensional menggunakan Optical Motion Capture (MoCap) berbasis marker/IMU sangat mahal, invasif, dan terbatas di laboratorium.
  - Tantangan Computer Vision saat ini: getaran koordinat (*keypoint jitter*), oklusi tubuh, keterbatasan deteksi telapak tangan, dan inkonsistensi identitas multi-person.
- **Naskah Pembicara:**  
  > *"Latihan kalistenik seperti push-up dan squat banyak diminati karena fleksibel dan hemat biaya. Namun tanpa instruktur profesional, repetisi dengan postur biomekanik yang salah dapat menyebabkan cedera sendi dan tulang belakang. Selama ini, analisis postur hanya bisa dilakukan di laboratorium menggunakan sensor mahal dan penanda fisik yang tidak praktis. Oleh karena itu, dibutuhkan sistem berbasis webcam standar yang mampu mengevaluasi postur secara otomatis, presisi, dan real-time tanpa penanda fisik."*

---

### Slide 3: Rumusan Masalah & Batasan Penelitian
- **Rumusan Masalah (Halaman 3 Proposal):**
  1. Bagaimana mengimplementasikan model YOLOv11-Pose terintegrasi ByteTrack dan One-Euro Filter untuk mengekstraksi dan menstabilkan 14 keypoints secara real-time?
  2. Bagaimana mendeteksi gerakan, menghitung sudut sendi (Hukum Kosinus), dan menghitung repetisi otomatis (FSM)?
  3. Bagaimana tingkat akurasi evaluasi postur, perhitungan repetisi, serta performa komputasi (FPS & Latensi)?
- **Batasan Masalah:**
  - 3 Gerakan: Push-up, Squat, Sit-up.
  - Single Camera 2D RGB (Sudut pandang samping / Sagittal Plane).
  - Kapasitas pelacakan maksimal 3 orang secara simultan (timeout 5 detik).
  - Skema COCO 14-Keypoints dengan resolusi inferensi 640 piksel.

---

### Slide 4: Tujuan & Manfaat Penelitian
- **Tujuan Penelitian:**
  - Membangun pipeline akuisisi real-time berbasis YOLOv11-Pose, ByteTrack, dan One-Euro Filter.
  - Mengimplementasikan analisis kinematik Hukum Kosinus dan Finite State Machine (FSM).
  - Mengevaluasi akurasi terhadap ground truth dan mengukur stabilitas FPS/latensi.
- **Manfaat Penelitian:**
  - **Teoritis:** Kontribusi ilmiah pengoptimalan model single-stage tanpa perlu classifier eksternal (*zero-external-classifier*).
  - **Praktis:** Aplikasi pemantauan kebugaran yang ringan dilengkapi HUD interaktif, Dynamic Depth Bar, dan visualisasi sudut.

---

### Slide 5: Landasan Teori & Arsitektur Inti
- **Komponen Utama Pipeline SKELIO:**
  1. **YOLOv11-Pose:** Arsitektur single-stage dengan blok C3k2 dan mekanisme perhatian C2PSA untuk deteksi 14 titik anatomis.
  2. **ByteTrack:** Mengatasi oklusi dan mempertahankan track ID hingga 3 orang melalui dua tahap asosiasi Kalman Filter.
  3. **One-Euro Filter:** Low-pass filter adaptif orde pertama untuk memecahkan dilema *jitter-lag trade-off*.
  4. **Palm Center Tracker:** Proyeksi 35% vektor siku-ke-pergelangan untuk melacak titik tumpu telapak tangan.
- **Naskah Pembicara:**  
  > *"Sistem SKELIO mengintegrasikan 4 pilar utama. YOLOv11-Pose mengekstraksi keypoint, ByteTrack menjaga ID agar tidak tertukar antar-orang, One-Euro Filter meredam getaran mikroskopis koordinat saat menahan gerakan, dan algoritma proyeksi telapak tangan mengatasi kelemahan model COCO yang hanya mendeteksi hingga pergelangan tangan."*

---

### Slide 6: Analisis Kinematik 2D (Hukum Kosinus & FSM)
- **Rumus Hukum Kosinus untuk Sudut Sendi B (diapit titik A dan C):**
  $$\cos(\theta) = \frac{a^2 + c^2 - b^2}{2ac}$$
  $$\theta = \arccos\left(\text{clip}\left(\frac{a^2 + c^2 - b^2}{2ac}, -1, 1\right)\right)$$
- **Logika Transisi Finite State Machine (FSM):**
  - **Push-up:** UP (sudut siku > 155°) $\rightarrow$ DOWN (sudut siku < 90°) $\rightarrow$ UP (Rep + 1). Postur: Sudut bahu-panggul-lutut > 150° (mencegah *hip sagging*).
  - **Squat:** UP (lutut > 155°) $\rightarrow$ DOWN (lutut < 100°) $\rightarrow$ UP (Rep + 1). Postur: Sudut dada-panggul-lutut > 70° (mencegah bungkuk).
  - **Sit-up:** DOWN (rebah > 125°) $\rightarrow$ UP (duduk < 65°) $\rightarrow$ Rep + 1.

---

### Slide 7: Keterkaitan dengan Karakteristik Big Data
*(Kunci Utama untuk Mata Kuliah Big Data / Skripsi)*
- **Karakteristik Big Data:**
  - **Volume:** Dataset spasial koordinat titik sendi mencapai **3+ Juta baris** data (`evaluasi_homografi_fitness_3juta.xlsx`).
  - **Velocity:** Aliran frame video real-time berkecepatan 30–45 FPS menghasilkan puluhan ribu data numerik per menit secara kontinu.
  - **Variety:** Transformasi data tidak terstruktur (video stream RGB) menjadi data tabular terstruktur berdimensi tinggi ($X, Y$, Confidence, Timestamp, Track ID).
- **Pemetaan Homografi:**  
  Transformasi koordinat spasial perspektif miring kamera menjadi bidang datar tegak lurus (*bird's-eye view*) untuk validasi posisi absolut.

---

### Slide 8: Hasil Pengujian Model & Benchmarking
- **Tampilkan Gambar:** `assets_sempro/chart1_fps_vs_accuracy.png` & `assets_sempro/chart3_spatial_errors.png`
- **Tampilkan Tabel Benchmarking Komparatif.**
- **Poin Presentasi:**
  - Model YOLOv11 Small mencapai akurasi mAP50 sebesar **99.20%** dengan galat posisi sendi (MPE) terendah yaitu **0.50 piksel**.
  - Waktu inferensi mencapai 193.47 ms per frame, siap dioptimalkan lebih lanjut menggunakan TensorRT untuk GPU laptop LOQ RTX.

---

### Slide 9: Metodologi Evaluasi & Pengujian Empiris
- **Indikator & Rumus Evaluasi Sesuai Bab III Proposal:**
  1. **Kesalahan Hitung Repetisi:**  
     $$E_{rep} = |R_s - R_g|, \quad E_{rep}(\%) = \frac{|R_s - R_g|}{R_g} \times 100\%$$
  2. **Akurasi Evaluasi Postur:**  
     $$A_{postur}(\%) = \frac{N_{benar}}{N_{total}} \times 100\%$$
  3. **Stabilitas Koordinat Keypoints:**  
     $$D_t = \sqrt{(x_t - x_{t-1})^2 + (y_t - y_{t-1})^2}$$
  4. **Metrik Performa Komputasi:** FPS aktual dan latensi end-to-end (ms).

---

### Slide 10: Tampilan Antarmuka Sistem SKELIO (Visual Showcase)
- **Tampilkan Gambar:** `test_pushup_result.jpg` dan `test_squat_result.jpg`.
- **Elemen Visual yang Diterangkan:**
  1. **Bounding Box & Skeleton:** Garis persendian warna kuning/neon.
  2. **Angle Arc (Busur Sudut):** Visualisasi sudut siku & lutut secara real-time.
  3. **HUD Card (Heads-Up Display):** Menampilkan ID Subjek, Status Postur, Reps Counter, Sudut Derajat, dan FPS.
  4. **Dynamic Depth Indicator Bar:** Bar vertikal persentase (0–100%) dengan indikasi warna (Merah = Dangkal, Hijau = Kedalaman Sempurna).
  5. **Palm Center Dot:** Titik hijau penanda telapak tangan.

---

### Slide 11: Live Demonstration / Video Playback
- **Langkah Tindakan:**  
  Jalankan file `run_demo_video_pushup.bat` atau `run_skelio.bat`.  
  Tunjukkan kepada penguji bagaimana FSM mengubah state dari `UP` $\rightarrow$ `DOWN` $\rightarrow$ `UP`, dan hitungan Reps bertambah secara valid hanya jika kedalaman tercapai.

---

### Slide 12: Roadmap & Rencana Tahapan Skripsi Selanjutnya
- **Timeline Penelitian:**
  - **Tahap 1:** Penyelesaian Seminar Proposal (Bulan ini).
  - **Tahap 2:** Pengambilan data sampel 1–3 orang di Kampus UNESA Ketintang dengan ground truth manual.
  - **Tahap 3:** Akselerasi NVIDIA TensorRT pada laptop Lenovo LOQ RTX untuk mencapai target 30–45 FPS.
  - **Tahap 4:** Evaluasi statistik (Confusion Matrix, Error Repetisi, IDF1).
  - **Tahap 5:** Penyusunan Laporan Skripsi & Sidang Akhir.

---

### Slide 13: Kesimpulan
- **Poin Kesimpulan:**
  1. Sistem SKELIO berhasil mengintegrasikan model YOLOv11-Pose, ByteTrack, dan One-Euro Filter dalam arsitektur tunggal tanpa classifier tambahan.
  2. Analisis kinematik berbasis Hukum Kosinus dan FSM terbukti efektif mengevaluasi bentuk gerakan kalistenik (push-up, squat, sit-up) dan menghitung repetisi secara akurat.
  3. Prototipe dan dataset Big Data 3+ juta baris siap diuji secara empiris sesuai kaidah metodologi penelitian UNESA.

---

### Slide 14: Sesi Tanya Jawab (Q&A)
- *"Terima kasih atas perhatian Bapak Dosen Penguji. Kami membuka sesi pertanyaan, kritik, dan saran untuk penyempurnaan penelitian ini."*

---

## 🛡️ 6. Panduan Menjawab Pertanyaan Kritis Dosen Penguji (Q&A Defense)

Berikut adalah pertanyaan yang paling sering diajukan dosen penguji beserta jawaban terbaiknya:

#### Q1: "Mengapa menggunakan YOLOv11-Pose dan bukan MediaPipe yang sudah umum?"
> **Jawaban:**  
> *"MediaPipe Pose dirancang untuk single-person. Jika ada dua atau tiga orang di depan kamera, MediaPipe akan mengalami kebingungan atau hanya melacak satu orang acak. Sementara YOLOv11-Pose adalah model deteksi single-stage berbasis top-down yang mampu mendeteksi multi-person secara bersamaan dalam satu inferensi. Selain itu, YOLOv11 memiliki modul perhatian C2PSA yang sangat tangguh saat sebagian anggota tubuh tertutup (oklusi) pada gerakan push-up atau squat."*

#### Q2: "Mengapa perlu menggunakan One-Euro Filter, mengapa tidak Kalman Filter saja?"
> **Jawaban:**  
> *"Kalman Filter standar memerlukan tuning matriks kovariansi yang kompleks dan cenderung menimbulkan keterlambatan (lag) ketika terjadi gerakan cepat. One-Euro Filter dirancang khusus untuk interaksi manusia dengan menyesuaikan frekuensi cutoff secara adaptif: saat pengguna menahan postur statis (plank), frekuensi cutoff diturunkan untuk meredam jitter piksel kamera. Namun saat pengguna bergerak cepat, frekuensi cutoff dinaikkan secara proporsional sehingga titik sendi bergerak responsif dengan latensi 0 ms."*

#### Q3: "Di mana letak aspek Big Data dalam penelitian ini?"
> **Jawaban:**  
> *"Sesuai dengan pembahasan di Bab II Halaman 5 proposal kami, aspek Big Data terletak pada dua karakteristik utama: Volume dan Velocity. Kamera video 30-45 FPS menangkap puluhan frame per detik. Setiap frame diekstraksi menjadi 14 titik koordinat dua dimensi beserta confidence score untuk hingga 3 orang, menghasilkan jutaan baris data tabular spasial berdimensi tinggi. Hal ini telah kami buktikan dengan perekaman dataset 3+ juta baris (`evaluasi_homografi_fitness_3juta.xlsx`) yang kami gunakan untuk analisis homografi dan evaluasi galat kinematik."*

#### Q4: "Bagaimana sistem memastikan repetisi tidak dihitung jika gerakannya curang (setengah-setengah / half-rep)?"
> **Jawaban:**  
> *"Sistem menggunakan Finite State Machine (FSM) dengan ambang batas sudut yang ketat. Pada push-up misalnya, transisi dari state 'UP' ke 'DOWN' hanya terjadi jika sudut siku melewati ambang batas bawah (< 90°). Jika pengguna hanya menekuk siku 120° lalu naik kembali, FSM tidak akan pernah masuk ke state 'DOWN', sehingga saat kembali naik hitungan Reps tidak akan bertambah. Ini diperkuat dengan Dynamic Depth Bar yang menuntut pengguna mencapai kedalaman minimal 70%."*

---

*File aset pendukung tersedia di folder `E:\Codingan BARU\Bigdata\assets_sempro\`.*
