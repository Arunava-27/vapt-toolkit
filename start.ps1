# VAPT Toolkit — start backend + frontend in separate windows
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
$venvActivate = Join-Path $venv "Scripts\Activate.ps1"

# --- venv setup (runs in this window so the user can see progress) ---
if (-not (Test-Path $venvPython)) {
    if (Test-Path $venv) {
        Write-Host ".venv exists but python.exe is missing — recreating..." -ForegroundColor Yellow
        Remove-Item $venv -Recurse -Force
    } else {
        Write-Host ".venv not found — creating virtual environment..." -ForegroundColor Yellow
    }
    python -m venv "$venv"
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: failed to create venv. Is Python installed?" -ForegroundColor Red; exit 1 }
    Write-Host "venv created. Installing dependencies..." -ForegroundColor Yellow
    & $venvPython -m pip install --quiet -r "$root\requirements.txt"
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: pip install failed." -ForegroundColor Red; exit 1 }
    Write-Host "Dependencies installed." -ForegroundColor Green
} else {
    Write-Host ".venv found." -ForegroundColor Green
}

# Backend — activate venv then run server (use modular server/main.py, not old server.py)
$backendCmd = "Set-Location '$root'; " +
    "Write-Host 'Activating venv...' -ForegroundColor Cyan; " +
    "& '$venvActivate'; " +
    "Write-Host 'Starting backend on http://localhost:8000  (Ctrl+C to stop)' -ForegroundColor Cyan; " +
    "python server\main.py; " +
    "Write-Host 'Backend stopped.' -ForegroundColor Yellow"
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-Command", $backendCmd

# Frontend
$frontendCmd = "Set-Location '$root\frontend'; " +
    "Write-Host 'Starting frontend on http://localhost:5173  (Ctrl+C to stop)' -ForegroundColor Green; " +
    "npm run dev; " +
    "Write-Host 'Frontend stopped.' -ForegroundColor Yellow"
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-Command", $frontendCmd

Write-Host ""
Write-Host "Both processes launched." -ForegroundColor Yellow
Write-Host "Backend : http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
