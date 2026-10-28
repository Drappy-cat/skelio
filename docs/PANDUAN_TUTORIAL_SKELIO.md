# 🏋️ BUKU PANDUAN LENGKAP & TUTORIAL SISTEM SKELIO
**Mata Kuliah:** Big Data — Program Studi S1 Teknik Informatika UNESA (2026)  
**Kelompok 11:** Rizma Indra Pramudya, Izora Elverda Narulita Putri, Putera Al Khalidi, Muhammad Abdullah Ro'in  
**Dosen Pengampu:** Saifudin Yahya, S.Kom., M.T.I  
**Dokumen Acuan:** `KELOMPOK 11 BIG DATA .pdf` (*ANALISIS KINEMATIK DAN EVALUASI POSTUR OLAHRAGA REAL-TIME BERBASIS AI POSE ESTIMATION PADA SISTEM SKELIO*)

---

## 📂 1. Peta Struktur Folder Proyek `E:\Codingan BARU\Bigdata`

Seluruh kebutuhan data, model, konfigurasi, dan kode program telah dipisahkan secara independen di dalam folder ini (repositori utama asli Anda tetap aman 100% dan tidak disentuh):

```
E:\Codingan BARU\Bigdata\
│
├── 📜 KELOMPOK 11 BIG DATA .pdf      <- Naskah Proposal Penelitian / Proyek SKELIO
├── 📊 evaluasi_homografi_fitness_3juta.xlsx <- Dataset Big Data koordinat spasial (3+ Juta baris)
├── 📄 Rancangan Teknis_...pdf        <- Cetak biru arsitektur multi-stage pipeline
│
├── 🐍 biomechanical_pipeline.py     <- Program Utama (Webcam Real-Time SKELIO: Push-up, Squat, Sit-up)
├── ⚙️ bytetrack_live.yaml           <- Konfigurasi ByteTrack Multi-Person (Maks. 3 orang)
├── 📦 yolo11n-pose.pt               <- Bobot model resmi COCO Pose untuk inferensi instan
├── 🚀 benchmark_evaluation.py       <- Skrip pengujian latensi, FPS, mAP, JAA, & MPE
├── ⚡ export_tensorrt.py            <- Skrip konversi model ke NVIDIA TensorRT FP16 (GPU Laptop)
├── 🏋️ batch_training.py             <- Skrip pelatihan model YOLOv11-Pose kalistenik
├── 📈 yolo11_biomechanics_benchmark.csv <- Hasil rekam benchmarking performa sistem
├── 📋 requirements.txt              <- Daftar pustaka/library Python yang dibutuhkan
├── 🚀 run_skelio.bat                <- File launcher 1-klik untuk menjalankan webcam SKELIO
│
├── 📁 notebooks/                    <- Eksperimen Analisis & Olah Data
│   ├── keypoint_detection_homography_mapping.ipynb  <- Algoritma pemetaan homografi & ekstraksi data
│   └── EDA.ipynb                                   <- Analisis eksplorasi distribusi titik sendi
│
├── 📁 models/                       <- Bobot Model Terlatih
│   └── best_calisthenics_pose.pt    <- Model terbaik hasil training pada dataset kalistenik
│
└── 📁 dataset/                      <- Data Latih & Validasi
    └── exercise.v4-up-exercise.yolov8/  <- Dataset citra & label (train, valid, test, data.yaml)
```

---

## ⚙️ 2. Prasyarat & Penyiapan Lingkungan Python (PENTING)

Sistem SKELIO menggunakan **PyTorch** dan **Ultralytics YOLOv11**.
> ⚠️ **Catatan Penting Python di Windows:**  
> Sangat disarankan menggunakan **Python 3.10** atau **Python 3.11** (jangan gunakan Python 3.14 karena PyTorch belum merilis wheel biner resmi Windows untuk 3.14). Di komputer Anda, Python 3.11 dan 3.10 sudah terpasang di sistem.

### Langkah Instalasi Library:
Buka **Terminal / PowerShell** di komputer Anda, lalu jalankan perintah berikut:

```powershell
# 1. Masuk ke direktori Bigdata
cd "E:\Codingan BARU\Bigdata"

# 2. Instal PyTorch (Pilih salah satu sesuai perangkat):
# JIKA INGIN MENGGUNAKAN GPU NVIDIA (Disarankan untuk Laptop LOQ RTX Anda):
py -3.11 -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# ATAU JIKA INGIN MENGGUNAKAN CPU SAJA:
# py -3.11 -m pip install torch torchvision

# 3. Instal pustaka pendukung SKELIO & Big Data Excel:
py -3.11 -m pip install -r requirements.txt
```

---

