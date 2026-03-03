# 算法优化完整规划文档

> **日期**: 2026-03-03  
> **状态**: ✅ 已完成 (2026-03-03) 
> **开发方法**: TDD（先写测试 → 写代码 → 验证）  
> **Superpowers**: brainstorming → writing-plans → executing-plans  

---

## 一、需求调研结论

以下为 brainstorming 阶段的用户确认结果：

### 1.1 查询缓存

| 决策项 | 用户选择 |
|--------|---------|
| 缓存范围 | **检索结果 + LLM 答案**（两层） |
| 缓存匹配方式 | **先全文精确匹配，无命中再语义匹配**（混合模式） |
| 缓存 TTL | **可配置**，默认 24 小时 |
| 知识库更新时 | **需要主动清除相关缓存** |

### 1.2 降级策略

| 决策项 | 用户选择 |
|--------|---------|
| 降级场景 | **多级降级**（向量超时 → BM25；ChromaDB 不可用 → BM25；全部失败 → 错误） |
| 降级提示 | **必须返回降级原因和级别** |

### 1.3 PII 匿名化

| 决策项 | 用户选择 |
|--------|---------|
| 脱敏类型 | **手机号、身份证、银行卡、邮箱、地址、姓名 + 自定义正则** |

### 1.4 禁用词库

| 决策项 | 用户选择 |
|--------|---------|
| 词库管理 | **内置默认 + 自定义文件 + 数据库动态管理** |

### 1.5 Phase 2 增强功能

| 决策项 | 用户选择 |
|--------|---------|
| 自查询检索器 | **需要** |
| SPLADE 稀疏嵌入 | **需要，与 BM25 并存** |
| 领域微调 | **暂不需要** |

---

## 二、方案选型

采用 **方案 A：渐进式实现**：

- **Phase 1 先完成**：查询缓存、降级策略、PII 匿名化、禁用词库（基础设施）
- **Phase 2 后完成**：自查询检索器、SPLADE 检索器（增强功能）

---

## 三、背景与目标

### 3.1 当前算法评估结论

基于对 `enterprise_rag` 项目的算法评估，与业界最佳实践（`企业级rag系统的算法.md`）对比：

| 优化项 | 当前状态 | 目标状态 |
|--------|---------|---------|
| 查询缓存 | ❌ 无 | ✅ 两层缓存 + 混合匹配 |
| 降级策略 | ❌ 无 | ✅ 多级降级 + 提示 |
| PII 匿名化 | ❌ 无 | ✅ 正则 + 自定义规则 |
| 禁用词库 | ❌ 无 | ✅ 数据库管理 + API |
| 自查询检索器 | ❌ 无 | ✅ LLM 意图解析 |
| SPLADE 检索 | ❌ 无 | ✅ 与 BM25 并存 |

### 3.2 目标

1. **降低 LLM 调用成本**：缓存热门查询，预计减少 50%+ 调用  
2. **提升系统稳定性**：降级策略保障服务可用性  
3. **保障合规安全**：PII 脱敏 + 禁用词过滤  
4. **增强检索能力**：自查询 + SPLADE 提升召回率  

---

## 四、整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           QaService                                      │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        QueryCacheService                            │ │
│  │  L1: Exact Match (Redis) ──► L2: Semantic Match (Vector)          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼ Cache Miss                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     PiiAnonymizer (输入端)                          │ │
│  │  检测 + 替换 PII ──► 匿名化问题 ──► LLM                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                   RetrievalOrchestrator                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │ Vector       │  │ SPLADE       │  │ BM25         │              │ │
│  │  │ (ChromaDB)   │  │ (新)         │  │ (PostgreSQL) │              │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │ │
│  │         ↓ 超时/错误        ↓              ↓                         │ │
│  │                    FallbackChain (降级链)                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                   ForbiddenWordFilter                               │ │
│  │  检测 + 替换禁用词 ──► 安全答案                                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     PiiRestorer (输出端)                            │ │
│  │  恢复 PII 占位符 ──► 最终答案 ──► 返回用户 + 缓存                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 五、Phase 1：基础设施详细设计

### 5.1 查询缓存服务 (QueryCacheService)

| 项目 | 内容 |
|------|------|
| **位置** | `backend/app/cache/query_cache.py` |
| **缓存键** | 精确: `qa:cache:kb:{kb_id}:query:{query_hash}`；语义索引: `qa:semantic:kb:{kb_id}:index` |
| **配置** | `cache_enabled`, `cache_default_ttl_seconds` (86400), `cache_semantic_threshold` (0.95), `cache_max_entries_per_kb` (1000) |
| **核心类** | `QueryCacheService`, `ExactCacheStore`, `SemanticCacheMatcher`, `CacheInvalidator` |

