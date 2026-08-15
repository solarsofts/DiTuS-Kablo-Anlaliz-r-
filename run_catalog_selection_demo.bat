@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [DiTuS] Sanal ortam bulunamadi. Once setup_venv.bat calistirin.
  pause
  exit /b 1
)
set "PYTHONPATH=%CD%\src"
".venv\Scripts\python.exe" "examples\run_catalog_selection_demo.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo [DiTuS] Katalog aday demo calismasi basarisiz. Kod: %RC%
  pause
  exit /b %RC%
)
echo [DiTuS] Sonuc: examples\catalog_selection_results.latest.json
pause
endlocal
