# 🌐 SKELIO Web Application (Roadmap & Architecture)

Modul ini dipersiapkan untuk pengembangan antarmuka berbasis web dari sistem **SKELIO (Real-Time Biomechanical Analysis)**.

---

## 🏗️ 1. Arsitektur Terencana (Planned Architecture)

Aplikasi web dirancang dengan arsitektur **Client-Server Real-Time Streaming**:

```
[ Browser Klien (Webcam) ]
        │  ▲
        │  │ WebSocket / WebRTC (Frame 30 FPS + JSON Telemetry)
        ▼  │
[ FastAPI / Flask Backend ]
        │
   (SKELIO Core Engine)
   - YOLOv11-Pose
   - ByteTrack
   - One-Euro Filter
   - Kinematics & FSM Counter
```

- **Frontend:** Next.js / React + TailwindCSS + HTML5 Canvas untuk rendering Skeleton, Angle Arc, dan HUD.
- **Backend:** Python FastAPI dengan WebSocket endpoint untuk streaming video berlatensi rendah (<50ms).
- **Core Link:** Mengimpor `BiomechanicalPipeline` langsung dari `../../core/biomechanical_pipeline.py`.

---

## 📂 2. Struktur Direktori yang Direncanakan

```
apps/web/
├── frontend/             # Next.js / React Source Code
│   ├── public/           # Aset statis & logo
│   └── src/
│       ├── components/   # HUDCard, DepthBar, VideoCanvas
│       └── app/          # Dashboard & workout session
│
└── backend/              # FastAPI Streaming Server
    ├── server.py         # WebSocket video stream handler
    └── requirements.txt  # FastAPI, uvicorn, websockets
```

---

## 🚀 3. Status Pengembangan

*Status:* **Pondasi Arsitektur Siap**. Core engine telah teruji di folder `core/` dan siap dihubungkan ke endpoint WebSocket FastAPI saat tahap implementasi web app dimulai.
