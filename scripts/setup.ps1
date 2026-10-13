# Windows PowerShell 5.1+ setup: virtualenv, dependencies, Chromium.
# Usage (from anywhere):  .\scripts\setup.ps1
# If PowerShell blocks scripts, run once in this window:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

function Fail($message) {
    Write-Host "error: $message" -ForegroundColor Red
    exit 1
}

# Find a Python launcher: 'py' (python.org installer) or 'python'.
$python = $null
foreach ($candidate in @("py", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $python = $candidate; break }
}
if (-not $python) { Fail "Python not found. Install Python 3.9+ from python.org and tick 'Add to PATH'." }

& $python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
if ($LASTEXITCODE -ne 0) { Fail "Python 3.9 or newer is required (check: $python --version)." }

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment in .venv ..."
    & $python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Fail "Could not create the virtual environment." }
}

$venvPython = Join-Path $repo ".venv\Scripts\python.exe"

Write-Host "Updating pip ..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail "Could not update pip." }

# --only-binary: use prebuilt wheels only, so nothing is ever compiled and no
# C++ Build Tools are needed. If a wheel is missing, pip stops with a clear message.
Write-Host "Installing dependencies ..."
& $venvPython -m pip install --only-binary=:all: -r requirements.txt
if ($LASTEXITCODE -ne 0) { Fail "pip install failed (see the message above)." }

Write-Host "Installing Chromium for Playwright (about 150 MB, first time only) ..."
& $venvPython -m playwright install chromium
if ($LASTEXITCODE -ne 0) { Fail "playwright install failed." }

Write-Host ""
Write-Host "Setup done. Next:  .\scripts\run.ps1" -ForegroundColor Green
