# 企业级 RAG 迭代详细建议

**日期**: 2026-03-05  
**基于**: 全项目梳理 + 二代/三代差距分析 + 现有 V2.0 计划  
**目标**: 在不急于上线的前提下，给出可执行的阶段与任务清单，先闭环第二代再分阶段引入第三代能力。

---

## 一、当前项目状态小结

### 1.1 技术栈与结构

| 层级 | 技术/结构 | 说明 |
|------|-----------|------|
| 后端 | FastAPI + SQLAlchemy + PostgreSQL | `backend/app/`，无 LangChain/LlamaIndex |
| 前端 | Streamlit (`frontend/`) + React SPA (`frontend_spa/`) | 双前端；SPA 为 Vite + React + Radix + Tailwind |
| 向量 | ChromaDB | `app/rag/vector_store.py`，collection 前缀 `kb` |
| 检索主路径 | `QaService.ask` / `stream_ask` | 向量 + KeywordRetriever（对向量候选按词重叠重排）→ 去重 → Reranker |
| 增强管道 | `HybridRetrievalPipeline` | BM25 + 向量 → RRF → 父文档 → Reranker → 自适应 → 去噪，**仅测试使用，未接入主 QA** |
| 验证 | VerifyPipeline | NLI、置信度、引用校验、拒答，已接在 ask/stream_ask |
| 配置 | `config.py` + `.env` | 策略名在 `retrieval_strategy.py` 为 smart/precise/fast/deep；config 默认仍为 `default` |

### 1.2 已具备的第二代能力

- 混合召回（向量 + KeywordRetriever 合并去重）、查询扩展（rule/llm/hybrid）、四档策略、Reranker、去重、VerifyPipeline、多轮对话、检索日志与反馈、检索看板。
- BM25、RRF、父文档、自适应、去噪、HybridRetrievalPipeline 已实现但未在主路径生效。

### 1.3 与「完整第二代」的主要差距（需在本建议中补齐）

1. **主路径未用 RRF/BM25/HybridPipeline**：当前为向量 + KeywordRetriever 简单并集，非 RRF 融合；真正 BM25 在 `bm25_retriever.py`，仅 HybridPipeline 使用。
2. **请求级 retrieval_mode 未生效**：API 传 `retrieval_mode`，`QaService.ask`/`stream_ask` 未接该参数，仅按策略决定是否用 keyword；写 log 时写死 `"hybrid"`。
3. **策略与配置不一致**：`config.retrieval_strategy` 为 `"default"`，策略名为 `smart/precise/fast/deep`；Schema 描述仍为 `default, high_recall, high_precision, low_latency`。
4. **无按 KB 的默认策略**：KnowledgeBase 有 `chunk_*`、`parent_retrieval_mode` 等，无 `default_retrieval_strategy`。
5. **无检索评估体系**：无 Recall@K、MRR 等固定 QA 集与回归。
6. **引用展示**：有 CitationPopover，答案内 span 级高亮与跳转未对齐「引用快照」体验。

---

## 二、迭代阶段总览

| 阶段 | 目标 | 建议周期 | 与上线关系 |
|------|------|----------|------------|
| **阶段 0** | 第二代结构闭环 | 1～2 迭代 | 上线前建议完成 |
| **阶段 1** | 低侵入第三代（评估 + 可观测） | 1～2 迭代 | 可与阶段 0 部分并行 |
| **阶段 2** | 高侵入第三代（多租户/生命周期） | 按需排期 | 不急于上线可延后 |
| **阶段 3** | 扩展型（意图/Agent） | 按需 | 可选 |

---

## 三、阶段 0：第二代结构闭环（详细任务）

目标：主路径与文档/对标描述一致，高级选项生效，配置统一，为后续评估与三代打基础。

### 3.1 主路径接入 RRF 或 HybridPipeline（P0）

**现状**：主路径为向量 + KeywordRetriever 按 chunk_id 并集 → 去重 → Reranker；RRF、BM25、父文档、自适应、去噪仅在 `HybridRetrievalPipeline` 中，且该管道为 async、未被 QA 调用。

**方案 A（推荐：主路径用 RRF，暂不接父文档/自适应/去噪）**

- 在 `qa_service.py` 的检索逻辑中：
  - 若策略为 hybrid（或 retrieval_mode 为 hybrid）：
    - 调用 `BM25Retriever.search(kb_id, query, top_k)`（需注入 BM25Retriever，依赖 PostgreSQL + pg_jieba）；
    - 调用现有 `VectorRetriever.retrieve(kb_id, query, top_k)`；
    - 使用 `RRFFusion.fuse()` 将两路结果融合，再 `_apply_dedup`、`_apply_reranker`。
  - 若为 vector-only：仅向量 + 去重 + Reranker。
