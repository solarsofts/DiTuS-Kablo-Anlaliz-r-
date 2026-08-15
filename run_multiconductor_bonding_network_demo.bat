@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo .venv bulunamadi. Once setup_venv.bat calistirin.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "examples\run_multiconductor_bonding_network_demo.py"
if errorlevel 1 (
  echo Demo basarisiz.
  pause
  exit /b 1
)
pause
