@echo off
chdir /d "%~dp0"
echo 正在启动前端，侧边栏将显示「系统介绍」...
streamlit run 系统介绍.py --server.port 8501
pause
