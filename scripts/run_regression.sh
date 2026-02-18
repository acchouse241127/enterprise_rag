#!/bin/bash
# Enterprise RAG System - Docker 全栈回归测试脚本
# Author: C2
# Date: 2026-02-13
#
# 用法：
#   ./scripts/run_regression.sh          # 运行全栈回归测试
#   ./scripts/run_regression.sh --clean  # 清理后运行
#   ./scripts/run_regression.sh --stop   # 仅停止服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止服务
stop_services() {
    log_info "Stopping services..."
    docker compose --profile full down -v 2>/dev/null || true
}

# 清理数据
clean_data() {
    log_info "Cleaning data directories..."
    rm -rf data/postgres data/vectors data/uploads 2>/dev/null || true
}

# 启动服务
start_services() {
    log_info "Starting full stack services..."
    docker compose --profile full up -d --build
    
    log_info "Waiting for services to be ready (60s)..."
    sleep 60
}

# 健康检查
health_check() {
    log_info "Running health checks..."
    
    # Backend health
    if curl -sf http://localhost:8000/api/health > /dev/null; then
        log_info "Backend: OK"
    else
        log_error "Backend: FAILED"
        return 1
    fi
    
    # Frontend health
    if curl -sf http://localhost:8501/_stcore/health > /dev/null; then
        log_info "Frontend: OK"
    else
        log_error "Frontend: FAILED"
        return 1
    fi
    
    # Postgres health
    if docker exec enterprise_rag_postgres pg_isready -U enterprise_rag > /dev/null 2>&1; then
        log_info "Postgres: OK"
    else
        log_error "Postgres: FAILED"
        return 1
    fi
    
    # ChromaDB health
    if curl -sf http://localhost:8001/api/v1/heartbeat > /dev/null; then
        log_info "ChromaDB: OK"
    else
        log_error "ChromaDB: FAILED"
        return 1
    fi
    
    log_info "All services healthy!"
}

# 运行测试
run_tests() {
    log_info "Running regression tests..."
    
    cd backend
    
    # 安装测试依赖（如果需要）
    pip install pytest pytest-asyncio httpx -q 2>/dev/null || true
    
    # 运行测试
    python -m pytest tests/ -v \
        --ignore=tests/test_qa.py \
        --tb=short \
        -x  # 遇到第一个失败就停止
    
    TEST_EXIT_CODE=$?
    cd ..
    
    return $TEST_EXIT_CODE
}

# 收集日志
collect_logs() {
    log_info "Collecting logs..."
    docker compose logs > regression_logs.txt
    log_info "Logs saved to regression_logs.txt"
}

# 主流程
main() {
    case "${1:-}" in
        --stop)
            stop_services
            exit 0
            ;;
        --clean)
            stop_services
            clean_data
            ;;
        --help|-h)
            echo "Usage: $0 [--clean|--stop|--help]"
            echo ""
            echo "Options:"
            echo "  --clean  Clean data before running"
            echo "  --stop   Stop services only"
            echo "  --help   Show this help"
            exit 0
            ;;
    esac
    
    log_info "=== Enterprise RAG Full Stack Regression ==="
    
    # 启动服务
    start_services
    
    # 健康检查
    if ! health_check; then
        log_error "Health check failed!"
        collect_logs
        stop_services
        exit 1
    fi
    
    # 运行测试
    if run_tests; then
        log_info "=== Regression PASSED ==="
        RESULT=0
    else
        log_error "=== Regression FAILED ==="
        collect_logs
        RESULT=1
    fi
    
    # 清理
    stop_services
    
    exit $RESULT
}

main "$@"
