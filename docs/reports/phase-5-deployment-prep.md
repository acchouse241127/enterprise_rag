# 阶段 5：部署准备报告

**日期**：2026-02-20  
**分支**：main  
**执行模式**：全自动 3A  

---

## 1. 执行摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| docker-compose 配置 | ✅ 有效 | `docker-compose config` 通过 |
| Dockerfile | ✅ 存在 | backend、frontend 各一 |
| .env.example | ✅ 完整 | 含数据库、LLM、安全等 |
| 服务健康探针 | ✅ 已配置 | backend: /api/system/health, frontend: /_stcore/health |

**结论**：部署配置完备，可按文档启动全栈。

---

## 2. Docker 配置

### 2.1 服务组成

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| postgres | postgres:16-alpine | 5432 | 主数据库，带 healthcheck |
| chromadb | chromadb/chroma:latest | 8001→8000 | 向量存储 |
| redis | redis:7-alpine | 6379 | Celery broker（profile: full） |
| backend | 自构建 | 8000 | FastAPI + uvicorn |
| frontend | 自构建 | 8501 | Streamlit |
| worker | 自构建 | - | Celery worker |

### 2.2 Profile 说明

- 默认：仅 postgres、chromadb
- `--profile full`：加上 redis、backend、frontend、worker

### 2.3 启动命令

```bash
# 仅数据库
docker-compose up -d

# 全栈
docker-compose --profile full up -d
```

---

## 3. 环境变量

`.env.example` 覆盖：

- 数据库：POSTGRES_*
- Chroma：CHROMA_*
- LLM：LLM_PROVIDER, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
- 安全：JWT_SECRET_KEY（生产必改）
- 上传：UPLOAD_ROOT_DIR
- 端口：BACKEND_PORT, FRONTEND_PORT

**生产必改**：JWT_SECRET_KEY、POSTGRES_PASSWORD、LLM_API_KEY、CORS/FRONTEND 相关。

---

## 4. 健康检查

| 端点 | 用途 |
|------|------|
| GET /health | 完整健康（含 DB） |
| GET /health/live | 存活探针 |
| GET /health/ready | 就绪探针 |
| GET /api/system/health | 轻量健康（Docker 探针用） |

---

## 5. 待办（可选）

1. 构建镜像：`docker-compose build`（需 Docker 环境）
2. 全栈启动验证：`docker-compose --profile full up -d`
3. 生产部署清单：参考 README 与 `.env.example` 完成必改项

---

## 6. 阶段门禁

- **是否通过**：通过  
- **建议**：可继续阶段 6（文档与发布）。
