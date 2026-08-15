@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo .venv bulunamadi. Once setup_venv.bat calistirin.
  pause
  exit /b 1
)
set PYTHONPATH=%CD%\src
".venv\Scripts\python.exe" "examples\run_project_application_demo.py"
if errorlevel 1 (
  echo.
  echo Proje uygulama demosu BASARISIZ.
  pause
  exit /b 1
)
echo.
echo Proje uygulama demosu tamamlandi.
pause
