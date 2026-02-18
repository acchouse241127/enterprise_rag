# 改好 .env 后执行此脚本，使新环境变量同步到正在运行的容器（无需重建镜像）
# 用法：在 PowerShell 中于 enterprise_rag 目录下执行 .\apply_env.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "[错误] 未找到 .env，请先复制 .env.example 为 .env 并填写 LLM_API_KEY 等" -ForegroundColor Red
    exit 1
}

Write-Host "[apply_env] 正在根据当前 .env 重建后端与前端容器，使新配置生效..." -ForegroundColor Cyan
docker compose --profile full up -d --force-recreate backend frontend

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 执行失败，请确认 Docker Desktop 已运行" -ForegroundColor Red
    exit 1
}

Write-Host "[apply_env] 已生效。后端会重新读取 .env（含 LLM_API_KEY）。" -ForegroundColor Green
