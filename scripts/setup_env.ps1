# O3 测试环境配置脚本（Windows PowerShell）
# 用途：一键完成 .env、Docker、依赖安装、数据库初始化，便于执行测试
# 使用：在项目根目录 enterprise_rag 下执行 .\scripts\setup_env.ps1

$ErrorActionPreference = "Stop"
# 脚本位于 enterprise_rag/scripts/，项目根为 enterprise_rag
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "========== 1/5 检查 .env ==========" -ForegroundColor Cyan
$envPath = Join-Path $ProjectRoot ".env"
$envExample = Join-Path $ProjectRoot ".env.example"
if (-not (Test-Path $envPath)) {
    Copy-Item $envExample $envPath
    Write-Host "已从 .env.example 复制生成 .env，请按需编辑 JWT_SECRET_KEY、LLM_API_KEY。" -ForegroundColor Yellow
} else {
    Write-Host ".env 已存在，跳过。" -ForegroundColor Green
}

Write-Host "`n========== 2/5 启动 Docker（PostgreSQL + ChromaDB）==========" -ForegroundColor Cyan
docker compose up -d postgres chromadb 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker 启动失败或未安装。请确保 Docker Desktop 已运行，并执行: docker compose up -d postgres chromadb" -ForegroundColor Red
} else {
    Write-Host "PostgreSQL、ChromaDB 已启动。" -ForegroundColor Green
}
Write-Host "等待 10 秒以便数据库就绪..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Write-Host "`n========== 3/5 安装后端依赖 ==========" -ForegroundColor Cyan
Set-Location (Join-Path $ProjectRoot "backend")
pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "后端依赖安装失败。" -ForegroundColor Red
    exit 1
}
Write-Host "后端依赖已安装。" -ForegroundColor Green

Write-Host "`n========== 4/5 安装前端依赖 ==========" -ForegroundColor Cyan
Set-Location (Join-Path $ProjectRoot "frontend_spa")
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "前端依赖安装失败。" -ForegroundColor Red
    exit 1
}
Write-Host "前端依赖已安装。" -ForegroundColor Green

Write-Host "`n========== 5/5 初始化数据库与测试账号 ==========" -ForegroundColor Cyan
Set-Location $ProjectRoot
python scripts/init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "init_db 失败，请确认 PostgreSQL 已启动且 .env 中数据库配置正确。" -ForegroundColor Red
    exit 1
}
Write-Host "数据库与测试账号已就绪（admin / password123，admin_totp / password123）。" -ForegroundColor Green

Write-Host "`n========== 环境配置完成 ==========" -ForegroundColor Green
Write-Host "后续可执行：" -ForegroundColor Cyan
Write-Host "  启动后端: cd backend; `$env:PYTHONPATH='.'; uvicorn main:app --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host "  启动前端: cd frontend_spa; npm run dev" -ForegroundColor Gray
Write-Host "  运行测试: cd backend; `$env:PYTHONPATH='.'; python -m pytest tests/ -v" -ForegroundColor Gray
Set-Location $ProjectRoot
