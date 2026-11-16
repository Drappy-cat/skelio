@echo off
title SKELIO API v3.0 - Low-Latency FastAPI WebSocket Server (UNESA)
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO v3.0: SPLIT-PIPELINE FASTAPI + WEBSOCKET SERVER
echo Untuk Aplikasi Android Native (Bare React Native)
echo ====================================================================
echo.
echo [*] Alamat IP lokal laptop Anda (gunakan salah satu di aplikasi HP):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do echo     ws:%%a:8000/ws/pose
echo.
echo [*] Memuat model AI YOLOv11 & server WebSocket di port 8000...
echo [TIPS] Tekan CTRL+C untuk menghentikan server.
echo ====================================================================
echo.

python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

echo.
echo Server API SKELIO telah dimatikan.
pause
