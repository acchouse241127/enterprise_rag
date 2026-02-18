# Enterprise RAG 从 0 重塑 — 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有 enterprise_rag 基础上，按已确认设计落地：前端独立 SPA（方案二）、后端方案二（队列+解析/检索/RAG 增强+闭环），并为后端方案三预留空间；实现音频/视频/网址解析、检索与 RAG 三版组合、检索质量看板与联动、团队手工验收可执行。

**Architecture:** API（FastAPI）+ Worker（Celery/Redis 或等价）异步解析与向量化；解析/检索/RAG 按设计分阶段增强；前端独立 SPA 通过 REST + SSE 消费 API；数据层 PostgreSQL + ChromaDB，解析逻辑模块化预留独立服务。

**Tech Stack:** FastAPI, Redis, Celery（或 ARQ）, PostgreSQL, ChromaDB, React/Vue/Next（待定）, JWT, SSE

---

## 实施顺序与批次建议

- **批次 1**：后端 SPA 对接（CORS、鉴权约定、流式/错误契约）— 使 SPA 能调通现有 API。
- **批次 2**：队列与 Worker 基础（Redis + Celery、上传改为发任务、Worker 消费现有解析管线）— 解析异步化。
- **批次 3**：解析增强（音视频、网址、分块策略与模块化）— 新输入类型 + 预留方案三边界。
- **批次 4**：检索与 RAG 三版（多路召回、查询扩展、排序与策略、引用与可解释）— 按版一→版二→版三顺序。
- **批次 5**：闭环与看板（RetrievalLog/反馈扩展、看板聚合、联动）— 方案三端到端。
- **批次 6**：前端 SPA（技术栈选定、工程初始化、登录/知识库/文档/问答/看板/任务页、部署与 CI）— 方案二落地。
- **批次 7**：验收与发布（自动化清单、手工验收清单、验收报告模板、全量回归与发布门禁）— 可发布标准可执行。

**档三 LLM 策略**：档三（全面 LLM）先按**策略 A**（单模型多角色）实现；根据测试结果再决定是否拆成**策略 B**（多模型分工）。实施时预留策略 B 迭代空间：所有 LLM 调用经「按任务类型获取 provider」的抽象，配置预留按任务类型指定 model/endpoint 的扩展（见 Task 16a）。

以下按任务列出，每任务可拆为「写测试→跑失败→实现→跑通过→提交」等子步；执行时按 **executing-plans** 分批（建议每批 2～3 个任务），每批后报告并等待反馈。

---

### Task 1: 后端 — 添加 CORS 支持

**Files:**
- Modify: `backend/main.py`（在 create_app 内添加 CORSMiddleware）
- Test: `backend/tests/test_cors.py`（可选，或手工验证 SPA origin 可跨域）

**Step 1:** 在 `main.py` 中引入 `from fastapi.middleware.cors import CORSMiddleware`，在 `create_app()` 内、`include_router` 之前添加 `app.add_middleware(CORSMiddleware, allow_origins=[...], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])`，origins 先可配置为环境变量或占位列表（如 `["http://localhost:3000"]`）。

**Step 2:** 运行后端，用浏览器或 curl 从另一 origin 发预检请求，确认返回 `Access-Control-Allow-Origin` 等头。

**Step 3:** 提交：`feat(backend): add CORS for SPA`

---

### Task 2: 后端 — 鉴权与 SPA 约定（可选 refresh 或 /auth/me）

**Files:**
- Modify: `backend/app/api/auth.py`（若有现成用户信息接口则复用，否则新增 GET /auth/me 或等价）
- Docs: 在 `docs/` 或 OpenAPI 中注明：401 时前端应跳转登录；token 存内存或 localStorage 的约定

**Step 1:** 确认现有登录返回的 JWT 结构；若 SPA 需要「校验 token 并拉当前用户」，新增 `GET /api/auth/me`（或等价），依赖 get_current_user，返回当前用户 id/username 等非敏感信息。

**Step 2:** 编写该接口的单元测试或集成测试（需认证），运行通过。

