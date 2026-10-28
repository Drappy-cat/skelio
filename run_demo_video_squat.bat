@echo off
title Sistem SKELIO - Demo Video Squat (UNESA)
echo ====================================================================
echo SISTEM SKELIO: DEMO EVALUASI SQUAT DARI VIDEO
echo Program Studi S1 Teknik Informatika UNESA - Kelompok 11 Big Data
echo ====================================================================
echo.
echo [Petunjuk]: Tekan tombol keyboard '2' untuk mengaktifkan mode Squat jika belum otomatis.
py -3.11 biomechanical_pipeline.py "assets_sempro\raw_squat_sample.mp4"
pause
