@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" examples\run_catalog_comparison_demo.py
) else (
  py -3 examples\run_catalog_comparison_demo.py
)
if errorlevel 1 pause
endlocal