**Step 3:** 提交：`feat(backend): add /auth/me for SPA token validation`

---

### Task 3: 后端 — 统一错误响应与生产不泄密

**Files:**
- Modify: `backend/app/core/exceptions.py` 或全局 exception handler：生产环境下 generic 异常不将 `str(exc)` 写入 response detail，仅返回通用 message + 可选 request_id
- Test: 现有或新增测试确保 500 时响应体格式一致

**Step 1:** 在 generic 异常处理中根据环境变量（如 `ENV=production`）判断，若为生产则 `detail=None` 或仅 `request_id`，详细内容只写日志。

**Step 2:** 运行测试，确认无回归。

**Step 3:** 提交：`fix(backend): do not leak exception detail in production`

---

### Task 4: 后端 — 引入 Redis 与 Celery（或 ARQ）依赖与配置

**Files:**
- Create/Modify: `backend/requirements.txt`（添加 redis, celery 或 arq）
- Create: `backend/app/core/celery_app.py`（或等价，定义 Celery app、broker=Redis URL）
- Modify: `backend/app/config.py`（增加 REDIS_URL、CELERY_BROKER 等配置项，从环境变量读取）

**Step 1:** 在 requirements 中加入 redis 与 celery（或 arq）；在 config 中增加配置项，默认可从 `.env` 读取。

**Step 2:** 编写 `celery_app.py`，broker 与 backend 指向 Redis；可空任务 `@app.task def noop(): pass`，运行 `celery -A app.core.celery_app worker --loglevel=info` 能启动即算通过。

**Step 3:** 提交：`chore(backend): add Redis and Celery (or ARQ) setup`

---

### Task 5: 后端 — 上传接口改为「写 Document 状态 + 发解析任务入队」

**Files:**
- Modify: `backend/app/services/document_service.py`（upload 内：写 Document 状态为 pending/uploaded，不入队同步解析；或入队后立即返回）
- Create: `backend/app/tasks/document_tasks.py`（定义 Celery task：接收 document_id，执行现有 parse→chunk→embed→upsert 逻辑，更新 Document 状态）
- Modify: `backend/app/api/document.py`（上传成功后调用 task.delay(document_id) 或等价）

**Step 1:** 将现有 `DocumentService.upload` 中「同步调用 parser.parse → chunk → embed → upsert」部分抽成可被 task 调用的函数（或保留在 service 内由 task 调用）。

**Step 2:** 在 document_tasks 中定义任务，接收 document_id，取 Document 与文件路径，执行解析与向量化，更新 status/parser_message。

**Step 3:** 在 upload API 中：写 Document 后发 `document_tasks.parse_and_index.delay(doc.id)`，返回 document 与 201；前端可轮询文档状态。

**Step 4:** 编写集成测试：上传文件后断言 Document 状态先为 pending/processing，Worker 消费后变为 vectorized（或失败状态）；或 mock 队列仅测 API 返回与入队调用。

**Step 5:** 提交：`feat(backend): async document parse via queue and worker`

---

### Task 6: 后端 — Docker Compose 增加 redis 与 worker 服务

**Files:**
- Modify: `docker-compose.yml`（增加 redis、worker 服务；worker 依赖 backend 与 redis，command 为 celery worker）
- Docs: README 或部署说明中更新「启动顺序」与「Worker 日志查看」

**Step 1:** 在 docker-compose 中添加 redis 与 worker；worker 使用 backend 镜像或同一构建，command 为 `celery -A app.core.celery_app worker ...`。

**Step 2:** 本地或 CI 中 `docker compose up -d redis worker`，上传文档后确认 worker 消费任务并更新状态。

**Step 3:** 提交：`chore(docker): add redis and celery worker to compose`

---

### Task 7: 后端 — 解析模块：音频格式支持（转写为文本）

