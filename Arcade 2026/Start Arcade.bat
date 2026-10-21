@echo off
title IEEE Arcade (keep this window open)
cd /d "%~dp0"

rem First run downloads a private copy of Python (needs internet once). Later runs skip this.
powershell -NoProfile -ExecutionPolicy Bypass -File "system\setup_runtime.ps1"
if errorlevel 1 (
  echo.
  echo Setup could not finish. Connect this laptop to the internet and run Start Arcade again.
  pause
  exit /b 1
)

echo Starting the arcade. Close the arcade with Alt+F4.
"%LOCALAPPDATA%\IEEEArcade\python\python.exe" "system\server.py" %*
if errorlevel 1 pause
