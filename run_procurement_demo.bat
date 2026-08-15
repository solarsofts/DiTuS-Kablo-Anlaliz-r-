@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" examples\run_procurement_demo.py
) else (
  python examples\run_procurement_demo.py
)
pause
