# 📱 SKELIO Mobile Application (Roadmap & Architecture)

Modul ini dipersiapkan untuk pengembangan aplikasi seluler (Android / iOS) berbasis **Edge AI (On-Device Inference)** dari sistem **SKELIO**.

---

## 🏗️ 1. Arsitektur Terencana (Planned Architecture)

Untuk penggunaan latihan mandiri (kalistenik di lantai/kamar), pemrosesan dilakukan secara lokal di perangkat tanpa membutuhkan koneksi internet server:

```
[ Kamera HP (Android / iOS) ]
        │
   (On-Device Processing)
   ├── Model: YOLOv11-Pose (.tflite / ONNX Runtime Mobile)
   ├── Smoother: One-Euro Filter (Native C++ / Dart)
   └── Logic: Cosine Law & FSM State Machine
        │
[ Tampilan HUD & Audio Coaching ]
- Suara Umpan Balik: "Pinggul terlalu turun!"
- Dynamic Depth Bar Vertikal
- Reps Counter otomatis
```

---

## 🛠️ 2. Rekomendasi Tech Stack

- **Cross-Platform:** Flutter / Dart (atau React Native).
- **Model Engine:** TensorFlow Lite (TFLite FP16) yang dikonversi dari `core/models/best_calisthenics_pose.pt`.
- **Hardware Acceleration:** NNAPI (Android) / Metal (iOS) untuk inferensi 30+ FPS pada prosesor smartphone modern.

---

## 🚀 3. Status Pengembangan

*Status:* **Pondasi Arsitektur Siap**. Konversi model ke TFLite dan integrasi Flutter dijadwalkan pada roadmap pasca-Seminar Proposal.
