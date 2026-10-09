$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python environment not found. Run scripts\setup.ps1 first."
}

Push-Location $ProjectRoot
try {
    & $Python -m uvicorn backend:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
