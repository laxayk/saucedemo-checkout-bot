# Windows PowerShell 5.1+ run script.
# Usage:
#   .\scripts\run.ps1                                   # standard_user, writes to outputs\
#   .\scripts\run.ps1 performance_glitch_user           # the slow user
#   .\scripts\run.ps1 standard_user --headed            # watch the browser
#   .\scripts\run.ps1 standard_user --out outputs\mine  # custom output folder
# The first argument is the username; everything after it goes to the bot.
# Credentials: uses SAUCE_PASSWORD if already set, otherwise the public demo
# password printed on saucedemo.com. Your environment variables are restored
# when the script ends, so nothing leaks into your next test.

param(
    [string]$User = "",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BotArgs
)

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$venvPython = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "error: .venv not found. Run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 2
}

# ".\run.ps1 --headed": the first token is a bot flag, not a username.
if ($User.StartsWith("--")) { $BotArgs = @($User) + $BotArgs; $User = "" }

if (-not $User) { $User = $env:SAUCE_USERNAME }
if (-not $User) { $User = "standard_user" }

$oldUser = $env:SAUCE_USERNAME
$oldPassword = $env:SAUCE_PASSWORD
$exitCode = 1
try {
    $env:SAUCE_USERNAME = $User
    if (-not $env:SAUCE_PASSWORD) { $env:SAUCE_PASSWORD = "secret_sauce" }  # public demo password

    $argList = @("-m", "saucebot", "--input", "input.json")
    if (-not ($BotArgs -contains "--out")) { $argList += @("--out", "outputs") }
    if ($BotArgs) { $argList += $BotArgs }

    & $venvPython @argList
    $exitCode = $LASTEXITCODE
}
finally {
    $env:SAUCE_USERNAME = $oldUser
    $env:SAUCE_PASSWORD = $oldPassword
}
exit $exitCode
