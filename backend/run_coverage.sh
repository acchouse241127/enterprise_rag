#!/bin/bash
# Run pytest with coverage report

cd "$(dirname "$0")"

echo "Running tests with coverage..."

# Run unit tests with coverage
python -m pytest tests/ \
    -v \
    --tb=short \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=json \
    --ignore=tests/test_qa.py \
    --ignore=tests/test_phase2_integration.py \
    --ignore=tests/test_v2_e2e.py \
    --ignore=tests/e2e/ \
    -m "not integration and not slow and not llm"

echo ""
echo "Coverage report generated in htmlcov/ and coverage.json"
echo "Open htmlcov/index.html in browser for detailed report"
