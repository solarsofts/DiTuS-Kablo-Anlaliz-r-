@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" examples\run_electrothermal_coupled_demo.py
) else (
  python examples\run_electrothermal_coupled_demo.py
)
pause
