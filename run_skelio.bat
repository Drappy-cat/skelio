@echo off
setlocal
title SKELIO Launcher v3.3 - Real-Time Biomechanics (UNESA)
cd /d "%~dp0"

:: ============================================================================
:: SKELIO UNIFIED LAUNCHER (v3.3.0)
:: Mendukung Menu Interaktif (klik ganda) maupun Argumen CLI:
::   run_skelio.bat api          -> [1] Server API Android (FastAPI + WS :8000)
::   run_skelio.bat web          -> [2] Aplikasi Web UI Baru All-in-One (:5000)
::   run_skelio.bat fullstack    -> [3] Developer Fullstack (Flask :5000 + Vite :5173)
::   run_skelio.bat cam          -> [4] OpenCV Desktop (Webcam / Demo Video)
::   run_skelio.bat demo [1|2]   ->     Shortcut Demo Video (1=Push-Up, 2=Squat)
::   run_skelio.bat apk  [1|2|3] -> [5] Android APK (1=Install USB, 2=Build Release)
:: ============================================================================

set "ARG1=%~1"
set "ARG2=%~2"

if /I "%ARG1%"=="api"       goto mode_api
if /I "%ARG1%"=="1"         goto mode_api
if /I "%ARG1%"=="web"       goto mode_web
if /I "%ARG1%"=="app"       goto mode_web
if /I "%ARG1%"=="desktop"   goto mode_web
if /I "%ARG1%"=="2"         goto mode_web
if /I "%ARG1%"=="fullstack" goto mode_fullstack
if /I "%ARG1%"=="dev"       goto mode_fullstack
if /I "%ARG1%"=="3"         goto mode_fullstack
if /I "%ARG1%"=="cam"       goto mode_opencv
if /I "%ARG1%"=="webcam"    goto mode_cam_direct
if /I "%ARG1%"=="4"         goto mode_opencv
if /I "%ARG1%"=="demo"      goto mode_demo
if /I "%ARG1%"=="apk"       goto mode_apk
if /I "%ARG1%"=="android"   goto mode_apk
if /I "%ARG1%"=="5"         goto mode_apk
if /I "%ARG1%"=="check"     goto mode_check

:menu
set "BASE_PY=[Belum Terdeteksi]"
py -3.11 -c "import cv2, ultralytics" >nul 2>nul && set "BASE_PY=py -3.11"
if "%BASE_PY%"=="[Belum Terdeteksi]" python -c "import cv2, ultralytics" >nul 2>nul && set "BASE_PY=python"
if "%BASE_PY%"=="[Belum Terdeteksi]" py -3.10 -c "import cv2, ultralytics" >nul 2>nul && set "BASE_PY=py -3.10"

cls
echo ====================================================================
echo   SISTEM SKELIO - REAL-TIME BIOMECHANICAL ANALYSIS (UNESA)
echo   Kelompok 11 Big Data - S1 Teknik Informatika
echo   Python Aktif : %BASE_PY%
echo ====================================================================
echo.
echo   [1] Server API Android    ^(FastAPI + WebSocket Port 8000^)
echo   [2] Aplikasi Web UI Baru  ^(All-in-One: AI + React UI Port 5000^)
echo   [3] Fullstack Dev Mode    ^(Backend Port 5000 + Vite HMR Port 5173^)
echo   [4] OpenCV Desktop ^& Demo ^(Live Webcam / Video Push-Up ^& Squat^)
echo   [5] Utilitas APK Android  ^(Pasang via USB / Build Release APK^)
echo   [0] Keluar
echo.
echo ====================================================================
set "CHOICE=1"
set /p "CHOICE=Pilih mode [1-5 / 0=Keluar, Enter=1]: "

if "%CHOICE%"=="1" goto mode_api
if "%CHOICE%"=="2" goto mode_web
if "%CHOICE%"=="3" goto mode_fullstack
if "%CHOICE%"=="4" goto mode_opencv
if "%CHOICE%"=="5" goto mode_apk
if "%CHOICE%"=="0" exit /b 0
echo [WARN] Pilihan tidak valid: %CHOICE%
timeout /t 2 >nul
goto menu

