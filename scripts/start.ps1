# CareerPilot AI — Application Launch Script (Windows PowerShell)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Starting CareerPilot AI System..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$baseDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $baseDir

$backendDir = Join-Path $baseDir "backend"
$frontendApp = Join-Path $baseDir "frontend\app.py"

# Set environment
$env:PYTHONPATH = $backendDir

Write-Host "[1/3] Starting FastAPI Backend on http://127.0.0.1:8005..." -ForegroundColor Cyan
$backendProc = Start-Process -FilePath "python" `
    -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8005" `
    -WorkingDirectory $baseDir `
    -PassThru

# Wait for backend health
Write-Host "[2/3] Waiting for Backend Health Check..." -ForegroundColor Cyan
$maxAttempts = 15
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    Start-Sleep -Seconds 1
    $attempt++
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8005/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($resp.status -eq "healthy" -or $resp.status -eq "degraded") {
            $backendReady = $true
            Write-Host "Backend is READY! Status: $($resp.status)" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "  ... waiting for backend (attempt $attempt/$maxAttempts)" -ForegroundColor Gray
    }
}

if (-not $backendReady) {
    Write-Host "[WARNING] Backend health check timed out. Attempting to start frontend anyway..." -ForegroundColor Yellow
}

Write-Host "[3/3] Launching Streamlit Frontend on http://localhost:8501..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   CareerPilot AI is live!" -ForegroundColor Green
Write-Host "   Frontend: http://localhost:8501" -ForegroundColor Yellow
Write-Host "   Backend API Docs: http://127.0.0.1:8005/docs" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate both servers when finished." -ForegroundColor Gray

try {
    streamlit run $frontendApp --server.port 8501 --server.headless false
} finally {
    Write-Host "Stopping FastAPI backend process (PID: $($backendProc.Id))..." -ForegroundColor Yellow
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "CareerPilot AI stopped safely." -ForegroundColor Green
}
