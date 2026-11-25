@echo off
title SKELIO - Fullstack AI Runner (Backend + UI)
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO: RUNNER PENUH (Backend YOLOv11 + Frontend Vite UI)
echo Kelompok 11 Big Data - S1 Teknik Informatika UNESA
echo ====================================================================
echo.
echo [*] Menyalakan Backend Flask & Model YOLOv11 di Background...
start "SKELIO Backend AI" cmd /k "cd /d "%~dp0" && python apps\web\app.py"

echo [*] Menunggu backend siap (3 detik)...
timeout /t 3 /nobreak >nul

echo [*] Menyalakan Frontend UI Vite...
start "SKELIO Frontend UI" cmd /k "cd /d "%~dp0" && npm run dev"

echo.
echo ====================================================================
echo [SELESAI] Kedua server sedang aktif!
echo Buka browser di http://localhost:5173 untuk menggunakan aplikasi.
echo ====================================================================
pause
