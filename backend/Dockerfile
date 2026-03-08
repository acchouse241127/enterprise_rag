# Enterprise RAG System - Backend Dockerfile
# Author: C2
# Date: 2026-02-13

FROM docker.m.daocloud.io/library/python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
# - libGL etc: for OpenCV/cv2 (PaddleOCR)
# - LibreOffice: for .doc/.ppt legacy format conversion (OPT-014)
#   Version: uses Debian distro default (e.g. 25.2.3 on bookworm/trixie);
#   to pin: apt-cache policy libreoffice-writer && add =<version> to package name
# Added retry logic for network stability
RUN apt-get update && \
    for i in 1 2 3; do \
        apt-get install -y --no-install-recommends --fix-missing \
            curl \
            libpq-dev \
            gcc \
            libgl1 \
            libgl1-mesa-dri \
            libglib2.0-0 \
            libreoffice-writer \
            libreoffice-impress && break || sleep 10; \
    done && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/system/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