### 5.2 降级策略服务 (RetrievalOrchestrator)

| 项目 | 内容 |
|------|------|
| **位置** | `backend/app/rag/retrieval_orchestrator.py` |
| **降级级别** | L0 正常；L1 Vector 超时→BM25；L2 ChromaDB 不可用→BM25；L3 全部失败→错误 |
| **返回字段** | `degradation_info: { level, reason, fallback_used }` |
| **配置** | `retrieval_timeout_ms` (500), `retrieval_fallback_enabled`, `health_check_interval_seconds` (30) |

### 5.3 PII 匿名化服务 (PiiAnonymizer)

| 项目 | 内容 |
|------|------|
| **位置** | `backend/app/security/pii_anonymizer.py` |
| **PII 类型** | phone, id_card, bank_card, email, address, name, custom |
| **表** | `pii_rules` |
| **配置** | `pii_anonymization_enabled`, `pii_types`, `pii_custom_rules` |

### 5.4 禁用词库服务 (ForbiddenWordService)

| 项目 | 内容 |
|------|------|
| **位置** | `backend/app/content/forbidden_word_service.py` |
| **表** | `forbidden_words` |
| **API** | GET/POST/PUT/DELETE `/api/v1/forbidden-words`；`POST /batch`, `POST /check` |
| **配置** | `forbidden_words_enabled`, `forbidden_words_cache_ttl_seconds`, `forbidden_words_default_action` |

---

## 六、Phase 2：增强功能详细设计

### 6.1 自查询检索器 (SelfQueryRetriever)

| 项目 | 内容 |
|------|------|
| **位置** | `backend/app/rag/self_query_retriever.py` |
| **流程** | LLM 解析意图 → 验证 → 构建过滤条件 → 带过滤检索 |
| **元数据** | year, document_type, department, created_at |
| **配置** | `self_query_enabled`, `self_query_llm_temperature` (0.1), `self_query_max_filter_fields` (5) |

### 6.2 SPLADE 稀疏嵌入检索器 (SpladeRetriever)

| 项目 | 内容 |
|------|------|
| **位置** | `backend/app/rag/splade_retriever.py` |
| **表** | `splade_embeddings` |
| **模型** | `naver/splade_v3_distil` |
| **配置** | `splade_enabled`, `splade_model_name`, `splade_threshold` (0.1) |

---

## 七、数据库迁移

```sql
-- V20260303__algorithm_optimization.sql

-- PII 规则表
CREATE TABLE pii_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    pattern VARCHAR(500) NOT NULL,
    mask_format VARCHAR(100) DEFAULT '****',
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 禁用词表
CREATE TABLE forbidden_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    replacement VARCHAR(200),
    is_enabled BOOLEAN DEFAULT TRUE,
    knowledge_base_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_forbidden_words_word ON forbidden_words(word);
CREATE INDEX idx_forbidden_words_kb ON forbidden_words(knowledge_base_id);

-- SPLADE 向量表
CREATE TABLE splade_embeddings (
    chunk_id INT PRIMARY KEY REFERENCES chunks(id),
    sparse_vector JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 内置 PII 规则
INSERT INTO pii_rules (name, pattern, mask_format) VALUES
('phone', '1[3-9]\d{9}', '<PHONE_****>'),
('id_card', '\d{17}[\dXx]', '<ID_****>'),
('bank_card', '\d{16,19}', '<BANK_****>'),
('email', '[\w.-]+@[\w.-]+\.\w+', '<EMAIL_****>');

-- 内置禁用词
INSERT INTO forbidden_words (word, category, replacement) VALUES
('最佳', 'absolute', '优秀'),
('第一', 'absolute', '领先'),
('唯一', 'absolute', '主要'),
('保本', 'misleading', NULL),
('无风险', 'misleading', NULL),
('必赚', 'misleading', NULL);
```

---

## 八、配置汇总

