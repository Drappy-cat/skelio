@echo off
setlocal
title SKELIO - Web Application Dashboard (UNESA)
:: Pindah ke direktori tempat file .bat berada
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO: WEB APPLICATION DASHBOARD (YOLOv11-Pose Engine)
echo Kelompok 11 Big Data - S1 Teknik Informatika UNESA
echo ====================================================================
echo.
echo [*] Memuat model AI YOLOv11 ^& server web Flask...
echo [*] Mohon tunggu beberapa detik, peramban (browser) akan terbuka otomatis!
echo.
echo [TIPS] Tekan CTRL+C di jendela hitam ini jika ingin menutup aplikasi.
echo ====================================================================
echo.

set "PY_CMD="
py -3.11 -c "import cv2, ultralytics, flask" >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD python -c "import cv2, ultralytics, flask" >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD py -3.10 -c "import cv2, ultralytics, flask" >nul 2>nul && set "PY_CMD=py -3.10"

if not defined PY_CMD (
    echo [ERROR] Tidak ditemukan Python dengan library cv2, ultralytics, dan flask.
    echo Jalankan perintah berikut untuk memasang dependensi:
    echo     python -m pip install opencv-python ultralytics flask
    echo.
    pause
    exit /b 1
)

echo [*] Menggunakan interpreter: %PY_CMD%
%PY_CMD% apps\web\app.py

echo.
echo Server SKELIO telah dimatikan.
pause
