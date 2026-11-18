# CareerPilot AI — Ollama Model Downloader (Windows PowerShell)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   CareerPilot AI — Local LLM Model Downloader" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$modelName = "llama3.2:3b"

# Check if Ollama is installed
try {
    $ollamaVer = ollama --version 2>&1
    Write-Host "Detected Ollama: $ollamaVer" -ForegroundColor Green
} catch {
    Write-Host "[NOTICE] Ollama CLI is not found in your system PATH." -ForegroundColor Yellow
    Write-Host "To enable local LLM inference:" -ForegroundColor Gray
    Write-Host "  1. Download and install Ollama from https://ollama.com" -ForegroundColor Gray
    Write-Host "  2. Rerun this script after installation." -ForegroundColor Gray
    Write-Host ""
    Write-Host "NOTE: CareerPilot AI does NOT require Ollama to run!" -ForegroundColor Cyan
    Write-Host "It has an integrated offline deterministic fallback engine that executes all" -ForegroundColor Cyan
    Write-Host "agent tools, matching, search, and gap calculations completely offline." -ForegroundColor Cyan
    exit 0
}

# Check if Ollama service is running
Write-Host "Checking if Ollama service is active..." -ForegroundColor Cyan
try {
    $null = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "Ollama service is active on http://localhost:11434" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Ollama server does not appear to be running on port 11434." -ForegroundColor Yellow
    Write-Host "Attempting to start Ollama in the background..." -ForegroundColor Gray
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# Pull Model
Write-Host "Pulling default model: $modelName..." -ForegroundColor Cyan
Write-Host "This is a lightweight 3-billion parameter model (~2.0 GB) optimized for CPU." -ForegroundColor Gray

ollama pull $modelName

if ($LASTEXITCODE -eq 0) {
    Write-Host "Model '$modelName' downloaded and ready for CareerPilot AI!" -ForegroundColor Green
} else {
    Write-Host "Failed to pull model '$modelName'. Please verify your internet connection or Ollama service." -ForegroundColor Red
}
