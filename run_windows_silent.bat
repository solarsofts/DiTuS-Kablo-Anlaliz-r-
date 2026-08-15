@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    call setup_venv.bat
    if errorlevel 1 exit /b 1
)
start "DiTuS Kablo Analizor" ".venv\Scripts\pythonw.exe" app.py
