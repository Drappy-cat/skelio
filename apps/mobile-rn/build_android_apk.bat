@echo off
title SKELIO v3.1 - Build Android APK (Bare React Native)
cd /d "%~dp0"

set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
set "PATH=%JAVA_HOME%\bin;%PATH%"

set "TASK=%1"
if "%TASK%"=="" set "TASK=assembleDebug"

echo ====================================================================
echo SKELIO v3.1: BUILD ANDROID APK (BARE REACT NATIVE - NO EXPO)
echo Task Gradle: %TASK% (arm64-v8a)
echo ====================================================================
echo.

pushd "%~dp0android"
call gradlew.bat %TASK% --no-daemon -PreactNativeArchitectures=arm64-v8a
set "BUILD_EC=%ERRORLEVEL%"
popd

echo.
if %BUILD_EC% equ 0 (
    echo [OK] Build selesai! Cek folder output di:
    echo      apps\mobile-rn\android\app\build\outputs\apk\
) else (
    echo [GAGAL] Build berakhir dengan exit code %BUILD_EC%.
)
pause
exit /b %BUILD_EC%
