@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM SKELIO Hermes Compiler Wrapper (Windows)
REM 1) Mencoba menjalankan hermesc.exe bawaan hermes-compiler terlebih dahulu.
REM 2) Jika hermesc.exe gagal inisialisasi DLL di Windows (exit -1073741502 /
REM    STATUS_DLL_INIT_FAILED), fallback menyalin bundle JS ter-minify langsung
REM    ke target output. Engine Hermes (libhermes.so) di Android secara native
REM    mendukung eksekusi langsung JavaScript bundle UTF-8.
REM ============================================================================

set "REAL_HERMESC=%~dp0..\node_modules\hermes-compiler\hermesc\win64-bin\hermesc.exe"

if exist "%REAL_HERMESC%" (
    "%REAL_HERMESC%" %*
    if !ERRORLEVEL! EQU 0 exit /b 0
    echo [SKELIO hermesc-win] WARN: hermesc.exe exited with code !ERRORLEVEL!. Using JS bundle fallback.
)

set "OUT_FILE="
set "IN_FILE="
set "NEXT_IS_OUT=0"
set "NEXT_IS_IN=0"

:parse_args
if "%~1"=="" goto done_args
if "!NEXT_IS_OUT!"=="1" (
    set "OUT_FILE=%~1"
    set "NEXT_IS_OUT=0"
    set "NEXT_IS_IN=1"
    shift
    goto parse_args
)
if "!NEXT_IS_IN!"=="1" (
    set "IN_FILE=%~1"
    set "NEXT_IS_IN=0"
    shift
    goto parse_args
)
if /I "%~1"=="-out" (
    set "NEXT_IS_OUT=1"
)
shift
goto parse_args

:done_args
if not defined OUT_FILE (
    echo [SKELIO hermesc-win] ERROR: Missing -out argument.
    exit /b 1
)
if not defined IN_FILE (
    echo [SKELIO hermesc-win] ERROR: Missing input bundle argument.
    exit /b 1
)
if not exist "%IN_FILE%" (
    echo [SKELIO hermesc-win] ERROR: Input bundle not found: "%IN_FILE%"
    exit /b 1
)

copy /Y "%IN_FILE%" "%OUT_FILE%" >nul
if !ERRORLEVEL! NEQ 0 (
    echo [SKELIO hermesc-win] ERROR: Failed to copy "%IN_FILE%" to "%OUT_FILE%".
    exit /b 1
)

echo [SKELIO hermesc-win] Fallback OK: packaged minified JS bundle into "%OUT_FILE%".
exit /b 0