- 涉及文件：`backend/app/services/qa_service.py`、`backend/app/api/deps.py`（若需注入 BM25Retriever）、`backend/app/rag/bm25_retriever.py`（确认接口与同步调用方式）。
- 注意：`HybridRetrievalPipeline.retrieve` 为 async，若希望直接复用，需在 sync 的 ask 中用 `asyncio.run()` 或线程池执行 async，或为 HybridPipeline 增加同步封装；否则采用方案 A 仅接 RRF 更简单。

**方案 B（完整复用 HybridPipeline）**

- 在 `deps.py` 中构造 `HybridRetrievalPipeline`（BM25、Vector、RRF、Parent、Adaptive、Denoiser、Reranker），通过依赖注入给 QA 路由或 QaService。
- QaService 在检索阶段改为调用该管道的 `retrieve()`；若管道为 async，需在 sync 中 `loop.run_until_complete` 或把 ask 改为 async 并让 FastAPI 支持 async 路由。
- 需从请求或 KB 中传入 `parent_retrieval_mode`、`dynamic_expand_n` 等（KnowledgeBase 表已有部分字段）。

**验收**：主路径在「混合」策略下产生 BM25 + 向量两路结果并经 RRF 融合；日志/看板可区分 retrieval_mode（见下）。

### 3.2 请求级 retrieval_mode 与策略覆盖生效（P1）

- 在 `QaService.ask()` 和 `QaService.stream_ask()` 的签名中增加参数：`retrieval_mode: Literal["vector", "bm25", "hybrid"] | None = None`。
- 逻辑：若 `retrieval_mode` 非空，则覆盖策略中的默认行为（例如强制 vector-only 或强制 hybrid）；否则沿用 `strat.retrieval_mode` / `strat.keyword_enabled`。
- API 层已传 `payload.retrieval_mode`，只需在 `qa_service.py` 中接收并传入 `ask`/`stream_ask`，并在写 `_log_retrieval` 时使用实际使用的 mode（请求覆盖或策略默认），不再写死 `"hybrid"`。
- 同步修正：
  - `config.py`：`retrieval_strategy` 默认值改为 `"smart"`（或保留 `"default"` 且在文档中明确等价于 smart）。
  - `schemas/qa.py`：`QaAskRequest.strategy` 的 description 改为 `"smart, precise, fast, deep"`。

**涉及文件**：`backend/app/services/qa_service.py`、`backend/app/api/qa.py`（确认传参）、`backend/app/config.py`、`backend/app/schemas/qa.py`。

**验收**：前端高级选项选择「仅向量」时，仅走向量检索；选择「混合」时走 RRF（在 3.1 完成后）；检索日志中 `retrieval_mode` 为实际使用值。

### 3.3 按知识库的默认检索策略（P2）

- 在 `KnowledgeBase` 模型上增加可选字段：`default_retrieval_strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)`（如 `smart`/`precise`/`fast`/`deep`）。
- 迁移：新增 migration 添加该列，默认 NULL。
- 列表/详情接口：在返回 KB 信息时包含 `default_retrieval_strategy`；创建/更新 KB 的 API 支持写入该字段（若产品需要）。
- 前端：进入某 KB 的问答页时，若该 KB 有 `default_retrieval_strategy`，则策略选择器默认选中该项；请求仍可被用户覆盖。

**涉及文件**：`backend/app/models/knowledge_base.py`、`backend/migrations/`、`backend/app/services/knowledge_base_service.py`、`backend/app/schemas/`（KB 的 response/request）、前端 KB 详情/问答页与 API 类型。

**验收**：为某 KB 设置默认策略后，在该 KB 下打开问答默认显示并采用该策略。

### 3.4 引用展示对齐「引用快照」（P2）

- 后端：流式/非流式响应中，citations 已含 chunk 信息；若需答案内 span 级对应，可在生成阶段或后处理中输出每个 citation 对应的答案片段区间（如 start/end 或 mark 列表），供前端高亮。
- 前端：在答案渲染时，根据 citation 与 span 信息将 `[ID:x]` 渲染为可点击的引用标记，点击展开 CitationPopover 或跳转到原文位置（若有文档预览页）。

**涉及文件**：`backend/app/rag/pipeline.py` 或生成结果构造处、`frontend_spa/src/components/qa/ChatMessage.tsx` 及引用渲染逻辑、`api/types.ts`（Citation 类型若需扩展）。

**验收**：用户可见答案内引用高亮/可点，与来源快照一一对应。

---

## 四、阶段 1：低侵入第三代（评估 + 可观测）

目标：建立可重复的检索与生成质量评估，以及成本与延迟的可观测性，不改变现有多租户与数据模型。