**Files:**
- Create: `backend/app/document_parser/audio_parser.py`（实现 BaseDocumentParser，调用转写 API 或本地模型，返回文本）
- Modify: `backend/app/document_parser/__init__.py`（get_parser_for_extension 增加 .mp3/.wav/.m4a/.flac 等 → AudioParser）
- Modify: `backend/app/services/document_service.py` 或 task：允许上传音频扩展名；Worker 中调用新 parser

**Step 1:** 选定转写方案（如 Whisper API、本地 Whisper、或第三方）；实现 AudioParser.parse(path) -> str。

**Step 2:** 在 __init__ 中注册音频扩展名；在 upload 与 task 中允许这些扩展名并调用 parser。

**Step 3:** 编写单测：mock 转写结果，断言 parse 返回文本；集成测试可选（需真实文件或 fixture）。

**Step 4:** 提交：`feat(parser): add audio parser (transcribe to text)`

---

### Task 8: 后端 — 解析模块：视频格式支持（抽帧或字幕/转写）

**Files:**
- Create: `backend/app/document_parser/video_parser.py`（实现 BaseDocumentParser：抽关键帧+OCR 或抽字幕/转写音频，合并为文本）
- Modify: `backend/app/document_parser/__init__.py`（注册 .mp4/.webm/.mov 等）
- 同上：upload 与 task 支持视频扩展名

**Step 1:** 选定方案（如 ffmpeg 抽帧 + OCR，或抽字幕轨，或音轨转写）；实现 VideoParser.parse(path) -> str。

**Step 2:** 注册扩展名；upload/task 支持。

**Step 3:** 单测与必要集成测；提交：`feat(parser): add video parser`

---

### Task 9: 后端 — 解析模块：网址抓取与正文提取

**Files:**
- Create: `backend/app/document_parser/url_parser.py`（或 url_fetcher 服务：输入 URL，抓取 HTML，去噪提取正文，返回文本）
- Modify: API：增加「按 URL 创建文档」的接口（如 POST /documents/from-url），写 Document 元数据、发 task，task 内调用 url_parser 后分块向量化
- Modify: `backend/app/models/document.py` 或 schema：若需存 source_url 字段则增加

**Step 1:** 实现 URL 抓取与正文提取（可用 readability、goose3 或自研）；实现 UrlParser 或 fetch_url_to_text(url) -> str。

**Step 2:** 新增 API：接收 knowledge_base_id、url，创建 Document（类型为 url）、发 task；task 内 fetch 文本 → chunk → embed → upsert。

**Step 3:** 单测与集成测；提交：`feat(parser): add URL fetch and parse`

---

### Task 10: 后端 — 分块策略增强（语义边界与按类型策略）

**Files:**
- Modify: `backend/app/rag/chunker.py` 或新建 chunker 策略类：支持按句/段切分、按文档类型选择策略（长文/表格/对话）
- Modify: DocumentService 或 task：解析后根据 document 类型或配置选择 chunker 策略

**Step 1:** 设计 Chunker 接口或扩展现有 TextChunker：支持「按句/段」与「按字符窗口」两种模式；可选按 file_type 选择。

**Step 2:** 在解析管线中接入新 chunker；保留现有默认 800/100 兼容。

**Step 3:** 单测：给定文本，断言块边界与块数符合预期；提交：`feat(rag): chunker semantic boundary and strategy`

---

### Task 11: 后端 — 检索多路召回（向量 + BM25/关键词）

**Files:**
- Create: `backend/app/rag/keyword_retriever.py` 或集成现有全文检索（对 chunk 建索引或使用 PostgreSQL 全文检索）；在 RetrievalService 中：向量检索与关键词检索各取 top_k，合并去重后进 rerank
- Modify: `backend/app/services/qa_service.py` 或 retrieval_service：调用双路召回、融合、再去重与 rerank

**Step 1:** 实现关键词/BM25 一路（可先用简单 in-memory 或 SQL 全文检索，或 Elasticsearch 依选型）；接口与向量检索返回格式一致（list of chunk dict）。

**Step 2:** 在检索流程中：向量一路 + 关键词一路，按 doc_id+chunk_index 去重，合并列表后截断候选数，再进现有 rerank。

