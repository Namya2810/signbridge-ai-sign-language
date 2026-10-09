$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    py -3.12 -m venv (Join-Path $ProjectRoot ".venv")
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
Push-Location (Join-Path $ProjectRoot "ui")
try {
    npm install
} finally {
    Pop-Location
}

Write-Host "Setup complete. Run scripts\start.ps1 to launch SignBridge."