## 🎥 3. Cara Menjalankan Sistem SKELIO (Webcam Real-Time)

### Cara A: 1-Klik Launcher (Paling Mudah)
Cukup **klik dua kali (double click)** pada file:
👉 `run_skelio.bat`

### Cara B: Lewat Terminal / PowerShell
```powershell
cd "E:\Codingan BARU\Bigdata"
py -3.11 biomechanical_pipeline.py
```
*(Jika ingin menggunakan video file rekaman alih-alih webcam, cukup tambahkan nama file video: `py -3.11 biomechanical_pipeline.py "video_latihan.mp4"`)*.

---

## 🎮 4. Panduan Tombol Kontrol Keyboard Saat Kamera Aktif

Saat jendela **"Sistem SKELIO - Evaluasi Kinematik Real-Time (UNESA)"** terbuka, Anda dapat mengontrol sistem secara langsung menggunakan keyboard:

| Tombol Keyboard | Fungsi / Aksi | Keterangan Kinematik |
| :---: | :--- | :--- |
| **`1`** | **Mode PUSH-UP** | Mengukur sudut siku (Target <90° turun, >155° naik) dan mendeteksi pinggul turun (*sagging*). |
| **`2`** | **Mode SQUAT** | Mengukur fleksi sudut lutut (Target <100° turun, >155° berdiri) dan mengevaluasi kelurusan punggung. |
| **`3`** | **Mode SIT-UP** | Mengukur sudut kontraksi torso-paha (<65° saat duduk naik, >125° saat rebah). |
| **`A`** | **Mode AUTO** | Sistem mendeteksi otomatis gerakan berdasarkan orientasi tubuh (tegak vs rebah). |
| **`R`** | **Reset Hitungan** | Me-reset hitungan repetisi (Reps) semua orang kembali ke 0. |
| **`Q`** atau `ESC` | **Keluar** | Menutup kamera dan keluar dari program. |

---

## 📊 5. Fitur Utama Sistem SKELIO yang Sesuai dengan Naskah Proposal

1. **Pelacakan Multi-Person (Maks. 3 Orang Bersamaan):**  
   Didukung oleh algoritma **ByteTrack** (`bytetrack_live.yaml`) tanpa benturan ID. Masing-masing orang mendapatkan kartu HUD statistik dan depth bar sendiri dengan warna berbeda (*Person 1 Kuning, Person 2 Hijau, Person 3 Orange*).
2. **One-Euro Filter (Peredam Jitter Spasial):**  
   Mencegah titik sendi bergetar saat Anda menahan gerakan (misal saat posisi plank atau bawah squat).
3. **Palm Center Tracker:**  
   Menyelesaikan masalah batas deteksi pergelangan tangan dengan memproyeksikan titik tengah telapak tangan sebesar 35% panjang lengan.
4. **Finite State Machine (FSM) & Dynamic Depth Bar:**  
   Menghitung repetisi valid hanya jika mencapai ambang kedalaman yang sempurna, dilengkapi bar persentase dinamis (0–100%).

---

## 📑 6. Menghubungkan dengan Dataset 3 Juta Baris (`evaluasi_homografi_fitness_3juta.xlsx`)

File `evaluasi_homografi_fitness_3juta.xlsx` merupakan representasi karakteristik **Big Data** (Volume & Velocity) yang dibahas pada Bab II Hal 5 proposal Anda.

Untuk menganalisis atau menjalankan pipeline pemetaan homografi terhadap dataset tersebut:
1. Buka Jupyter Notebook:
   ```powershell
   py -3.11 -m notebook notebooks/keypoint_detection_homography_mapping.ipynb
   ```
2. Notebook ini berisi:
   - Transformasi matriks homografi dari bidang kamera 2D miring ke bidang datar tegak lurus (*bird's-eye view*).
   - Ekstraksi koordinat keypoints frame-by-frame menjadi jutaan baris data tabular.
   - Perhitungan error metrik spasial (Mean Pixel Error).

---

## ⚡ 7. Pengujian Tambahan (Benchmark & TensorRT)

* **Menjalankan Pengujian Benchmark (Bab III Hal 17):**
  ```powershell
  py -3.11 benchmark_evaluation.py
  ```
  *Skrip ini akan menguji latensi inferensi, rata-rata FPS, dan merekam hasilnya ke file `yolo11_biomechanics_benchmark.csv`.*

* **Mengekspor Model ke TensorRT (Jika ingin inferensi ultra-cepat di GPU RTX):**
  ```powershell
  py -3.11 export_tensorrt.py
  ```

---

*Semua file di folder ini siap pakai untuk demonstrasi tugas mata kuliah Big Data maupun ujian proposal penelitian SKELIO.*
