# Enterprise RAG System

企业知识库问答系统 - 基于 RAG（Retrieval-Augmented Generation）技术的智能问答平台。

## 功能特性

- **用户认证**：JWT + TOTP 双因素认证
- **知识库管理**：创建、编辑、删除知识库
- **文档处理**：支持 TXT、MD、PDF、DOC、DOCX、XLS、XLSX、PPT、PPTX、PNG、JPG、JPEG；单文件上限 200MB
- **智能问答**：基于知识库的 RAG 问答，支持流式输出、多轮对话
- **引用溯源**：回答自动标注来源文档和位置（`[ID:x]`）
- **文档重新解析**：支持对单文档重新解析并向量化，无需删除再传
- **QA 降级展示**：大模型不可用时仍可查看检索结果，并按来源文件展示便于查阅
- **Phase 2/3 增强**：Reranker、检索去重、动态阈值、RBAC、文档版本管理、文件夹同步、检索质量看板、用户反馈、异步任务、Prometheus/Grafana 监控、对话导出与分享、知识库在线编辑与分块调整

## 技术栈

- **后端**：FastAPI + SQLAlchemy + PostgreSQL
- **向量数据库**：ChromaDB（见下方「ChromaDB 部署方式」）
- **Embedding**：由 `EMBEDDING_MODEL_NAME` 配置，默认 `BAAI/bge-m3`；推荐轻量选项 `paraphrase-multilingual-MiniLM-L12-v2`（支持中文，sentence-transformers）
- **LLM**：DeepSeek / OpenAI / Gemini 等兼容接口（见 `.env`）
- **前端**：Streamlit

**用户使用手册**：[docs/用户使用手册.md](docs/用户使用手册.md)（登录、知识库、文档上传、RAG 问答及常见问题）

---

## 快速启动

### 前置要求

- Python 3.11+
- Docker Desktop
- LLM API Key（DeepSeek 或 OpenAI）

### 方式一：本地开发模式

```bash
# 1. 克隆项目并进入目录
cd enterprise_rag

# 2. 复制环境变量模板
# Windows PowerShell:
Copy-Item .env.example .env
# Linux/Mac:
# cp .env.example .env

# 3. 编辑 .env 文件，配置必要参数
# - JWT_SECRET_KEY：修改为随机字符串
# - LLM_API_KEY：填入你的 API Key

# 4. 启动数据库服务
docker compose up -d postgres chromadb

# 5. 等待数据库就绪（约 10 秒）

# 6. 启动后端
cd backend
pip install -r requirements.txt
python scripts/init_db.py  # 初始化数据库和测试账号
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 7. 新开终端，启动前端（侧边栏显示「系统介绍」，即首页详细内容）
cd frontend
pip install -r requirements.txt
streamlit run 系统介绍.py --server.port 8501
# 或双击 frontend/run.bat，或项目根目录执行: .\scripts\run_frontend.ps1
```

### 只重启后端（保持前端运行）

修改后端代码或 `.env` 后，若不想重启前端，可只重启后端：

**Windows PowerShell（项目根目录）：**
```powershell
.\scripts\restart_backend.ps1
```
脚本会结束占用 8000 端口的进程并在当前终端启动 uvicorn，前端（8501）不受影响。

**或手动：** 在后端终端 `Ctrl+C` 停掉 uvicorn，再执行 `cd backend && set PYTHONPATH=. && uvicorn main:app --host 0.0.0.0 --port 8000`。勿使用会结束所有 Python 进程的方式（否则会连前端一起关掉）。

### 方式二：Docker 完整部署

```bash
# 1. 复制并配置环境变量
Copy-Item .env.example .env
# 编辑 .env 文件配置 JWT_SECRET_KEY 和 LLM_API_KEY

# 2. 启动所有服务
docker compose --profile full up -d

# 3. 访问应用
# 前端：http://localhost:8501
# 后端 API 文档：http://localhost:8000/docs
```