:: ============================================================================
:: [1] SERVER API ANDROID (FASTAPI + BINARY WEBSOCKET)
:: ============================================================================
:mode_api
echo.
echo ====================================================================
echo [MODE 1] SKELIO SERVER API + WEBSOCKET ^(UNTUK HP ANDROID^)
echo ====================================================================
call :detect_python "cv2, ultralytics, fastapi, uvicorn" "opencv-python ultralytics fastapi uvicorn websockets"
if errorlevel 1 goto end_pause

echo.
echo [*] Alamat Server IP untuk dimasukkan di aplikasi HP Android:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do for /f "tokens=1" %%b in ("%%a") do echo     ws://%%b:8000/ws/pose
echo     ws://127.0.0.1:8000/ws/pose  ^(jika via kabel USB + adb reverse^)
echo.
echo [*] Interpreter : %PY_CMD%
echo [*] Memuat model AI YOLOv11 ^& server WebSocket di port 8000...
echo [TIPS] Tekan CTRL+C untuk menghentikan server.
echo ====================================================================
echo.
%PY_CMD% -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
goto end_pause

:: ============================================================================
:: [2] APLIKASI WEB UI BARU ALL-IN-ONE (FLASK + VITE BUILD DI PORT 5000)
:: ============================================================================
:mode_web
echo.
echo ====================================================================
echo [MODE 2] SKELIO UNIFIED WEB APP ^(AI + REACT UI DI PORT 5000^)
echo ====================================================================
call :detect_python "cv2, ultralytics, flask" "opencv-python ultralytics flask"
if errorlevel 1 goto end_pause

call :ensure_frontend_dist
if errorlevel 1 goto end_pause

