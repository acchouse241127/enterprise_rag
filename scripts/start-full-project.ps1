# Start full project (SPA + backend + DB) and optionally SSH tunnel for external access
# Usage: from repo root, run .\scripts\start-full-project.ps1
# Skip tunnel: .\scripts\start-full-project.ps1 -NoTunnel

param([switch]$NoTunnel)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $ProjectRoot) { $ProjectRoot = (Get-Location).Path }
Set-Location $ProjectRoot

Write-Host "Starting full stack (postgres, chromadb, redis, backend, spa, worker)..." -ForegroundColor Cyan
& docker compose --profile full up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Compose failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

$spaPort = 3000
if (Test-Path (Join-Path $ProjectRoot ".env")) {
    $envContent = Get-Content (Join-Path $ProjectRoot ".env") -Raw -Encoding UTF8
    if ($envContent -match 'SPA_PORT\s*=\s*(\d+)') { $spaPort = $matches[1] }
}

Write-Host "Waiting for SPA at localhost:$spaPort ..." -ForegroundColor Gray
$maxAttempts = 30
$attempt = 0
do {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$spaPort/" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { break }
    } catch {}
    $attempt++
} while ($attempt -lt $maxAttempts)

if ($attempt -ge $maxAttempts) {
    Write-Host "SPA not ready in time. Try later: http://localhost:$spaPort" -ForegroundColor Yellow
} else {
    Write-Host "Full project ready. Local: http://localhost:$spaPort" -ForegroundColor Green
}

if (-not $NoTunnel) {
    $envTunnel = Join-Path $ProjectRoot ".env.tunnel"
    $hasVps = $false
    if (Test-Path $envTunnel) {
        Get-Content $envTunnel -Encoding UTF8 | ForEach-Object {
            if ($_ -match '^\s*TUNNEL_VPS_HOST\s*=\s*(.+)$' -and $matches[1].Trim() -notmatch '^your-|^$') { $hasVps = $true }
        }
    }
    if ($hasVps) {
        Write-Host "Starting SSH tunnel (keep this window open)..." -ForegroundColor Cyan
        & (Join-Path $PSScriptRoot "start-spa-tunnel.ps1")
    } else {
        Write-Host ""
        Write-Host "For external access: copy .env.tunnel.example to .env.tunnel, set TUNNEL_VPS_HOST and TUNNEL_VPS_USER, then run .\scripts\start-spa-tunnel.ps1" -ForegroundColor Yellow
        Write-Host "Or use ngrok/cloudflared to expose port $spaPort. See docs/SPA external access doc." -ForegroundColor Yellow
        Write-Host ""
    }
}
