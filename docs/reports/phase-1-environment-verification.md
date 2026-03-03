# 阶段 1：环境验证报告

**日期**：2026-02-20  
**分支**：main  
**执行模式**：全自动 3A  

---

## 1. 执行摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| 依赖安装 | ✅ 通过 | `pip install -r requirements.txt` 完成 |
| 单元测试 | ⚠️ 部分通过 | 纯逻辑测试通过，依赖 DB/Chroma 的测试失败 |
| 后端启动 | ❌ 失败 | Postgres 连接被拒绝 (localhost:5432) |
| 健康检查 | - | 后端未就绪，无法执行 |
| 前端启动 | 未执行 | 依赖后端 |

**结论**：环境验证在无 Postgres/Chroma 的当前环境下，依赖安装与纯单元测试可完成；后端与集成测试需要先启动 Postgres。

---

## 2. 依赖安装

- **命令**：`cd backend && pip install -r requirements.txt`
- **结果**：退出码 0，约 130 秒
- **说明**：所有依赖安装成功（含 fastapi、uvicorn、sqlalchemy、chromadb、sentence-transformers 等）

---

## 3. 单元测试

- **命令**：`python -m pytest tests/ -v`
- **总数**：117
- **通过**：约 85（chunker、dedup、document_parser、document_version 服务层、folder_sync、llm_provider 等）
- **错误**：约 32（auth、cors、document_version API、knowledge_base、performance、phase2_3_health 等）

**错误原因**：使用 `TestClient(app)` 时，应用 lifespan 会连接 Postgres；Postgres 未运行导致 `psycopg2.OperationalError: connection refused`。

**说明**：`pytest-cov` 未在 requirements.txt 中，未执行覆盖率收集。

---

## 4. 后端启动与健康检查

### 4.1 启动命令

- 文档写的是 `python main.py`，但 `main.py` 无 `if __name__ == "__main__"` 块
- 正确启动方式：`uvicorn main:app --host 0.0.0.0 --port 8000`

### 4.2 启动结果

- **命令**：`python -m uvicorn main:app --host 0.0.0.0 --port 8000`
- **错误**：应用 startup 阶段失败
  ```
  psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused
  connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
  ```
- **原因**：Postgres 未在本机 localhost:5432 监听

### 4.3 配置

- 默认：`postgres_host=localhost`, `postgres_port=5432`, `postgres_db=enterprise_rag`
- 可通过 `.env` 或环境变量覆盖（如 `POSTGRES_HOST`）

---

## 5. 待办与建议

1. **启动 Postgres**  
   - 使用 Docker：`docker run -d -p 5432:5432 -e POSTGRES_DB=enterprise_rag -e POSTGRES_USER=enterprise_rag -e POSTGRES_PASSWORD=enterprise_rag postgres:15`  
   - 或按项目文档启动本地 Postgres

2. **修正启动文档**  
   - 将 `python main.py` 改为 `uvicorn main:app --host 0.0.0.0 --port 8000`  
   - 或在 `main.py` 中加入 `if __name__ == "__main__"` 调用 uvicorn

3. **测试与覆盖率**  
   - 安装 `pytest-cov` 并加入 requirements.txt  
   - Postgres/Chroma 就绪后重跑全部测试并收集覆盖率

4. **前端验证**  
   - 后端健康检查通过后，启动 Streamlit 并执行 `docs/checklists/manual-acceptance-v2.md`

---

## 6. 阶段门禁

- **是否通过**：有条件通过  
  - 依赖与纯单元测试可完成  
  - 后端、集成测试需 Postgres/Chroma 运行
- **建议**：在 Postgres 可用环境中完成本阶段剩余项后，再进入阶段 2（代码审查）。
