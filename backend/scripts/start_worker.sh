#!/bin/bash
# Worker startup script - ensures dependencies before starting Celery
set -e

# Install missing dependencies (temporary fix until image is rebuilt)
pip install --quiet tiktoken 2>/dev/null || true

# Start Celery worker
exec celery -A app.core.celery_app worker --loglevel=info
