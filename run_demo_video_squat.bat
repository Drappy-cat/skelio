@echo off
setlocal
title Sistem SKELIO - Demo Video Squat (UNESA)
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO: DEMO EVALUASI SQUAT DARI VIDEO
echo Program Studi S1 Teknik Informatika UNESA - Kelompok 11 Big Data
echo ====================================================================
echo.
echo [Petunjuk]: Tekan tombol keyboard '2' untuk mengaktifkan mode Squat jika belum otomatis.

set "PY_CMD="
py -3.11 -c "import cv2, ultralytics" >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD python -c "import cv2, ultralytics" >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD py -3.10 -c "import cv2, ultralytics" >nul 2>nul && set "PY_CMD=py -3.10"

if not defined PY_CMD (
    echo [ERROR] Tidak ditemukan Python dengan library 'cv2' dan 'ultralytics'.
    echo Jalankan: python -m pip install opencv-python ultralytics torch
    pause
    exit /b 1
)

%PY_CMD% biomechanical_pipeline.py "assets_sempro\raw_squat_sample.mp4"
pause
