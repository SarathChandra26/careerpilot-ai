# CareerPilot AI — Environment Verification Script (Windows PowerShell)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   CareerPilot AI — Environment Diagnostics" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check PowerShell Version
$psVersion = $PSVersionTable.PSVersion
Write-Host "[1/5] PowerShell Version: $psVersion" -ForegroundColor Green

# 2. Check Python Version
try {
    $pyVersionOutput = python --version 2>&1
    Write-Host "[2/5] Python Detected: $pyVersionOutput" -ForegroundColor Green
    
    # Check if 3.10+
    $match = [regex]::Match($pyVersionOutput, "Python (\d+)\.(\d+)")
    if ($match.Success) {
        $major = [int]$match.Groups[1].Value
        $minor = [int]$match.Groups[2].Value
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "  [WARNING] Python 3.10+ is recommended. Found: $pyVersionOutput" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  [ERROR] Python is not found in PATH! Please install Python 3.10+." -ForegroundColor Red
}

# 3. Check Pip Dependencies
Write-Host "[3/5] Checking Critical Python Packages..." -ForegroundColor Cyan
$packages = @("fastapi", "uvicorn", "pydantic", "sqlalchemy", "streamlit", "plotly", "requests", "pandas", "fitz", "docx")
$allInstalled = $true

foreach ($pkg in $packages) {
    $check = python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  + $pkg : Installed" -ForegroundColor Green
    } else {
        Write-Host "  - $pkg : MISSING" -ForegroundColor Red
        $allInstalled = $false
    }
}

if (-not $allInstalled) {
    Write-Host "  [ACTION REQUIRED] Run `.\scripts\setup.ps1` to install all missing dependencies." -ForegroundColor Yellow
}

# 4. Check Ollama Installation
Write-Host "[4/5] Checking Ollama Local LLM Engine..." -ForegroundColor Cyan
try {
    $ollamaVersion = ollama --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  + Ollama CLI Detected: $ollamaVersion" -ForegroundColor Green
        
        # Test HTTP API
        try {
            $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
            Write-Host "  + Ollama Service is running on http://localhost:11434" -ForegroundColor Green
            $models = $resp.models | ForEach-Object { $_.name }
            Write-Host "  + Available Local Models: $($models -join ', ')" -ForegroundColor Gray
            if ($models -contains "llama3.2:3b" -or $models -contains "llama3.2:latest") {
                Write-Host "  + Recommended default model (llama3.2:3b) is present!" -ForegroundColor Green
            } else {
                Write-Host "  [INFO] llama3.2:3b is not pulled yet. Run `.\scripts\download_models.ps1` to download." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  [INFO] Ollama is installed but not currently running on port 11434." -ForegroundColor Yellow
            Write-Host "         CareerPilot AI will seamlessly operate in Offline Deterministic Fallback mode." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [INFO] Ollama not found in PATH." -ForegroundColor Yellow
        Write-Host "         CareerPilot AI will operate in Offline Deterministic Fallback mode." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [INFO] Ollama executable not found. Offline Deterministic Fallback mode enabled." -ForegroundColor Yellow
}

# 5. Check Directory & Database Layout
Write-Host "[5/5] Checking Storage & Paths..." -ForegroundColor Cyan
$storagePath = Join-Path $PSScriptRoot "..\storage"
$dataPath = Join-Path $PSScriptRoot "..\data"

if (Test-Path $storagePath) {
    Write-Host "  + Storage Directory exists: $storagePath" -ForegroundColor Green
} else {
    Write-Host "  - Storage Directory missing, creating..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $storagePath | Out-Null
}

$dbPath = Join-Path $storagePath "careerpilot.db"
if (Test-Path $dbPath) {
    $size = (Get-Item $dbPath).Length / 1KB
    Write-Host "  + SQLite Database found: $dbPath ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "  [INFO] Database not yet created. It will initialize automatically on first startup." -ForegroundColor Cyan
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Environment Diagnostic Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
