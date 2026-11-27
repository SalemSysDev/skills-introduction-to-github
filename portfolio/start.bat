@echo off
REM ============================================================
REM  Salem Makki Portfolio - one-click local start (Windows)
REM  Double-click this file. First run installs everything.
REM ============================================================
cd /d "%~dp0"
title Salem Makki Portfolio

REM Find a real Python 3 (the "python" command may be a Microsoft Store shortcut)
set "SYS_PY="
py -3 --version >nul 2>nul && set "SYS_PY=py -3"
if not defined SYS_PY (
  python --version >nul 2>nul && set "SYS_PY=python"
)
if not defined SYS_PY (
  echo.
  echo [!] Python 3 is not installed.
  echo     1. Install it from https://www.python.org/downloads/
  echo     2. During setup tick "Add Python to PATH"
  echo     3. Run this file again.
  start "" https://www.python.org/downloads/
  pause
  exit /b 1
)
echo Using: %SYS_PY%
%SYS_PY% --version

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating virtual environment...
  %SYS_PY% -m venv .venv || goto :error
)

set "PY=.venv\Scripts\python.exe"

if not exist "instance\.setup_done" (
  echo [2/4] Installing packages - this can take a minute...
  "%PY%" -m pip install --disable-pip-version-check -q -r requirements.txt || goto :error

  if not exist ".env" (
    "%PY%" -c "import secrets; open('.env','w').write('SECRET_KEY='+secrets.token_hex(32)+'\n')"
  )

  echo [3/4] Preparing the database and sample content...
  "%PY%" -m flask --app run init-db || goto :error
  "%PY%" -m flask --app run seed || goto :error

  echo.
  echo [4/4] Create your admin account for the dashboard.
  echo       The password must be at least 10 characters.
  echo       Characters are hidden while you type - this is normal.
  "%PY%" -m flask --app run create-admin || goto :error

  if not exist instance mkdir instance
  echo done> "instance\.setup_done"
)

echo.
echo ============================================================
echo   Website:    http://localhost:5000
echo   Dashboard:  http://localhost:5000/admin
echo   Keep this window open. Press Ctrl+C to stop.
echo ============================================================
start "" cmd /c "timeout /t 3 >nul & start http://localhost:5000"
"%PY%" -m flask --app run run
pause
exit /b 0

:error
echo.
echo [!] Something went wrong. Copy the red/error text above and send it.
pause
exit /b 1
