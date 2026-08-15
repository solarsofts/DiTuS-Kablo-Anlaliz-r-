@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [DiTuS] Sanal ortam bulunamadi. setup_venv.bat calistiriliyor...
  call setup_venv.bat
  if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 (
  echo.
  echo [DiTuS] Testler BASARISIZ.
  pause
  exit /b 1
)
echo.
echo [DiTuS] Tum testler BASARILI.
pause