### 4.1 检索评估基线（Recall@K / MRR）

- 新增模块（如 `backend/app/eval/` 或 `backend/scripts/eval/`）：
  - **固定 QA 集**：JSON/YAML 结构，每项含 `question`、`expected_chunk_ids` 或 `expected_document_ids`（至少一种），可选 `knowledge_base_id`。
  - **检索评估脚本**：对每条 question 调用当前检索管线（仅检索，不调用 LLM），得到 chunk 列表；计算 Recall@K（如 K=5）、MRR；输出每条与汇总指标。
- 可选：在 CI 或定期任务中跑该脚本，与阈值比较（如 Recall@5 ≥ 某值），不通过则告警或阻塞发布。
- 不依赖多租户；可先单 KB、少量题目，再扩展。

**涉及**：新建 `backend/app/eval/` 或 `scripts/eval_retrieval.py`、`backend/tests/fixtures/` 下样例 QA 集、README 或 docs 中说明如何添加题目与跑评估。

**验收**：命令行可跑出 Recall@5、MRR；结果可写文件或打日志。

### 4.2 生成与业务指标（与 VerifyPipeline 结合）

- 在现有 `retrieval_log` 或单独表中，聚合「验证通过率、拒答率、引用准确率」等（按日/按 KB 或按应用）；若暂无应用维度可先按全局或 KB。
- 可选：简单看板或 API（如 `/api/metrics/quality`）返回近期聚合结果，供内部查看趋势。
- 与固定 QA 集结合：对同一 QA 集跑「检索 + 生成」，记录答案与验证结果，用于回归（如禁止通过率明显下降）。

**涉及**：`retrieval_log` 或新表、`RetrievalLogService` 或新 service、可选的前端看板或 API。

**验收**：能查到近期验证通过率/拒答率；可选地跑 QA 集生成并记录结果。

### 4.3 可观测与成本（时延分解、用量）

- **时延分解**：在 `qa_service` 与检索/重排/LLM 各阶段已部分打点；补全并统一字段（如 `retrieval_ms`、`rerank_ms`、`llm_ms`、`verify_ms`），写入 `retrieval_log` 或现有 metrics，并暴露到 Prometheus（若已有）。
- **用量与成本**：按请求记录 token 用量（若 LLM 返回）或估算；按 KB 或按用户聚合；可选地写配置中的「预算」或告警（如某 KB 日调用超量）。
- 不要求多租户；先按 `user_id` 或 `knowledge_base_id` 聚合即可。

**涉及**：`qa_service.py` 打点、`retrieval_log` 或 metrics 表/接口、`app/metrics.py` 或运维文档。

**验收**：单次请求可看到各阶段耗时；可查某 KB 或某用户的调用量与估算成本。

---

## 五、阶段 2：高侵入第三代（多租户与生命周期，概要）

- **多租户与权限**：显式租户/团队/应用模型、RBAC、审计、数据隔离；需动数据模型与大部分查询（加 tenant_id/scope）。建议单独排期、单独分支，与阶段 0/1 解耦。
- **生命周期**：流式接入、按文档类型切片配置、增量更新、任务调度；需新表与新服务。可在多租户稳定后再做，或先做「按类型切片」等单点能力。

不在本建议中展开具体任务清单；建议在阶段 0/1 稳定后再写「阶段 2 详细设计」。

---

## 六、阶段 3：扩展型（意图与 Agent，概要）

- **意图识别与路由**：在检索前对请求分类（FAQ 直答 / 知识库检索 / 拒答），不同路径不同策略；可先规则或轻量模型，再考虑 Ragent 等参考。
- **Agent / 多步检索 / 工具**：在主 RAG 外增加「规划 → 检索或工具 → 再检索 → 汇总」的环路；对现有检索与生成管道以扩展为主，改动相对可控。可按需排期。

---

## 七、建议执行顺序与优先级（不急于上线）

| 顺序 | 任务 | 阶段 | 说明 |
|------|------|------|------|
| 1 | 主路径接入 RRF（或 HybridPipeline） | 0 | 与文档/对标一致，检索质量可预期提升 |
| 2 | retrieval_mode 与策略覆盖 + config/schema 统一 | 0 | 高级选项生效，配置清晰 |
| 3 | 检索评估基线（Recall@K/MRR + 固定 QA 集） | 1 | 为后续优化与回归提供依据 |
| 4 | 按 KB 默认策略 | 0 | 体验优化，改动小 |
| 5 | 引用展示（span 高亮/跳转） | 0 | 体验与可信度 |
| 6 | 可观测与成本（时延、用量） | 1 | 运维与成本可控 |
| 7 | 生成/业务指标与简单看板 | 1 | 与 4.2 一致 |
| 8 | 多租户/生命周期/意图/Agent | 2/3 | 按需、单独设计 |

