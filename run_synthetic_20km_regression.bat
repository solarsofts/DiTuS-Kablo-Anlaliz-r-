@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo HATA: Sanal ortam bulunamadi. setup_venv.bat calistirin.
  exit /b 1
)
".venv\Scripts\python.exe" "examples\run_synthetic_20km_regression.py"
endlocal
