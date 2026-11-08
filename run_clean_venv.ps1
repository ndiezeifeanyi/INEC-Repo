# Clean virtual environment setup and test runner script for PowerShell
$ErrorActionPreference = "Stop"

Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Error "Python not found on PATH."
}

Write-Host "[2/4] Setting up .venv..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

Write-Host "[3/4] Installing pinned requirements from requirements.txt..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "[4/4] Executing test suite..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pytest tests/ -v

Write-Host "All steps executed successfully." -ForegroundColor Green

