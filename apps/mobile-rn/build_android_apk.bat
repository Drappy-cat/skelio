@echo off
title SKELIO v3.0 - Build Android APK (Bare React Native)
cd /d "%~dp0"

set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
set "PATH=%JAVA_HOME%\bin;%PATH%"

set "TASK=%1"
if "%TASK%"=="" set "TASK=assembleDebug"

echo ====================================================================
echo SKELIO v3.0: BUILD ANDROID APK (BARE REACT NATIVE - NO EXPO)
echo Task Gradle: %TASK% (arm64-v8a)
echo ====================================================================
echo.

:: Mapping sementara ke drive S: untuk menghindari batas MAX_PATH 260 karakter Windows pada CMake/Ninja
subst S: "%~dp0" >nul 2>nul
pushd S:\android
call gradlew.bat %TASK% --no-daemon -PreactNativeArchitectures=arm64-v8a
set "BUILD_EC=%ERRORLEVEL%"
popd
subst S: /D >nul 2>nul

echo.
if %BUILD_EC% equ 0 (
    echo [OK] Build selesai! Cek folder output di:
    echo      apps\mobile-rn\android\app\build\outputs\apk\
) else (
    echo [GAGAL] Build berakhir dengan exit code %BUILD_EC%.
)
pause
exit /b %BUILD_EC%
