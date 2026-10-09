$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$UiRoot = Join-Path $ProjectRoot "ui"

if (-not (Test-Path -LiteralPath (Join-Path $UiRoot "node_modules"))) {
    throw "Frontend dependencies not found. Run scripts\setup.ps1 first."
}

Push-Location $UiRoot
try {
    npm run dev -- --host 127.0.0.1
} finally {
    Pop-Location
}
