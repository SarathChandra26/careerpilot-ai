# CareerPilot AI — Initial Setup & Dependency Installer (Windows PowerShell)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   CareerPilot AI — Environment Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$baseDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $baseDir

# 1. Install / Update Python Requirements
Write-Host "[1/3] Installing Python Dependencies from requirements.txt..." -ForegroundColor Cyan
$reqFile = Join-Path $baseDir "requirements.txt"
if (Test-Path $reqFile) {
    python -m pip install --upgrade pip
    python -m pip install -r $reqFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install some dependencies. Please check terminal output." -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "requirements.txt not found!" -ForegroundColor Red
    exit 1
}

# 2. Ensure Required Directories Exist
Write-Host "[2/3] Setting Up Directory Structure..." -ForegroundColor Cyan
$dirs = @(
    (Join-Path $baseDir "storage"),
    (Join-Path $baseDir "storage\resumes"),
    (Join-Path $baseDir "data")
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Host "Created: $d" -ForegroundColor Green
    }
}

# 3. Generate Sample Job Records & Initialize Database
Write-Host "[3/3] Generating and Seeding Sample Job Opportunities..." -ForegroundColor Cyan
$sampleCsv = Join-Path $baseDir "data\sample_jobs.csv"
$genScript = Join-Path $baseDir "scripts\generate_sample_jobs.py"

if (Test-Path $genScript) {
    python $genScript
    Write-Host "Sample jobs catalogue verified!" -ForegroundColor Green
}

# Run database startup seeder
$env:PYTHONPATH = (Join-Path $baseDir "backend")
python -c "from app.database.session import init_db; init_db(); from app.main import seed_sample_data; from app.database.session import SessionLocal; db = SessionLocal(); seed_sample_data(db); db.close(); print('Database tables and seed data initialized successfully!')"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   CareerPilot AI Setup Complete!" -ForegroundColor Green
Write-Host "   You can now launch the system with: .\scripts\start.ps1" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
