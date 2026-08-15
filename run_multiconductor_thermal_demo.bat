@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" examples\run_multiconductor_thermal_demo.py
) else (
  python examples\run_multiconductor_thermal_demo.py
)
pause
