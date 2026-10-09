$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $PSScriptRoot "start-backend.ps1")
) -WorkingDirectory $ProjectRoot

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $PSScriptRoot "start-frontend.ps1")
) -WorkingDirectory $ProjectRoot

Write-Host "SignBridge is starting at http://127.0.0.1:5173"
