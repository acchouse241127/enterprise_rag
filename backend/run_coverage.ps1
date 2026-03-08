# Run pytest with coverage report

$ErrorActionPreference = "Stop"

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Running tests with coverage..." -ForegroundColor Green

# Run unit tests with coverage
python -m pytest tests/ `
    -v `
    --tb=short `
    --cov=app `
    --cov-report=term-missing `
    --cov-report=html `
    --cov-report=json `
    --ignore=tests/test_qa.py `
    --ignore=tests/test_phase2_integration.py `
    --ignore=tests/test_v2_e2e.py `
    --ignore=tests/e2e/ `
    -m "not integration and not slow and not llm"

Write-Host ""
Write-Host "Coverage report generated in htmlcov/ and coverage.json" -ForegroundColor Cyan
Write-Host "Open htmlcov/index.html in browser for detailed report" -ForegroundColor Yellow