set "WEB_MODE=%ARG2%"
if "%WEB_MODE%"=="" (
    echo   [1] Buka di Browser Standar ^(http://localhost:5000 - Default^)
    echo   [2] Buka sebagai Jendela Aplikasi Mandiri ^(Edge/Chrome App Window^)
    echo.
    set "WEB_MODE=1"
    set /p "WEB_MODE=Pilih tampilan [1-2, Enter=1]: "
)

if "%WEB_MODE%"=="2" goto run_web_app_window

echo [*] Menjalankan SKELIO All-in-One di http://localhost:5000...
echo [TIPS] Tekan CTRL+C di jendela ini untuk mematikan aplikasi.
%PY_CMD% apps\web\app.py
goto end_pause

:run_web_app_window
set "APP_BROWSER="
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" set "APP_BROWSER=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not defined APP_BROWSER if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "APP_BROWSER=C:\Program Files\Google\Chrome\Application\chrome.exe"

if not defined APP_BROWSER (
    %PY_CMD% apps\web\app.py
    goto end_pause
)

echo [*] Menjalankan server Flask ^& membuka Jendela Aplikasi Mandiri...
echo [TIPS] Tekan CTRL+C di jendela ini untuk mematikan server.
start "" cmd /c "timeout /t 2 /nobreak >nul & start """" ""%APP_BROWSER%"" --app=http://localhost:5000 --window-size=460,860"
%PY_CMD% apps\web\app.py --no-browser
goto end_pause

:: ============================================================================
:: [3] FULLSTACK DEVELOPER MODE (FLASK :5000 + VITE DEV SERVER :5173)
:: ============================================================================
:mode_fullstack
echo.
echo ====================================================================
echo [MODE 3] SKELIO FULLSTACK DEV ^(FLASK :5000 + VITE HMR :5173^)
echo ====================================================================
call :detect_python "cv2, ultralytics, flask" "opencv-python ultralytics flask"
if errorlevel 1 goto end_pause

call :ensure_node_modules
if errorlevel 1 goto end_pause

echo [*] Menyalakan Backend Flask ^& Model YOLOv11 di jendela terpisah...
start "SKELIO Backend AI (:5000)" cmd /k "cd /d ""%~dp0"" && %PY_CMD% apps\web\app.py --no-browser"

echo [*] Menunggu backend siap ^(2 detik^)...
timeout /t 2 /nobreak >nul

echo [*] Menyalakan Frontend Vite UI di http://localhost:5173 ...
echo [TIPS] Tekan CTRL+C untuk menghentikan Vite ^(dan tutup jendela Backend AI jika selesai^).
start "" cmd /c "timeout /t 2 /nobreak >nul & start """" http://localhost:5173"
call npm.cmd run dev
goto end_pause

:: ============================================================================
:: [4] OPENCV DESKTOP (LIVE WEBCAM / DEMO VIDEO)
:: ============================================================================
:mode_opencv
echo.
echo ====================================================================
echo [MODE 4] SKELIO OPENCV DESKTOP PIPELINE
echo ====================================================================
call :detect_python "cv2, ultralytics" "opencv-python ultralytics torch"
if errorlevel 1 goto end_pause

set "CV_OPT=%ARG2%"
if "%CV_OPT%"=="" (
    echo   [1] Live Webcam Laptop ^(Real-Time^)
    echo   [2] Demo Video Push-Up ^(assets_sempro\raw_push-up_sample.mp4^)
    echo   [3] Demo Video Squat   ^(assets_sempro\raw_squat_sample.mp4^)
    echo.
    set "CV_OPT=1"
    set /p "CV_OPT=Pilih sumber [1-3, Enter=1]: "
)

if "%CV_OPT%"=="1" goto mode_cam_run
if "%CV_OPT%"=="2" set "ARG2=1" & goto mode_demo
if "%CV_OPT%"=="3" set "ARG2=2" & goto mode_demo
goto mode_cam_run

:mode_cam_direct
call :detect_python "cv2, ultralytics" "opencv-python ultralytics torch"
if errorlevel 1 goto end_pause

:mode_cam_run
echo [*] Interpreter : %PY_CMD%
echo [TIPS] Tombol: 1=Push-Up, 2=Squat, 3=Sit-Up, A=Auto, R=Reset, Q=Keluar
echo.
%PY_CMD% biomechanical_pipeline.py
goto end_pause

:mode_demo
call :detect_python "cv2, ultralytics" "opencv-python ultralytics torch"
if errorlevel 1 goto end_pause

set "DEMO_OPT=%ARG2%"
if "%DEMO_OPT%"=="" set "DEMO_OPT=1"

set "VIDEO_FILE=assets_sempro\raw_push-up_sample.mp4"
if /I "%DEMO_OPT%"=="2"     set "VIDEO_FILE=assets_sempro\raw_squat_sample.mp4"
if /I "%DEMO_OPT%"=="squat" set "VIDEO_FILE=assets_sempro\raw_squat_sample.mp4"

if /I "%DEMO_OPT%"=="2" echo [TIPS] Tekan tombol keyboard '2' untuk mengaktifkan mode Squat jika belum otomatis.
if /I "%DEMO_OPT%"=="squat" echo [TIPS] Tekan tombol keyboard '2' untuk mengaktifkan mode Squat jika belum otomatis.

echo [*] Memutar evaluasi video: %VIDEO_FILE%
%PY_CMD% biomechanical_pipeline.py "%VIDEO_FILE%"
goto end_pause

:: ============================================================================
:: [5] UTILITAS APK ANDROID (INSTALL USB ADB / BUILD GRADLE)
:: ============================================================================
:mode_apk
echo.
echo ====================================================================
echo [MODE 5] SKELIO ANDROID APK TOOL ^(BARE REACT NATIVE^)
echo ====================================================================

set "APK_OPT=%ARG2%"
if "%APK_OPT%"=="" (
    echo   [1] Pasang Release APK ke HP via Kabel USB ^(adb install + reverse^)
    echo   [2] Build Ulang Release APK Mandiri ^(assembleRelease arm64-v8a^)
    echo   [3] Build Debug APK ^(assembleDebug arm64-v8a^)
    echo.
    set "APK_OPT=1"
    set /p "APK_OPT=Pilih aksi [1-3, Enter=1]: "
)

if /I "%APK_OPT%"=="1"       goto apk_install
if /I "%APK_OPT%"=="install" goto apk_install
if /I "%APK_OPT%"=="2"       goto apk_build_release
if /I "%APK_OPT%"=="release" goto apk_build_release
if /I "%APK_OPT%"=="build"   goto apk_build_release
if /I "%APK_OPT%"=="3"       goto apk_build_debug
if /I "%APK_OPT%"=="debug"   goto apk_build_debug
echo [ERROR] Pilihan APK tidak dikenal: %APK_OPT%
goto end_pause

:apk_install
set "ADB_CMD=adb"
where adb >nul 2>nul
if errorlevel 1 if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" set "ADB_CMD=%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"

set "APK_PATH=apps\mobile-rn\android\app\build\outputs\apk\release\app-arm64-v8a-release.apk"
if not exist "%APK_PATH%" (
    echo [ERROR] File Release APK belum ditemukan di:
    echo         %APK_PATH%
    echo Silakan pilih opsi [2] terlebih dahulu untuk melakukan Build Release APK.
    goto end_pause
)

echo [*] Memeriksa koneksi perangkat Android via USB...
"%ADB_CMD%" devices
echo [*] Memasang %APK_PATH% ke HP...
"%ADB_CMD%" install -r "%APK_PATH%"
if errorlevel 1 (
    echo [GAGAL] Instalasi APK gagal. Pastikan kabel USB terhubung ^& USB Debugging aktif.
    goto end_pause
)
echo [*] Mengaktifkan port forwarding USB ^(adb reverse tcp:8000 tcp:8000^)...
"%ADB_CMD%" reverse tcp:8000 tcp:8000 >nul 2>nul
echo [OK] APK berhasil terpasang! Gunakan ws://127.0.0.1:8000/ws/pose ^(USB^) atau IP Wi-Fi laptop.
goto end_pause

:apk_build_release
set "GRADLE_TASK=assembleRelease"
goto apk_run_gradle

:apk_build_debug
set "GRADLE_TASK=assembleDebug"
goto apk_run_gradle

:apk_run_gradle
if exist "C:\Program Files\Android\Android Studio\jbr\bin\java.exe" (
    set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
    set "PATH=C:\Program Files\Android\Android Studio\jbr\bin;%PATH%"
)
echo [*] Menjalankan Gradle Task: %GRADLE_TASK% ^(arm64-v8a^)...
pushd "%~dp0apps\mobile-rn\android"
call gradlew.bat %GRADLE_TASK% --no-daemon -PreactNativeArchitectures=arm64-v8a
set "BUILD_EC=%ERRORLEVEL%"
popd
echo.
if "%BUILD_EC%"=="0" (
    echo [OK] Build selesai! Cek folder output di:
    echo      apps\mobile-rn\android\app\build\outputs\apk\
) else (
    echo [GAGAL] Build berakhir dengan exit code %BUILD_EC%.
)
goto end_pause

:: ============================================================================
:: MODE VERIFIKASI NON-INTERAKTIF (run_skelio.bat check)
:: ============================================================================
:mode_check
call :detect_python "cv2, ultralytics, flask, fastapi, uvicorn" "opencv-python ultralytics flask fastapi uvicorn"
if errorlevel 1 exit /b 1
echo [CHECK OK] Launcher SKELIO v3.3 siap. Interpreter: %PY_CMD%
exit /b 0

:: ============================================================================
:: HELPER: PASTIKAN NODE_MODULES & DIST FRONTEND SIAP
:: ============================================================================
:ensure_node_modules
if exist "node_modules\vite\dist\node\cli.js" exit /b 0
if exist "node_modules\vite\package.json" (
    echo [*] Mendeteksi node_modules tidak lengkap, membersihkan ulang...
    rmdir /s /q "node_modules" 2>nul
)
echo [*] Melengkapi dependensi frontend Vite ^(npm install^)...
call npm.cmd install
if errorlevel 1 (
    echo [ERROR] Gagal menjalankan npm install. Pastikan Node.js terpasang.
    exit /b 1
)
exit /b 0

:ensure_frontend_dist
call :ensure_node_modules
if errorlevel 1 exit /b 1
if exist "dist\index.html" exit /b 0
echo [*] Membangun tampilan UI React baru ke folder dist/ ^(npm run build^)...
call npm.cmd run build
if errorlevel 1 (
    echo [ERROR] Gagal melakukan build frontend Vite.
    exit /b 1
)
exit /b 0

:: ============================================================================
:: HELPER: DETEKSI INTERPRETER PYTHON TERPUSAT
:: ============================================================================
:detect_python
set "REQ_MODS=%~1"
set "PIP_PKGS=%~2"
set "PY_CMD="
py -3.11 -c "import %REQ_MODS%" >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD python -c "import %REQ_MODS%" >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD py -3.10 -c "import %REQ_MODS%" >nul 2>nul && set "PY_CMD=py -3.10"
if defined PY_CMD exit /b 0

echo.
echo [ERROR] Tidak ditemukan Python dengan library wajib: %REQ_MODS%
echo Jalankan perintah berikut di terminal untuk memasang dependensi:
echo     python -m pip install %PIP_PKGS%
echo.
exit /b 1

:end_pause
echo.
pause
exit /b 0