**Step 3:** 单测或集成测：给定 query，断言两路均有结果且融合去重正确；提交：`feat(retrieval): multi-path recall vector + keyword`

---

### Task 12: 后端 — 检索查询扩展（同义/改写 query）

**Files:**
- Create: `backend/app/rag/query_expansion.py`（规则或轻量 LLM 生成 1～3 个改写 query）
- Modify: 检索流程：对原始 query + 改写 query 分别做向量（及关键词）检索，结果合并去重后再 rerank

**Step 1:** 实现 query_expansion(query) -> list[str]；可选配置开关，默认可关闭以控延迟。

**Step 2:** 在检索入口调用 expansion，多 query 检索后合并去重。

**Step 3:** 单测与集成测；提交：`feat(retrieval): query expansion for recall`

---

### Task 13: 后端 — 检索多阶段排序与可配置策略

**Files:**
- Modify: `backend/app/services/qa_service.py`（在 rerank 后增加可选「规则排序」层：按 metadata 加权或过滤）
- Modify: `backend/app/config.py` 或知识库配置：增加「检索策略」预设（高召回/高精度/低延迟），对应 top_k、是否开 expansion、是否开 BM25 等
- Modify: API：问答接口支持传入 strategy 或使用知识库默认

**Step 1:** 定义策略枚举或配置结构；在检索流程中根据策略选择 top_k、是否 query_expansion、是否走关键词一路。

**Step 2:** 在 rerank 后增加 metadata 加权或过滤（如 chunk 类型、文档时间）；可选。

**Step 3:** 单测与集成测；提交：`feat(retrieval): configurable strategy and post-rerank rules`

---

### Task 14: 后端 — RAG 引用约束与可解释埋点

**Files:**
- Modify: `backend/app/rag/pipeline.py` 或 prompt：在 system 中明确「仅依据给定 context 的 ID 引用，关键结论带 [ID:x]」
- Modify: 返回给前端的 citations 结构：增加「为何命中」简短理由或匹配片段（可从 rerank 分数或 snippet 生成）
- Modify: RetrievalLog 或日志：记录最终入选 chunk、是否被 LLM 引用（若可解析回答中的 [ID:x]）

**Step 1:** 更新 RAG system prompt，强调引用规范；可选后处理校验回答中的 [ID:x] 是否均来自本次 chunk。

**Step 2:** 在 API 返回的 citations 中增加 reason 或 snippet 字段；RetrievalLog 扩展字段或单独表记录「引用情况」。

**Step 3:** 单测与集成测；提交：`feat(rag): citation constraint and explainable retrieval`

---

### Task 15: 后端 — 检索质量看板数据与反馈接口

**Files:**
- Modify: `backend/app/models/retrieval_log.py` 或反馈表：确保有 retrieval_log_id、满意度、是否采纳等字段
- Modify: API：检索反馈/满意度提交接口（若已有则扩展），看板聚合接口（按知识库/时间聚合检索量、平均候选数、rerank 后数量、满意度）
- Modify: 前端或后续 SPA：看板页消费聚合 API

**Step 1:** 确认 RetrievalLog 与 RetrievalFeedback 表结构满足看板维度（知识库、时间、用户、满意度）；若无则迁移增加字段。

**Step 2:** 实现 GET /api/retrieval/dashboard 或等价：按 kb_id、时间范围聚合指标；实现 POST /api/retrieval/feedback 或满意度接口。

**Step 3:** 单测或集成测；提交：`feat(backend): retrieval dashboard API and feedback`

---

### Task 16: 后端 — 为方案三预留（租户/限流/审计扩展点）

**Files:**
- Modify: `backend/app/models/` 或 config：在知识库/用户相关表中预留 `tenant_id` 或 `organization_id` 字段（可为 NULL），文档注明「ToB 多租户时启用」
- Create: `docs/plans/2026-02-18-backend-plan-three-reserved.md`（简短说明：限流按租户、审计日志接口预留，后续 ToB 就绪时接入）

