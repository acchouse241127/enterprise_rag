# V2.0 Docker 容器说明

## 一、必须的容器（由 docker-compose 管理）

当前 `docker-compose.yml` 使用 **profile: full** 时，以下容器为 V2.0 所需：

| 容器名 | 镜像 | 作用 | 端口 |
|--------|------|------|------|
| **enterprise_rag_postgres** | enterprise_rag_postgres:pg_jieba | PostgreSQL + pg_jieba（V2.0 中文全文检索） | 5432 |
| **enterprise_rag_chromadb** | chromadb/chroma:latest | 向量库 | 8001→8000 |
| **enterprise_rag_redis** | redis:7-alpine | Redis（Celery 队列/缓存） | 6379 |
| **enterprise_rag_backend** | enterprise_rag-backend | FastAPI 后端 API | 8000 |
| **enterprise_rag_frontend** | enterprise_rag-frontend | Streamlit 前端 | 8501 |
| **enterprise_rag_spa** | enterprise_rag-spa | React SPA 前端（可选） | 3000→80 |
| **enterprise_rag_worker** | enterprise_rag-worker | Celery 异步任务（文档解析等） | - |

**启动命令**（在项目根目录）：

```bash
docker compose --profile full up -d
```

---

## 二、多余的容器（可删除）

以下 3 个容器**不属于**当前 compose 编排，且已退出，可安全删除：

| 容器名 | 镜像 | 原因 |
|--------|------|------|
| **kind_goldberg** | postgres:16-alpine | 非 compose 创建；未配置 POSTGRES_PASSWORD，启动即退出。项目已用 enterprise_rag_postgres。 |
| **beautiful_hodgkin** | enterprise_rag-spa:latest | 旧/单独启动的 SPA 容器，不在 compose 网络中，nginx 无法解析 host "backend"，启动失败。 |
| **relaxed_lalande** | enterprise_rag-worker:latest | 旧/单独启动的 worker，未注入 POSTGRES_HOST=postgres，连 localhost:5432 被拒绝，启动失败。 |

**删除命令**：

```bash
docker rm kind_goldberg beautiful_hodgkin relaxed_lalande
```

若提示容器在运行，先停止再删：

```bash
docker stop kind_goldberg beautiful_hodgkin relaxed_lalande
docker rm kind_goldberg beautiful_hodgkin relaxed_lalande
```

---

## 三、当前运行状态与日志结论

- **enterprise_rag_postgres / chromadb / redis / backend / frontend**：由 compose 正常拉起，应保持运行。
- **enterprise_rag_spa / enterprise_rag_worker**：若需要 SPA 或异步任务，应由 compose 启动（`docker compose --profile full up -d`），不要单独运行旧镜像，否则会因网络或环境变量再次失败。
- **kind_goldberg / beautiful_hodgkin / relaxed_lalande**：均为多余，删除即可。

---

## 四、若需要 SPA 和 Worker

确保用 compose 统一启动，这样会使用正确网络与环境变量：

```bash
docker compose --profile full up -d
```

检查是否都起来：

```bash
docker compose --profile full ps
```
