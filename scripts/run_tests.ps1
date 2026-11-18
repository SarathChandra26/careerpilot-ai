# CareerPilot AI — Test & Evaluation Runner (Windows PowerShell)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   CareerPilot AI — Test Suite & Benchmarks" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$baseDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $baseDir

$backendDir = Join-Path $baseDir "backend"
$env:PYTHONPATH = $backendDir

# 1. Run Unit & Integration Tests
Write-Host "[1/2] Running Unit & Integration Test Suite (pytest)..." -ForegroundColor Cyan
python -m pytest "$backendDir\tests" -v

$testExit = $LASTEXITCODE
if ($testExit -ne 0) {
    Write-Host "[FAIL] Some pytest unit tests failed with code $testExit!" -ForegroundColor Red
} else {
    Write-Host "[PASS] All pytest test suites passed successfully!" -ForegroundColor Green
}

# 2. Run Evaluation Benchmarks
Write-Host ""
Write-Host "[2/2] Running Evaluation Benchmark Suite..." -ForegroundColor Cyan
python -m app.evaluation.benchmark_runner

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Testing and Benchmarking Completed!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
