@echo off
setlocal
title SKELIO - Native Desktop Application (UNESA)
cd /d "%~dp0"

echo ====================================================================
echo SISTEM SKELIO: NATIVE DESKTOP APPLICATION (Standalone Window)
echo Kelompok 11 Big Data - S1 Teknik Informatika UNESA
echo ====================================================================
echo.
echo [*] Memuat model AI YOLOv11 ^& server background...

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

:: Jalankan server backend di background
echo [*] Menggunakan interpreter: %PY_CMD%
start /B "" %PY_CMD% apps\web\app.py

:: Tunggu 3 detik sampai model siap
echo [*] Menyiapkan jendela aplikasi native...
timeout /t 3 /nobreak >nul

:: Luncurkan jendela mandiri tanpa tab/address bar (Native App Mode)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo [*] Membuka via Microsoft Edge App Container...
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="http://localhost:5000" --window-size=1366,850
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [*] Membuka via Google Chrome App Container...
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="http://localhost:5000" --window-size=1366,850
) else (
    start "" http://localhost:5000
)

echo.
echo [INFO] Aplikasi SKELIO Desktop sedang berjalan di jendela khusus.
echo [TIPS] Tutup jendela aplikasi atau tekan CTRL+C di sini jika selesai.
echo ====================================================================
pause
