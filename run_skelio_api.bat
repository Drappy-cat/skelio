@echo off
setlocal
title SKELIO API v3.1 - Low-Latency FastAPI WebSocket Server (UNESA)
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO v3.1: SPLIT-PIPELINE FASTAPI + WEBSOCKET SERVER
echo Untuk Aplikasi Android Native (Bare React Native)
echo ====================================================================
echo.
echo [*] Alamat IP lokal laptop Anda (gunakan salah satu di aplikasi HP):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    for /f "tokens=1" %%b in ("%%a") do echo     ws://%%b:8000/ws/pose
)
echo.
echo [*] Memuat model AI YOLOv11 ^& server WebSocket di port 8000...
echo [TIPS] Tekan CTRL+C untuk menghentikan server.
echo ====================================================================
echo.

set "PY_CMD="
py -3.11 -c "import cv2, ultralytics, fastapi, uvicorn" >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD python -c "import cv2, ultralytics, fastapi, uvicorn" >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD py -3.10 -c "import cv2, ultralytics, fastapi, uvicorn" >nul 2>nul && set "PY_CMD=py -3.10"

if not defined PY_CMD (
    echo [ERROR] Tidak ditemukan Python dengan library cv2, ultralytics, fastapi, dan uvicorn.
    echo Jalankan perintah berikut untuk memasang dependensi:
    echo     python -m pip install opencv-python ultralytics fastapi uvicorn websockets
    echo.
    pause
    exit /b 1
)

echo [*] Menggunakan interpreter: %PY_CMD%
%PY_CMD% -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

echo.
echo Server API SKELIO telah dimatikan.
pause
