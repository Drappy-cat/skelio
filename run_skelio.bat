@echo off
setlocal
title Sistem SKELIO - Real-Time Biomechanics (UNESA)
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO: EVALUASI POSTUR OLAHRAGA REAL-TIME (YOLOv11-Pose)
echo Program Studi S1 Teknik Informatika UNESA - Kelompok 11 Big Data
echo ====================================================================
echo.

:: Deteksi otomatis interpreter Python yang sudah terpasang cv2 ^& ultralytics
set "PY_CMD="
py -3.11 -c "import cv2, ultralytics" >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD python -c "import cv2, ultralytics" >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD py -3.10 -c "import cv2, ultralytics" >nul 2>nul && set "PY_CMD=py -3.10"

if not defined PY_CMD (
    echo [ERROR] Tidak ditemukan Python dengan library 'cv2' dan 'ultralytics'.
    echo Jalankan perintah berikut untuk memasang dependensi:
    echo     python -m pip install opencv-python ultralytics torch
    echo.
    pause
    exit /b 1
)

echo [*] Menjalankan SKELIO dengan interpreter: %PY_CMD%
%PY_CMD% biomechanical_pipeline.py

echo.
echo Aplikasi SKELIO telah ditutup.
pause
