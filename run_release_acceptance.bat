@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [DiTuS] Sanal ortam bulunamadi. setup_venv.bat calistiriliyor...
  call setup_venv.bat
  if errorlevel 1 exit /b 1
)
set "PYTHONPATH=%CD%\src;%CD%"
set "SHARD_COUNT=8"
for /L %%I in (0,1,7) do (
  echo [DiTuS] Test shard %%I/%SHARD_COUNT%...
  ".venv\Scripts\python.exe" -m tools.run_release_acceptance --root "%CD%" --version 0.16.9.4.18 --shard-count %SHARD_COUNT% --run-shard-index %%I
  if errorlevel 1 (
    echo.
    echo [DiTuS] Test shard BASARISIZ: %%I
    pause
    exit /b 1
  )
)
".venv\Scripts\python.exe" -m tools.run_release_acceptance --root "%CD%" --version 0.16.9.4.18 --shard-count %SHARD_COUNT% --finalize-from-shards
if errorlevel 1 (
  echo.
  echo [DiTuS] Paket kabul kapilari BASARISIZ.
  pause
  exit /b 1
)
echo.
echo [DiTuS] Paket kabul kapilari BASARILI.
pause
