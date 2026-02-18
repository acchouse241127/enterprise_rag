# Enterprise RAG System - Docker 全栈回归测试脚本 (Windows PowerShell)
# Author: C2
# Date: 2026-02-13
#
# 用法：
#   .\scripts\run_regression.ps1          # 运行全栈回归测试
#   .\scripts\run_regression.ps1 -Clean   # 清理后运行
#   .\scripts\run_regression.ps1 -Stop    # 仅停止服务

param(
    [switch]$Clean,
    [switch]$Stop,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Stop-Services {
    Write-Info "Stopping services..."
    docker compose --profile full down -v 2>$null
}

function Clear-Data {
    Write-Info "Cleaning data directories..."
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue data/postgres, data/vectors, data/uploads
}

function Start-Services {
    Write-Info "Starting full stack services..."
    docker compose --profile full up -d --build
    
    Write-Info "Waiting for services to be ready (60s)..."
    Start-Sleep -Seconds 60
}

function Test-Health {
    Write-Info "Running health checks..."
    
    # Backend health
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 10
        Write-Info "Backend: OK"
    } catch {
        Write-Err "Backend: FAILED"
        return $false
    }
    
    # Frontend health
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -TimeoutSec 10
        Write-Info "Frontend: OK"
    } catch {
        Write-Err "Frontend: FAILED"
        return $false
    }
    
    # ChromaDB health
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/heartbeat" -TimeoutSec 10
        Write-Info "ChromaDB: OK"
    } catch {
        Write-Err "ChromaDB: FAILED"
        return $false
    }
    
    Write-Info "All services healthy!"
    return $true
}

function Invoke-Tests {
    Write-Info "Running regression tests..."
    
    Set-Location backend
    
    # 运行测试
    python -m pytest tests/ -v `
        --ignore=tests/test_qa.py `
        --tb=short `
        -x
    
    $TestExitCode = $LASTEXITCODE
    Set-Location ..
    
    return $TestExitCode -eq 0
}

function Save-Logs {
    Write-Info "Collecting logs..."
    docker compose logs | Out-File -FilePath "regression_logs.txt" -Encoding UTF8
    Write-Info "Logs saved to regression_logs.txt"
}

# 主流程
function Main {
    if ($Help) {
        Write-Host @"
Usage: .\run_regression.ps1 [-Clean] [-Stop] [-Help]

Options:
  -Clean  Clean data before running
  -Stop   Stop services only
  -Help   Show this help
"@
        return
    }
    
    if ($Stop) {
        Stop-Services
        return
    }
    
    if ($Clean) {
        Stop-Services
        Clear-Data
    }
    
    Write-Info "=== Enterprise RAG Full Stack Regression ==="
    
    # 启动服务
    Start-Services
    
    # 健康检查
    if (-not (Test-Health)) {
        Write-Err "Health check failed!"
        Save-Logs
        Stop-Services
        exit 1
    }
    
    # 运行测试
    $TestPassed = Invoke-Tests
    
    if ($TestPassed) {
        Write-Info "=== Regression PASSED ==="
        $Result = 0
    } else {
        Write-Err "=== Regression FAILED ==="
        Save-Logs
        $Result = 1
    }
    
    # 清理
    Stop-Services
    
    exit $Result
}

Main
