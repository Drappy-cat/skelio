# 🏋️ SKELIO: Real-Time Biomechanical Analysis Pipeline

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.14-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![YOLOv11](https://img.shields.io/badge/YOLOv11-Pose-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black)](https://github.com/ultralytics/ultralytics)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![UNESA](https://img.shields.io/badge/UNESA-Informatika_2026-F59E0B?style=for-the-badge)](https://www.unesa.ac.id/)

> **Sistem Evaluasi Postur Olahraga dan Penghitungan Repetisi Real-Time Berbasis AI Pose Estimation Tanpa Penanda Fisik (Markerless Biomechanics).**  
> *Proposal Penelitian & Tugas Besar Big Data — Program Studi S1 Teknik Informatika, Universitas Negeri Surabaya (UNESA) 2026.*

---

## 👥 Tim Peneliti (Kelompok 11 Big Data UNESA)
- **Rizma Indra Pramudya** (NIM: 25051204370)
- **Izora Elverda Narulita Putri** (NIM: 25051204287)
- **Putera Al Khalidi** (NIM: 25051204362)
- **Muhammad Abdullah Ro'in** (NIM: 25051204270)  
*Dosen Pengampu / Pembimbing:* **Saifudin Yahya, S.Kom., M.T.I**

---

## 🌟 Fitur Unggulan Sistem SKELIO

1. **Single-Stage Pose Estimation (YOLOv11-Pose):**  
   Mengekstraksi 14 titik kunci anatomi tubuh (*COCO format*) secara simultan dengan mekanisme perhatian spasial paralel (*C2PSA*) yang tangguh terhadap oklusi tubuh.
2. **Multi-Person Tracking (ByteTrack):**  
   Melacak hingga 3 subjek secara bersamaan tanpa benturan ID (*identity switch*) menggunakan asosiasi dua tahap Kalman Filter.
3. **Peredam Getaran Adaptif (One-Euro Filter):**  
   Menyelesaikan dilema *jitter-lag trade-off*: meredam getaran piksel saat posisi statis (plank) dan bebas lag saat gerakan transisi cepat.
4. **Palm Center Tracker:**  
   Mengatasi keterbatasan model COCO yang hanya mendeteksi hingga pergelangan tangan dengan memproyeksikan titik tengah telapak tangan (35% vektor siku-ke-pergelangan).
5. **Kinematika 2D & Finite State Machine (FSM):**  
   Menghitung sudut sendi dengan **Hukum Kosinus** dan menghitung repetisi valid hanya jika mencapai ambang kedalaman yang sempurna.
6. **Heads-Up Display (HUD) & Dynamic Depth Bar (0–100%):**  
   Indikator visual real-time dengan kartu statistik multi-subjek, busur sudut (*angle arc*), dan pelacakan postur bersih (*Clean Reps*).

---

## 📂 Struktur Repositori Modular (Monorepo Layout)

Struktur repositori telah dipisahkan secara modular untuk memudahkan ekspansi ke aplikasi Web dan Mobile:

```
skelio/
├── 🌐 apps/
│   ├── web/                    # Rencana arsitektur Web App (Next.js / FastAPI WebRTC)
│   └── mobile/                 # Rencana arsitektur Mobile App (Flutter / Android TFLite)
│
├── ⚙️ core/                    # Engine Utama SKELIO
│   ├── biomechanical_pipeline.py  # Pipeline real-time webcam & video evaluator
│   ├── bytetrack_live.yaml        # Konfigurasi kustom ByteTrack
│   ├── batch_training.py          # Skrip pelatihan model YOLOv11 kalistenik
│   ├── benchmark_evaluation.py    # Skrip pengujian FPS, latensi, dan MPE
│   ├── export_tensorrt.py         # Skrip ekspor model ke NVIDIA TensorRT FP16
│   ├── generate_demo_videos.py    # Skrip builder video demo evaluasi
│   ├── generate_sempro_charts.py  # Skrip visualisasi grafik komparasi model
│   └── yolo11_biomechanics_benchmark.csv # Data benchmark empiris
│
├── 📦 models/                  # Bobot model AI terlatih
│   ├── best_calisthenics_pose.pt  # Model terlatih kalistenik (19.9 MB)
│   └── yolo11n-pose.pt            # Bobot model COCO baseline
│
├── 📊 dataset/                 # Dataset citra & anotasi Roboflow
│   └── exercise.v4-up-exercise.yolov8/ (train, valid, test, data.yaml)
│
├── 📓 notebooks/               # Eksperimen data & analisis spasial
│   ├── EDA.ipynb               # Exploratory Data Analysis
│   └── keypoint_detection_homography_mapping.ipynb # Pemetaan homografi
│
├── 📚 docs/                    # Berkas naskah akademik & presentasi
│   ├── KELOMPOK 11 BIG DATA .pdf  # Naskah Proposal Penelitian Resmi
│   ├── PPT KELOMPOK 11 BIG DATA.pptx # Slide presentasi Sempro
│   ├── PANDUAN_PRESENTASI_SEMPRO.md  # Naskah pembicara & panduan Q&A
│   ├── PANDUAN_TUTORIAL_SKELIO.md    # Buku panduan lengkap sistem
│   └── assets_sempro/          # Grafik high-res dan rekaman video demo
│
├── 🚀 run_skelio.bat           # Launcher 1-klik LIVE Webcam
├── 🎬 run_demo_video_pushup.bat# Launcher 1-klik Demo Video Push-Up
├── 🏋️ run_demo_video_squat.bat # Launcher 1-klik Demo Video Squat
└── requirements.txt            # Dependensi pustaka Python
```

---

## 📊 Hasil Pengujian Benchmarking Model

| Model YOLOv11 | Ukuran (MB) | Latensi (ms) | Kecepatan (FPS) | Galat Sendi (MPE) | Galat Homografi | Akurasi mAP50 | JAA (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **YOLOv11 Nano** | 5.62 MB | 245.23 ms | 4.08 FPS | 4.05 px | 1.62 px | 19.02% | 19.02% |
| **YOLOv11 Small (Best)** | **19.02 MB** | **193.47 ms** | **5.17 FPS** | **0.50 px** | **0.20 px** | **99.20%** | **99.20%** |
| **YOLOv11 Medium** | 40.31 MB | 206.82 ms | 4.84 FPS | 0.50 px | 0.20 px | 99.12% | 99.12% |
| **YOLOv11 Large** | 50.51 MB | 210.34 ms | 4.75 FPS | 0.50 px | 0.20 px | 99.12% | 99.12% |
| **YOLOv11 X-Large** | 112.78 MB| 250.53 ms | 3.99 FPS | 0.88 px | 0.35 px | 82.46% | 82.46% |

---

## ⚡ Panduan Instalasi & Menjalankan Proyek

### 1. Prasyarat Lingkungan
Gunakan **Python 3.10** atau **Python 3.11** (64-bit Windows):
```bash
# Clone repositori
git clone https://github.com/Drappy-cat/skelio.git
cd skelio

# Instal dependensi
pip install -r requirements.txt
```

### 2. Menjalankan Sistem SKELIO
- **Live Webcam:** Dobel klik `run_skelio.bat` atau jalankan:
  ```bash
  python core/biomechanical_pipeline.py
  ```
- **Demo Video Offline (Tanpa Perlu Gerakan Fisik di Depan Penguji):**
  - Push-Up: Dobel klik `run_demo_video_pushup.bat`
  - Squat: Dobel klik `run_demo_video_squat.bat`

### 🎮 Kontrol Keyboard Interaktif:
- `1` : Mode Push-Up (Sudut siku & kelurusan tulang punggung).
- `2` : Mode Squat (Sudut fleksi lutut & ketegakan dada).
- `3` : Mode Sit-Up (Sudut torso-paha saat duduk dan rebah).
- `A` : Auto Detection (Mendeteksi otomatis berdasarkan orientasi tubuh).
- `R` : Reset hitungan repetisi kembali ke 0.
- `Q` / `ESC` : Keluar dari aplikasi.

---

## 📜 Lisensi & Sitasi
Penelitian ini dikembangkan untuk kebutuhan akademik Program Studi S1 Teknik Informatika Universitas Negeri Surabaya (UNESA) tahun 2026.
