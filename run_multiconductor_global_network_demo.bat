@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" examples\run_multiconductor_global_network_demo.py
) else (
  python examples\run_multiconductor_global_network_demo.py
)
pause