**Step 1:** 在 knowledge_bases 或 users 表增加可选 tenant_id；迁移脚本；代码中查询暂不过滤 tenant（保持现有行为）。

**Step 2:** 在 config 或文档中列出「预留配置项」：如 RATE_LIMIT_PER_TENANT、AUDIT_LOG_ENABLED，默认关闭。

**Step 3:** 提交：`chore(backend): reserve tenant and audit for plan three`

---

### Task 16a: 后端 — LLM 按任务类型抽象与策略 B 预留

**目标**：先按策略 A（单模型）使用 LLM；在代码与配置上预留策略 B（按任务类型使用不同模型）的扩展空间，便于根据测试结果后续迭代。

**Files:**
- Modify: `backend/app/llm/__init__.py`（新增 `get_provider_for_task(task_type: str | None) -> BaseChatProvider`；内部默认使用现有 `build_chat_provider()` 逻辑；若配置中存在该 task_type 的 override，则用对应 model/base_url/api_key 构建 provider）
- Modify: `backend/app/config.py`（预留可选配置：如 `llm_task_overrides: dict[str, dict]` 或通过环境变量 `LLM_TASK_QA_MODEL`、`LLM_TASK_REWRITE_MODEL` 等读入；策略 A 下不配置即全部用默认 llm_*）
- Modify: `backend/app/services/qa_service.py`（将现有 `build_chat_provider()` 改为 `get_provider_for_task("qa")` 或 `get_provider_for_task("rag")`，保持行为一致）
- Docs: 在 `backend/app/llm/README.md` 或设计文档中列出预留的 task_type 枚举（qa / rewrite / summary / explain / grounding / session_summary / feedback / error_suggestion / suggest_question / follow_up / context_help / moderation 等），并说明策略 B 时如何配置 per-task 模型

**Step 1:** 在 config 中增加可选「按任务类型覆盖」的配置结构（例如 `llm_task_overrides` 或单列环境变量），默认空；文档说明策略 A 不填、策略 B 时按 task 填 model/base_url/api_key。

**Step 2:** 在 `app/llm/__init__.py` 中实现 `get_provider_for_task(task_type: str | None = None)`：无 override 或 task_type 不在 override 中时，调用现有 `build_chat_provider()` 返回默认 provider；有 override 时用该 task 的配置构建 provider（复用同一套 DeepSeek/OpenAI 等工厂逻辑）。

**Step 3:** 将 `qa_service` 中所有 `build_chat_provider()` 替换为 `get_provider_for_task("qa")`（或统一常量如 `TASK_QA`）；单测与集成测保持通过。

**Step 4:** 在文档中列出预留的 task_type 列表及策略 B 的配置示例；提交：`refactor(backend): LLM provider by task type with strategy-B reserve`

---

### Task 17: 前端 SPA — 技术栈选定与工程初始化

**Files:**
- Create: `frontend_spa/` 或独立仓库：使用 create-react-app / Vue CLI / create-next-app 等初始化项目；配置 API 基地址（环境变量）、代理或 CORS 说明
- Docs: `frontend_spa/README.md` 中说明如何启动、如何连接本地后端

**Step 1:** 选定 React+TypeScript 或 Vue3 或 Next.js；初始化工程；配置 `API_BASE_URL` 或 VITE_API_URL 等。

**Step 2:** 实现最小可运行页（如「Hello + 调用 GET /health」），确认能访问现有后端。

**Step 3:** 提交：`feat(frontend-spa): init project and API connection`

---

### Task 18: 前端 SPA — 登录页与鉴权

**Files:**
- Create: `frontend_spa/src/pages/Login.tsx`（或等价）：表单、调用 POST /api/auth/login、存储 token、跳转首页）
- Create: `frontend_spa/src/auth.ts`（或 store）：getToken、setToken、logout、请求头注入 Authorization）
- Modify: 全局请求封装：401 时清除 token 并跳转登录页

**Step 1:** 实现登录表单与调用；token 存 localStorage 或 memory；登录成功后跳转。