---

## 默认账号

**以 `scripts/init_db.py` 为准**。初始化后可使用以下测试账号（执行 `python scripts/init_db.py` 创建）：

| 用户名 | 密码 | TOTP |
|--------|------|------|
| admin | password123 | 无 |
| admin_totp | password123 | 需要（用于 TOTP 绑定与验证测试） |

---

## 项目结构

```
enterprise_rag/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心模块（安全、数据库、日志）
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── services/       # 业务逻辑
│   │   ├── document_parser/# 文档解析器
│   │   ├── rag/            # RAG 组件
│   │   └── llm/            # LLM 提供者
│   ├── tests/              # 测试用例
│   ├── scripts/            # 脚本工具（如 init_db）
│   └── main.py             # 应用入口
├── frontend/               # 前端服务
│   ├── pages/              # Streamlit 页面
│   ├── 系统介绍.py         # 前端唯一入口（侧边栏显示「系统介绍」，即首页内容）
│   └── run.bat             # 双击启动前端（推荐）
├── scripts/                # 项目脚本
│   ├── restart_backend.ps1 # 仅重启后端（不杀前端）
│   └── ...
├── data/                   # 数据目录（自动创建）
│   ├── postgres/           # PostgreSQL 数据
│   ├── vectors/            # ChromaDB 向量
│   └── uploads/            # 上传文件
├── tests/                  # 集成测试
│   └── fixtures/           # 测试文件
├── docker-compose.yml      # Docker 编排
└── .env.example            # 环境变量模板
```

---

## API 文档

启动后端后访问：
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/knowledge-bases` | GET/POST | 知识库列表/创建 |
| `/api/knowledge-bases/{id}/documents` | POST | 上传文档 |
| `/api/documents/{id}/reparse` | POST | 重新解析并向量化文档 |
| `/api/qa/ask` | POST | 问答（同步）；LLM 不可用时返回检索结果及来源文件 |
| `/api/qa/stream` | POST | 问答（流式） |

---

## 配置说明

主要环境变量（`.env` 文件）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET_KEY` | JWT 密钥（**生产环境必须修改**） | please-change-me |
| `LLM_PROVIDER` | LLM 提供者 | deepseek |
| `LLM_API_KEY` | LLM API 密钥 | - |
| `LLM_BASE_URL` | LLM API 地址 | https://api.deepseek.com/v1 |
| `POSTGRES_PASSWORD` | 数据库密码 | enterprise_rag |
| `LOG_LEVEL` | 日志级别 | INFO |
| `EMBEDDING_MODEL_NAME` | 嵌入模型名（sentence-transformers） | BAAI/bge-m3 |
| `CHROMA_HOST` / `CHROMA_PORT` | ChromaDB 地址与端口（本地部署时） | localhost / 8001 |

### ChromaDB 部署方式

1. **Docker（推荐）**：在项目根目录执行 `docker compose up -d postgres chromadb`，ChromaDB 监听 **8001** 端口；后端通过 `CHROMA_HOST=localhost`、`CHROMA_PORT=8001` 连接（`.env` 默认即此）。
2. **本地安装**：若已通过 pip 等在本机安装 ChromaDB 并单独启动服务，需保证服务端口与 `.env` 中 `CHROMA_PORT` 一致；或使用 ChromaDB 客户端库直连时，需在代码/配置中指定相同地址与端口。  
两种方式二选一，后端仅通过 HTTP 与 ChromaDB 通信，不依赖 Docker 内网。

---

## 操作日志（便于测试与排查）

前端与后端的所有请求/操作（成功与失败）会写入**同一份日志文件**，便于排查问题：