```python
# backend/app/config.py 新增

# ============ 缓存 ============
cache_enabled: bool = True
cache_default_ttl_seconds: int = 86400
cache_semantic_threshold: float = 0.95
cache_max_entries_per_kb: int = 1000

# ============ 降级 ============
retrieval_timeout_ms: int = 500
retrieval_fallback_enabled: bool = True
health_check_interval_seconds: int = 30

# ============ PII ============
pii_anonymization_enabled: bool = True
pii_types: list[str] = ["phone", "id_card", "bank_card", "email", "address", "name"]
pii_custom_rules: list[dict] = []

# ============ 禁用词 ============
forbidden_words_enabled: bool = True
forbidden_words_cache_ttl_seconds: int = 300
forbidden_words_default_action: str = "replace"

# ============ 自查询 ============
self_query_enabled: bool = True
self_query_llm_temperature: float = 0.1
self_query_max_filter_fields: int = 5

# ============ SPLADE ============
splade_enabled: bool = False
splade_model_name: str = "naver/splade_v3_distil"
splade_max_vocab_size: int = 30522
splade_threshold: float = 0.1
```

---

## 九、TDD 实现计划

遵循 **writing-plans**：每个任务 5 步（写失败测试 → 运行确认失败 → 写最小实现 → 运行确认通过 → 提交）。

### 9.1 Phase 1.1 查询缓存

| 步骤 | 操作 |
|------|------|
| 1 | 写 `tests/test_query_cache.py`：`test_exact_match_hit`, `test_semantic_match_hit`, `test_cache_miss`, `test_invalidate_kb` |
| 2 | `pytest tests/test_query_cache.py -v` → 预期 FAIL |
| 3 | 实现 `backend/app/cache/query_cache.py` 及各子模块 |
| 4 | `pytest tests/test_query_cache.py -v` → 预期 PASS |
| 5 | `git commit -m "feat: add query cache service"` |

### 9.2 Phase 1.2 降级策略

| 步骤 | 操作 |
|------|------|
| 1 | 写 `tests/test_retrieval_orchestrator.py`：`test_fallback_on_vector_timeout`, `test_degradation_info_returned` |
| 2 | 运行测试 → FAIL |
| 3 | 实现 `backend/app/rag/retrieval_orchestrator.py` |
| 4 | 运行测试 → PASS |
| 5 | 提交 |

### 9.3 Phase 1.3 PII 匿名化

| 步骤 | 操作 |
|------|------|
| 1 | 写 `tests/test_pii_anonymizer.py`：`test_phone_anonymize`, `test_id_card_anonymize`, `test_restore` |
| 2 | 运行测试 → FAIL |
| 3 | 实现 `backend/app/security/pii_anonymizer.py` |
| 4 | 运行测试 → PASS |
| 5 | 提交 |

### 9.4 Phase 1.4 禁用词库

| 步骤 | 操作 |
|------|------|
| 1 | 写 `tests/test_forbidden_word_service.py` 及 `tests/test_forbidden_words_api.py` |
| 2 | 运行测试 → FAIL |
| 3 | 实现服务与 API |
| 4 | 运行测试 → PASS |
| 5 | 提交 |

### 9.5 Phase 2.1 自查询检索器

| 步骤 | 操作 |
|------|------|
| 1 | 写 `tests/test_self_query_retriever.py`（含 Mock LLM） |
| 2–5 | 按 TDD 流程完成实现与提交 |

### 9.6 Phase 2.2 SPLADE 检索器

| 步骤 | 操作 |
|------|------|
| 1 | 写 `tests/test_splade_retriever.py` |
| 2–5 | 按 TDD 流程完成实现与提交 |

---

## 十、测试策略

| 类型 | 内容 |
|------|------|
| **单元测试** | 各服务核心逻辑，Mock Redis/DB |
| **集成测试** | 与 QaService 集成，需 Postgres/Chroma/Redis |
| **性能测试** | 缓存命中率、降级切换延迟 |
| **安全测试** | PII 漏检、自查询注入、禁用词 bypass |

---

## 十一、验收标准

### Phase 1

- [ ] 缓存命中率 ≥30%（热门查询）
- [ ] 降级切换时间 <100ms
- [ ] PII 检测准确率 ≥99%
- [ ] 禁用词过滤无遗漏

### Phase 2

- [ ] 自查询意图解析准确率 ≥90%
- [ ] SPLADE 检索召回率提升 ≥10%

---

## 十二、执行选项

**计划完成后，可选择：**

1. **子代理驱动**：本会话内，每任务派遣子代理，任务间人工 review  
2. **并行会话**：新开会话，使用 `superpowers:executing-plans`，带检查点批量执行  

---

## 附录：项目上下文

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis + Celery  
- **向量库**: ChromaDB (HNSW)  
- **Embedding**: BGE-M3  
- **Reranker**: BGE-Reranker-v2-m3  
- **测试**: pytest + conftest (Postgres/Chroma skip 条件)  
- **配置**: `backend/app/config.py` (pydantic-settings)
