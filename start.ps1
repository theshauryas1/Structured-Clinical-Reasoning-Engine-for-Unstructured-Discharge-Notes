$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path "$root\frontend\dist\index.html")) {
    Push-Location "$root\frontend"
    try {
        npm install
        npm run build
    } finally {
        Pop-Location
    }
}

$port = if ($env:PORT) { $env:PORT } else { "8000" }
python -m uvicorn backend.main:app --host 0.0.0.0 --port $port
