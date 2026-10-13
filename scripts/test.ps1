# Windows PowerShell 5.1+: run the test suite.
#   .\scripts\test.ps1           # all 9 tests (needs internet, uses saucedemo.com)
#   .\scripts\test.ps1 -UnitOnly # only the 4 fast unit tests
# Your environment variables are restored afterwards.

param([switch]$UnitOnly)

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$venvPython = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "error: .venv not found. Run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 2
}

& $venvPython -c "import pytest" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $venvPython -m pip install --disable-pip-version-check pytest
    if ($LASTEXITCODE -ne 0) { Write-Host "error: could not install pytest." -ForegroundColor Red; exit 1 }
}

$oldSkip = $env:SKIP_E2E
$exitCode = 1
try {
    if ($UnitOnly) { $env:SKIP_E2E = "1" } else { $env:SKIP_E2E = $null }
    & $venvPython -m pytest -q
    $exitCode = $LASTEXITCODE
}
finally {
    $env:SKIP_E2E = $oldSkip
}
exit $exitCode
