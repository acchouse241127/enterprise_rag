# 生成测试覆盖率基线报告
# Usage: .\generate_coverage_baseline.ps1

$ErrorActionPreference = "Stop"

$BACKEND_DIR = "e:\Super Fund\enterprise_rag\backend"
$COVERAGE_FILE = "coverage_baseline.json"

Write-Host "Generating coverage baseline..." -ForegroundColor Cyan
Write-Host ""

# 切换到后端目录
Set-Location $BACKEND_DIR

# 运行测试并生成覆盖率
Write-Host "Running tests with coverage..." -ForegroundColor Yellow
$testCmd = "python -m pytest --cov=app --cov-report=json --cov-report=term-missing --ignore=tests/test_qa.py --ignore=tests/test_phase2_integration.py -q"

Invoke-Expression $testCmd

if ($LASTEXITCODE -eq 0) {
    # 备份覆盖率报告
    if (Test-Path "coverage.json") {
        Copy-Item -Path "coverage.json" -Destination $COVERAGE_FILE -Force
        Write-Host ""
        Write-Host "[SUCCESS] Coverage baseline saved to: $COVERAGE_FILE" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] coverage.json not found!" -ForegroundColor Red
        exit 1
    }

    # 分析覆盖率
    Write-Host ""
    Write-Host "Analyzing coverage..." -ForegroundColor Yellow
    $analyzeCmd = "python scripts\analyze_coverage.py"
    Invoke-Expression $analyzeCmd
} else {
    Write-Host "[ERROR] Tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
