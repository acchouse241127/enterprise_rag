# 启动前端（侧边栏显示「系统介绍」）
# 在项目根目录执行: .\scripts\run_frontend.ps1
$FrontendDir = Join-Path $PSScriptRoot ".." "frontend"
Set-Location $FrontendDir
streamlit run 系统介绍.py --server.port 8501
