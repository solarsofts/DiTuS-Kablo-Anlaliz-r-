@echo off
setlocal
cd /d "%~dp0"
if exist .venv (
    echo .venv klasoru siliniyor...
    rmdir /s /q .venv
)
echo Sanal ortam temizlendi.
pause
