# 📱 SKELIO Native Android (`apps/mobile-rn`) — v3.0.0

Aplikasi Android **native murni** berbasis **Bare React Native CLI (`0.88.1`, Hermes Engine, TypeScript)** tanpa Expo dan tanpa WebView. Model AI tetap berada di luar APK (dijalankan di server **FastAPI** melalui **Split-Pipeline Binary WebSocket**) untuk menjaga ukuran APK tetap ringan dan meminimalkan latensi visual.

---

## ⚡ Arsitektur Split-Pipeline Berlatensi Rendah

1. **Preview Kamera Lokal 60 FPS**: `react-native-vision-camera` (`5.2.4`) menampilkan preview kamera langsung di HP (`implementationMode="compatible"`).
2. **Capture & Downscale di Kotlin (NitroImage)**: Frame kamera di-resize ke lebar `320px` dan di-encode ke JPEG ringan (`quality 60`) sebagai `ArrayBuffer` biner, lalu dikirim ke `/ws/pose` dengan **Queue=1 Backpressure** (frame baru menunggu slot inferensi sebelumnya selesai agar tidak menumpuk antrean).
3. **Server Mengembalikan Koordinat Saja (`~840 bytes`)**: Server FastAPI (`apps/api/main.py`) menjalankan `BiomechanicalPipeline.process_frame_telemetry()` tanpa menggambar HUD OpenCV dan tanpa meng-encode JPEG balik.
4. **Client Smoothing & SVG Overlay**: HP memfilter koordinat menggunakan `OneEuroKeypointFilter` ([src/engine/OneEuroFilter.ts](file:///c:/Users/alama/Favorites/semester%205/BIG%20Data/Projek/skelio/apps/mobile-rn/src/engine/OneEuroFilter.ts)) dan menggambar skeleton di [src/components/SkeletonOverlay.tsx](file:///c:/Users/alama/Favorites/semester%205/BIG%20Data/Projek/skelio/apps/mobile-rn/src/components/SkeletonOverlay.tsx) via `react-native-svg`.

---

## 🚀 Cara Menjalankan & Build APK

### 1. Jalankan Server FastAPI di Laptop
Di folder root `skelio/`, klik ganda `run_skelio_api.bat` atau jalankan:
```bash
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```
Catat IP Wi-Fi laptop yang ditampilkan di terminal (misalnya `ws://192.168.1.31:8000/ws/pose`).

### 2. Install APK Debug ke HP Android (via USB ADB) atau Jalankan Metro
- **Build Debug APK** (1 klik di Windows):
  ```cmd
  apps\mobile-rn\build_android_apk.bat
  ```
- **Build Release APK**:
  ```cmd
  apps\mobile-rn\build_android_apk.bat assembleRelease
  ```
- **Install ke HP Android yang terhubung USB Debugging**:
  ```cmd
  adb install -r apps\mobile-rn\android\app\build\outputs\apk\debug\app-arm64-v8a-debug.apk
  ```
- **Menjalankan Metro Bundler untuk mode Debug**:
  ```cmd
  cd apps\mobile-rn
  npm start
  ```
  *(Jika menggunakan USB, Anda juga bisa menjalankan `adb reverse tcp:8081 tcp:8081` dan `adb reverse tcp:8000 tcp:8000`, lalu ubah Server IP di aplikasi menjadi `ws://127.0.0.1:8000/ws/pose`).*