**Step 2:** 实现 axios/fetch 拦截器或封装：请求头带 Bearer token；响应 401 时跳转登录。

**Step 3:** 提交：`feat(frontend-spa): login and auth`

---

### Task 19: 前端 SPA — 知识库列表与文档上传页

**Files:**
- Create: 知识库列表页：调用 GET /api/knowledge-bases，展示列表；新建知识库表单调用 POST
- Create: 文档上传页：选择知识库、上传文件调用 POST /api/documents/upload、轮询或 WebSocket 查文档状态（待实现 task 状态接口若需）

**Step 1:** 知识库列表与创建；文档上传 multipart；上传后轮询 GET /api/documents/{id} 或列表接口查 status。

**Step 2:** 加载态与错误态统一（loading、err_network、err_business）；与设计规范一致。

**Step 3:** 提交：`feat(frontend-spa): knowledge base and document upload`

---

### Task 20: 前端 SPA — 问答页（流式 + 降级展示）

**Files:**
- Create: 问答页：知识库选择、输入框、调用 POST /api/qa/stream（SSE），用 fetch + ReadableStream 或 EventSource 消费流式响应；展示引用来源；当返回 llm_failed 时展示「仅检索结果」+ retrieved_chunks 列表
- 与现有 design_system 对齐：布局、颜色、反馈

**Step 1:** 实现流式请求与逐 token/逐段渲染；实现引用来源折叠或列表。

**Step 2:** 根据响应中 llm_failed 与 retrieved_chunks 展示降级 UI；重试按钮可选。

**Step 3:** 提交：`feat(frontend-spa): QA page with stream and fallback`

---

### Task 21: 前端 SPA — 检索质量看板与异步任务页

**Files:**
- Create: 看板页：调用 GET /api/retrieval/dashboard（或等价），展示图表或表格（按知识库、时间聚合）
- Create: 异步任务页：调用 GET /api/async-tasks 或任务列表接口，展示任务状态与进度
- 与 design_system 对齐

**Step 1:** 看板页与聚合 API 对接；异步任务页与现有 async_tasks API 对接。

**Step 2:** 提交：`feat(frontend-spa): dashboard and async tasks pages`

---

### Task 22: 验收 — 自动化与手工清单及报告模板

**Files:**
- Create: `docs/checklists/pre-release.md`（发布前检查清单：lint、单元测试、集成测试、安全/性能若已有；命令与顺序）
- Create: `docs/checklists/manual-acceptance.md`（手工验收清单：登录→知识库→上传→问答每步操作与预期）
- Create: `docs/templates/acceptance-report.md`（验收报告模板：版本、执行人、日期、自动化结果、手工结果、阻塞项）

**Step 1:** 编写 pre-release 清单与命令；编写 manual-acceptance 场景与预期。

**Step 2:** 编写验收报告模板；在 README 或发布流程中引用。

**Step 3:** 提交：`docs: add release checklist and acceptance template`

---

### Task 23: 发布前全量回归与门禁

**Files:**
- Modify: `scripts/run_regression.ps1` 或等价：确保包含「启动 redis + worker + backend + 前端（若已容器化）」及 pytest 全量
- Docs: 注明「发布前执行 run_regression 并通过手工验收清单、填写验收报告」

**Step 1:** 回归脚本覆盖当前所有服务（postgres、chromadb、redis、backend、worker、frontend 或 SPA）；pytest 全量通过。

**Step 2:** 文档注明发布门禁；提交：`chore: full regression and release gate`

---

## 执行说明

- 按 **executing-plans** 技能：每批执行 2～3 个任务，每批完成后报告「实现了什么」「验证命令与输出」，等待反馈后再进行下一批。
- 每任务内遵循 **test-driven-development**：能写测试的先写失败测试，再实现，再跑通过。
- 在声称「完成」前遵循 **verification-before-completion**：运行实际验证命令并贴出输出。
- 全部任务完成后使用 **finishing-a-development-branch**：验证测试通过 → 呈现合并/PR/保留/丢弃选项 → 执行用户选择。
