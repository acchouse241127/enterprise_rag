# 仅重启后端（不杀前端）
# 用法: 在项目根目录执行 .\scripts\restart_backend.ps1
# 本脚本会结束占用 8000 端口的进程，然后在本终端启动后端（前端 8501 不受影响）

$ErrorActionPreference = "Stop"
$backendPort = 8000

# 查找占用 8000 端口的进程并结束
$conn = Get-NetTCPConnection -LocalPort $backendPort -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "正在结束占用端口 $backendPort 的进程 (PID: $($conn.OwningProcess)) ..."
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

$backendDir = Join-Path $PSScriptRoot "..\backend"
$env:PYTHONPATH = "."
Set-Location $backendDir
Write-Host "正在启动后端: http://localhost:$backendPort (前端未受影响，Ctrl+C 停止后端)"
uvicorn main:app --host 0.0.0.0 --port $backendPort
