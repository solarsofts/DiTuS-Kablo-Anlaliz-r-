@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" examples\run_multiconductor_em_demo.py
) else (
  py -3 examples\run_multiconductor_em_demo.py
)
pause
