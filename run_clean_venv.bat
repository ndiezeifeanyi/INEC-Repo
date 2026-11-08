@echo off
REM Setup clean virtual environment, install pinned dependencies, and run test suite
setlocal enabledelayedexpansion

echo [1/4] Checking Python installation...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: python is not found on PATH.
    exit /b 1
)

echo [2/4] Creating virtual environment (.venv)...
if not exist ".venv" (
    python -m venv .venv
)

echo [3/4] Activating virtual environment and installing pinned dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [4/4] Running test suite...
python -m pytest tests/ -v

echo Done.

