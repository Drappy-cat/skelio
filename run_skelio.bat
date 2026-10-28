@echo off
title Sistem SKELIO - Real-Time Biomechanics (UNESA)
echo ====================================================================
echo SISTEM SKELIO: EVALUASI POSTUR OLAHRAGA REAL-TIME (YOLOv11-Pose)
echo Program Studi S1 Teknik Informatika UNESA - Kelompok 11 Big Data
echo ====================================================================
echo.

:: Prioritas: Python 3.11 atau 3.10 untuk stabilitas PyTorch Windows
where py >nul 2>nul
if %errorlevel% equ 0 (
    echo Mencoba menjalankan dengan Python 3.11...
    py -3.11 biomechanical_pipeline.py
    if %errorlevel% neq 0 (
        echo Mencoba beralih ke Python 3.10...
        py -3.10 biomechanical_pipeline.py
    )
    if %errorlevel% neq 0 (
        echo Mencoba default python...
        python biomechanical_pipeline.py
    )
) else (
    python biomechanical_pipeline.py
)

echo.
echo Aplikasi SKELIO telah ditutup.
pause
