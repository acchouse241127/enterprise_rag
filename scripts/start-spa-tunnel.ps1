# 建立 SSH 反向隧道，使外网通过 VPS 访问本机 SPA 前端
# 使用前：复制 .env.tunnel.example 为 .env.tunnel，填写 TUNNEL_VPS_HOST 和 TUNNEL_VPS_USER

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $ProjectRoot) { $ProjectRoot = (Get-Location).Path }
Set-Location $ProjectRoot

$envFile = Join-Path $ProjectRoot ".env.tunnel"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($key, $val, 'Process')
        }
    }
}

$hostName = $env:TUNNEL_VPS_HOST
$userName = $env:TUNNEL_VPS_USER
$localPort = if ($env:TUNNEL_LOCAL_PORT) { $env:TUNNEL_LOCAL_PORT } else { "3000" }
$remotePort = if ($env:TUNNEL_REMOTE_PORT) { $env:TUNNEL_REMOTE_PORT } else { "10080" }

if (-not $hostName -or -not $userName) {
    Write-Host "未配置 VPS 信息。请：" -ForegroundColor Yellow
    Write-Host "  1. 复制 .env.tunnel.example 为 .env.tunnel"
    Write-Host "  2. 编辑 .env.tunnel，填写 TUNNEL_VPS_HOST 和 TUNNEL_VPS_USER"
    Write-Host "  3. 重新运行本脚本"
    exit 1
}

Write-Host "正在建立隧道: VPS ${remotePort} -> 本机 localhost:${localPort}" -ForegroundColor Cyan
Write-Host "连接 ${userName}@${hostName}，保持此窗口打开以维持隧道。按 Ctrl+C 退出。" -ForegroundColor Gray
& ssh -R "${remotePort}:localhost:${localPort}" -N -o ServerAliveInterval=60 "${userName}@${hostName}"
