# Enterprise RAG System - 完整 Docker 部署脚本
# 用法：在 PowerShell 中执行 .\docker_full_deploy.ps1
# 首次构建约需 15-25 分钟，请耐心等待
#
# 环境在「容器启动时」从宿主机 .env 注入，不打进镜像。
# 若之后修改了 .env，重新执行本脚本或执行：
#   docker compose --profile full up -d --force-recreate
# 即可使新环境生效。

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Enterprise RAG - 完整 Docker 部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 .env 是否存在
if (-not (Test-Path ".env")) {
    Write-Host "[提示] 未找到 .env 文件，已从 .env.example 复制" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[重要] 请编辑 .env 文件，配置 LLM_API_KEY 和 JWT_SECRET_KEY" -ForegroundColor Yellow
    Write-Host ""
}

# 若存在冲突的旧容器，先移除
Write-Host "[0/2] 清理可能存在的冲突容器..." -ForegroundColor Gray
docker rm -f enterprise_rag_backend enterprise_rag_frontend 2>$null

Write-Host "[1/2] 正在构建并启动服务（postgres + chromadb + backend + frontend）..." -ForegroundColor Green
docker compose --profile full up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 部署失败，请检查 Docker Desktop 是否正常运行" -ForegroundColor Red
    Write-Host "若出现 502 Bad Gateway，可尝试重启 Docker Desktop 后重试" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[2/2] 等待服务就绪..." -ForegroundColor Green
Start-Sleep -Seconds 15

# 检查服务状态
Write-Host ""
Write-Host "当前容器状态：" -ForegroundColor Cyan
docker compose --profile full ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " 部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host " 前端: http://localhost:8501" -ForegroundColor White
Write-Host " 后端 API 文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host " 默认账号: admin / password123" -ForegroundColor White
Write-Host ""