---

## 八、文件级清单（阶段 0 + 阶段 1）

| 任务 | 可能涉及的文件/目录 |
|------|---------------------|
| RRF 进主路径 | `backend/app/services/qa_service.py`、`backend/app/rag/rrf_fusion.py`、`backend/app/rag/bm25_retriever.py`、`backend/app/api/deps.py` |
| retrieval_mode 生效 | `backend/app/services/qa_service.py`、`backend/app/api/qa.py`、`backend/app/config.py`、`backend/app/schemas/qa.py` |
| 按 KB 默认策略 | `backend/app/models/knowledge_base.py`、migrations、`backend/app/services/knowledge_base_service.py`、KB 相关 schema、前端 KB/QA 页与 API |
| 引用展示 | `backend/app/rag/pipeline.py` 或生成构造处、`frontend_spa/src/components/qa/ChatMessage.tsx`、`api/types.ts` |
| 检索评估 | 新建 `backend/app/eval/` 或 `scripts/eval_retrieval.py`、fixtures、docs |
| 可观测/成本 | `backend/app/services/qa_service.py`、`backend/app/models/retrieval_log.py`、`backend/app/metrics.py`、检索日志服务与 API |

---

## 九、测试与文档建议

- **阶段 0**：为 RRF 主路径、retrieval_mode 覆盖、按 KB 策略增加单元或集成测试；更新 API 文档与「检索与配置」类文档（如 `V2.0_检索与配置汇总.md`）。
- **阶段 1**：评估脚本可纳入 CI 或定期任务；在 docs 中说明如何维护 QA 集与解读指标。
- 所有阶段：关键决策与接口变更记录在 `docs/` 或 `adr/`，便于后续多租户与三期规划时回溯。

---

## 十、总结

- **当前项目**已具备第二代大部分能力（混合召回、策略、验证、多轮、日志）；与「完整第二代」的差距集中在：主路径未用 RRF/BM25、请求级 retrieval_mode 未生效、配置与 schema 不统一、无按 KB 策略、无检索评估、引用展示可加强。
- **建议**：先完成阶段 0（结构闭环），再做阶段 1（评估 + 可观测）；多租户与生命周期作为阶段 2 单独排期；意图与 Agent 作为阶段 3 按需扩展。不急于上线时，可把阶段 0 和阶段 1 做扎实，再启动阶段 2 的详细设计。
- 本文档可与《RAG对标项目与迭代借鉴清单》《架构优化与评估报告_2026-03-03》及现有 V2.0 计划（B1/B2/B3）一起使用，作为迭代与排期的依据。

---

## 十一、执行进度更新（2026-03-06）

### 已验证完成的任务（代码已存在）

| 任务 | 状态 | 说明 |
|------|------|------|
| 主路径接入 RRF/HybridPipeline | ✅ 已完成 | `qa_service.py` hybrid 模式调用 `_retrieve_with_hybrid_pipeline()` |
| retrieval_mode 参数生效 | ✅ 已完成 | 完整链路：API → QaService → actual_retrieval_mode |
| 引用展示（[ID:x] 高亮/跳转） | ✅ 已完成 | `ChatMessage.tsx` + `CitationPopover.tsx` |
| Schema 描述统一 | ✅ 已完成 | `schemas/qa.py` 已更新为 smart/precise/fast/deep |
| 可观测时延分解 | ✅ 已完成 | `latency_breakdown` JSON 字段记录详细延迟 |
| VerifyPipeline 集成 | ✅ 已完成 | 已接入 ask/stream_ask，默认关闭 |

### 本次执行的修复（2026-03-06）

| 任务 | 状态 | 涉及文件 |
|------|------|----------|
| config 默认值修复 | ✅ 已完成 | `config.py`: "default" → "smart" |
| 评估脚本 hybrid 模式用 RRF | ✅ 已完成 | `scripts/eval_retrieval.py` |
| 按 KB 默认策略字段 | ✅ 已完成 | `models/knowledge_base.py`、`schemas/knowledge_base.py`、`services/knowledge_base_service.py`、`migrations/V2.0_009_add_kb_default_strategy.sql`、`main.py`、`frontend_spa/src/api/types.ts` |

### 待完成任务

| 任务 | 优先级 | 说明 |
|------|--------|------|
| QA 测试集标注 | P1 | `tests/fixtures/eval_qa_set.yaml` 的 expected_chunk_ids 需人工标注 |
| 前端 KB 设置页支持默认策略 | P2 | 需在 KB 创建/编辑页面添加策略选择器 |
| token 用量记录 | P2 | 可选，用于成本统计 |

