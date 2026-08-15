@echo off
setlocal
set "ROOT=%~dp0"
if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo Once setup_venv.bat must be run first.
  exit /b 1
)
"%ROOT%.venv\Scripts\python.exe" "%ROOT%examples\run_workflow_demo.py"
endlocal
