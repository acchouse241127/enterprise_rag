# Enterprise RAG System - Frontend Dockerfile
# Author: C2
# Date: 2026-02-13

FROM python:3.11-slim

# Set environment variables（LC_ALL 保证容器内中文文件名 系统介绍.py 可正确解析）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check（start-period 拉长避免启动慢被误判不健康）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit（入口为 系统介绍.py，侧边栏显示「系统介绍」）
CMD ["streamlit", "run", "系统介绍.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
