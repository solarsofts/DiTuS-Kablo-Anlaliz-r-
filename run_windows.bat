@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam bulunamadi. Kurulum baslatiliyor...
    call setup_venv.bat
    if errorlevel 1 exit /b 1
)

echo DiTuS Kablo Analizor baslatiliyor...
".venv\Scripts\python.exe" app.py
if errorlevel 1 (
    echo.
    echo Uygulama hata ile kapandi. Yukaridaki mesaji inceleyin.
    pause
    exit /b 1
)
exit /b 0
