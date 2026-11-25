@echo off
title SKELIO - Unified Application (Kelompok 11 Big Data UNESA)
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO: SATU PERINTAH RUNNING (All-in-One: AI + Camera + UI)
echo Kelompok 11 Big Data - S1 Teknik Informatika UNESA
echo ====================================================================
echo.
echo [*] Menyiapkan server SKELIO di port 5000...
echo [*] Backend Flask, AI YOLOv11-Pose, & UI Frontend telah disatukan!
echo.
echo [TIPS] Browser akan terbuka otomatis di http://localhost:5000
echo [TIPS] Tekan CTRL+C di jendela ini jika ingin mematikan aplikasi.
echo ====================================================================
echo.

python apps\web\app.py

pause