- **路径**：`enterprise_rag/logs/operation.log`（项目根目录下 `logs/operation.log`）
- **内容**：
  - **BACKEND**：每条 API 请求的 method、path、query、client、status_code、duration_ms、success 等；未捕获异常会带堆栈
  - **FRONTEND**：每次前端发起的请求（登录、知识库列表、上传、下载、预览、问答等）的 operation、url、status_code、duration_ms、response_size、success 或 error
- **格式**：每行一条记录，带时间戳，可用文本编辑器或 `grep` 按时间、路径、状态码等筛选。

首次有请求或后端启动时会自动创建 `logs` 目录；若需长期保留日志，请注意该文件会持续追加，可定期归档或清空。

---

## 开发指南

### 运行测试

项目使用 pytest 进行测试，支持多种测试模式：

```bash
cd backend

# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行单元测试（无外部依赖，默认模式）
python -m pytest tests/ -v --ignore=tests/test_qa.py

# 运行集成测试（需要 Postgres + ChromaDB）
python -m pytest tests/ -v -m integration

# 运行全部测试（含覆盖率报告）
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# 运行特定测试文件
python -m pytest tests/test_document_version.py -v
```

#### 测试标记（Markers）

| 标记 | 说明 |
|------|------|
| `@pytest.mark.integration` | 集成测试，需要外部服务 |
| `@pytest.mark.slow` | 慢速测试 |
| `@pytest.mark.llm` | 需要 LLM API |

#### 环境依赖跳过

测试会自动检测外部服务可用性，不可用时自动跳过：

- **Postgres 不可用**：跳过数据库相关测试
- **ChromaDB 不可用**：跳过向量存储测试
- **LLM API 未配置**：跳过 LLM 相关测试

### Docker 全栈回归测试

```bash
# Linux/Mac
./scripts/run_regression.sh

# Windows PowerShell
.\scripts\run_regression.ps1

# 清理后运行
.\scripts\run_regression.ps1 -Clean

# 仅停止服务
.\scripts\run_regression.ps1 -Stop
```

### CI/CD

项目配置了 GitHub Actions CI，位于 `.github/workflows/ci.yml`：

- **lint**: 代码质量检查（ruff、black、isort）
- **unit-tests**: 单元测试（无外部依赖）
- **integration-tests**: 集成测试（使用 GitHub Actions services）
- **docker-build**: Docker 镜像构建测试
- **full-stack-regression**: 全栈回归（手动触发或 commit message 含 `[full-regression]`）

### 代码检查

```bash
pip install ruff black isort
ruff check backend/
black --check backend/
isort --check-only backend/
```

---

## 常见问题

### Q: ChromaDB 连接失败？
A: 确保 Docker 容器正常运行：`docker compose ps`，检查 chromadb 状态。

### Q: LLM 调用超时？
A: 检查 `LLM_API_KEY` 是否正确配置，网络是否能访问 API 地址。

### Q: 文档解析失败？
A: .doc、.ppt 旧格式需安装 LibreOffice（soffice）才能解析；未安装时请转换为 .docx、.pptx 后上传。其他格式（TXT、MD、PDF、DOCX、XLS、XLSX、PPTX、PNG、JPG、JPEG）均可正常解析。

### Q: .doc / .ppt 如何解析？
A: Docker 部署时镜像内已集成 LibreOffice，无需额外安装。本地开发需在 PATH 或常见路径安装 LibreOffice，解析时自动调用 soffice 转换为 .docx/.pptx。

### Q: 上传文件大小限制？
A: 单文件上限 200MB，超过将被拒绝。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v4.0.0 | 2026-02-14 | Phase 3 完成：异步任务、Prometheus/Grafana、对话导出分享、知识库在线编辑；单文件 200MB 限制 |
| v3.1.0 | 2026-02-13 | Phase 3.1: 文档版本管理、测试环境标准化 |
| v2.0.0 | 2026-02-13 | Phase 2 完成：检索去重、动态阈值、RBAC、监控 |
| v1.0.0 | 2026-02-13 | MVP 发布 |

---

## 许可证

MIT License

