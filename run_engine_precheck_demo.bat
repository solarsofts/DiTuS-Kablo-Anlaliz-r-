@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo .venv bulunamadi. Once setup_venv.bat calistirin.
  exit /b 1
)
set PYTHONPATH=%CD%\src
".venv\Scripts\python.exe" examples\run_engine_precheck_demo.py
endlocal
