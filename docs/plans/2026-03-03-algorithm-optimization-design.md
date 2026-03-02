# 算法优化设计文档

> 日期: 2026-03-03
> 状态: 待实现
> 优先级: Phase 1 (基础设施) → Phase 2 (增强功能)

---

## 一、背景与目标

### 1.1 背景

基于对项目算法评估和业界最佳实践对比，发现以下优化空间：

| 优化项 | 当前状态 | 目标状态 |
|--------|---------|---------|
| 查询缓存 | ❌ 无 | ✅ 两层缓存 + 混合匹配 |
| 降级策略 | ❌ 无 | ✅ 多级降级 + 提示 |
| PII 匿名化 | ❌ 无 | ✅ 正则 + 自定义规则 |
| 禁用词库 | ❌ 无 | ✅ 数据库管理 + API |
| 自查询检索器 | ❌ 无 | ✅ LLM 意图解析 |
| SPLADE 检索 | ❌ 无 | ✅ 与 BM25 并存 |

### 1.2 目标

1. **降低 LLM 调用成本**: 缓存热门查询，预计减少 50%+ 调用
2. **提升系统稳定性**: 降级策略保障服务可用性
3. **保障合规安全**: PII 脱敏 + 禁用词过滤
4. **增强检索能力**: 自查询 + SPLADE 提升召回率

---

## 二、整体架构

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

## 三、Phase 1：基础设施优化

### 3.1 查询缓存服务 (QueryCacheService)

#### 3.1.1 功能需求

- **两层缓存**: 检索结果缓存 + LLM 答案缓存
- **混合匹配**: 先精确匹配，无命中再语义匹配（相似度 ≥0.95）
- **TTL 可配置**: 默认 24 小时
- **缓存失效**: 知识库更新时清除相关缓存

#### 3.1.2 核心组件

```python
# backend/app/cache/query_cache.py

class QueryCacheService:
    """查询缓存服务 - 两层匹配策略"""

    def __init__(self, redis_client, embedding_service):
        self.exact_store = ExactCacheStore(redis_client)
        self.semantic_matcher = SemanticCacheMatcher(embedding_service)
        self.invalidator = CacheInvalidator(redis_client)

    async def get(self, kb_id: int, query: str) -> CacheResult | None:
        """获取缓存：L1 精确匹配 → L2 语义匹配"""
        # L1: 精确匹配
        result = await self.exact_store.get(kb_id, query)
        if result:
            return result

        # L2: 语义匹配
        return await self.semantic_matcher.find_similar(kb_id, query)

    async def set(self, kb_id: int, query: str, result: dict, ttl: int):
        """设置缓存"""
        await self.exact_store.set(kb_id, query, result, ttl)
        await self.semantic_matcher.register(kb_id, query)

    async def invalidate_kb(self, kb_id: int):
        """清除知识库相关缓存"""
        await self.invalidator.invalidate_by_kb(kb_id)
```

#### 3.1.3 缓存键设计

```python
# 精确匹配键
EXACT_KEY_PATTERN = "qa:cache:kb:{kb_id}:query:{query_hash}"

# 语义匹配索引
SEMANTIC_INDEX_KEY = "qa:semantic:kb:{kb_id}:index"  # Redis Set

# 知识库缓存集合（用于批量失效）
KB_CACHE_SET_KEY = "qa:cache:kb:{kb_id}:keys"
```

#### 3.1.4 配置项

```python
# backend/app/config.py 新增
cache_enabled: bool = True
cache_default_ttl_seconds: int = 86400  # 24 小时
cache_semantic_threshold: float = 0.95   # 语义相似度阈值
cache_max_entries_per_kb: int = 1000     # 每个 KB 最大缓存条目
```

---

### 3.2 降级策略服务 (RetrievalOrchestrator)

#### 3.2.1 功能需求

- **多级降级**: Vector → SPLADE → BM25 → 错误
- **健康检查**: 定期检测 ChromaDB/PostgreSQL 状态
- **降级提示**: 返回降级原因和级别

#### 3.2.2 降级级别定义

| 级别 | 状态 | 行为 | 返回字段 |
|------|------|------|---------|
| L0 | 全部正常 | Vector + BM25 混合 | 无 |
| L1 | Vector 超时 | 仅 BM25 | `degradation_info.level=1` |
| L2 | ChromaDB 不可用 | 仅 BM25 | `degradation_info.level=2` |
| L3 | 全部失败 | 返回错误 | `error` |

#### 3.2.3 核心组件

```python
# backend/app/rag/retrieval_orchestrator.py

class RetrievalOrchestrator:
    """检索编排器 - 管理降级链"""

    def __init__(self):
        self.health_checker = RetrievalHealthChecker()
        self.fallback_chain = FallbackChain()

    async def retrieve(self, kb_id: int, query: str, top_k: int) -> RetrievalResult:
        """执行检索，自动降级"""
        health = await self.health_checker.check()

        # 根据健康状态选择检索策略
        if health.chroma == "healthy":
            return await self._hybrid_retrieve(kb_id, query, top_k)
        elif health.chroma == "degraded":
            return await self._bm25_only_retrieve(kb_id, query, top_k, reason="chroma_degraded")
        else:
            return await self._bm25_only_retrieve(kb_id, query, top_k, reason="chroma_down")
```

#### 3.2.4 配置项

```python
# backend/app/config.py 新增
retrieval_timeout_ms: int = 500           # 单次检索超时
retrieval_fallback_enabled: bool = True   # 启用降级
health_check_interval_seconds: int = 30   # 健康检查间隔
```

---

### 3.3 PII 匿名化服务 (PiiAnonymizer)

#### 3.3.1 功能需求

- **支持的 PII 类型**: 手机号、身份证、银行卡、邮箱、地址、姓名、自定义
- **双向处理**: 输入端匿名化 → 输出端恢复
- **可配置规则**: 内置 + 数据库自定义

#### 3.3.2 PII 类型与规则

| 类型 | 正则模式 | 替换格式 |
|------|---------|---------|
| phone | `1[3-9]\d{9}` | `<PHONE_****后4位>` |
| id_card | `\d{17}[\dXx]` | `<ID_****后4位>` |
| bank_card | `\d{16,19}` | `<BANK_****后4位>` |
| email | `[\w.-]+@[\w.-]+\.\w+` | `<EMAIL_****域名>` |
| address | 可配置 | `<ADDR>` |
| name | 可配置词表 | `<NAME>` |
| custom | 用户定义 | `<CUSTOM_标签>` |

#### 3.3.3 核心组件

```python
# backend/app/security/pii_anonymizer.py

class PiiAnonymizer:
    """PII 匿名化服务"""

    def __init__(self, rule_registry: PiiRuleRegistry):
        self.detector = PiiDetector(rule_registry)
        self.replacer = PiiReplacer()
        self.restorer = PiiRestorer()

    def anonymize(self, text: str) -> tuple[str, dict]:
        """匿名化文本，返回 (匿名化文本, 映射表)"""
        detections = self.detector.detect(text)
        anonymized, mapping = self.replacer.replace(text, detections)
        return anonymized, mapping

    def restore(self, text: str, mapping: dict) -> str:
        """恢复匿名化文本"""
        return self.restorer.restore(text, mapping)
```

#### 3.3.4 数据库设计

```sql
-- 自定义 PII 规则表
CREATE TABLE pii_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    pattern VARCHAR(500) NOT NULL,
    mask_format VARCHAR(100) DEFAULT '****',
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3.4 禁用词库服务 (ForbiddenWordService)

#### 3.4.1 功能需求

- **词库管理**: 数据库存储 + API CRUD
- **高效匹配**: Trie 树 / Aho-Corasick 算法
- **多级作用域**: 全局 / 知识库级别

#### 3.4.2 禁用词类型

| 类型 | 示例 | 替换策略 |
|------|------|---------|
| absolute | "最佳"、"第一"、"唯一" | 替换为合规词 |
| misleading | "保本"、"无风险"、"必赚" | 删除 |
| sensitive | 政治敏感词 | `***` |
| competitor | 竞争对手名称 | `[竞品名称]` |

#### 3.4.3 核心组件

```python
# backend/app/content/forbidden_word_service.py

class ForbiddenWordService:
    """禁用词服务"""

    def __init__(self, db: Session):
        self.registry = ForbiddenWordRegistry(db)
        self.matcher = WordMatcher()  # Aho-Corasick 实现

    def filter(self, text: str, kb_id: int | None = None) -> FilterResult:
        """过滤文本中的禁用词"""
        words = self.registry.get_words(kb_id)
        matches = self.matcher.find_all(text, words)
        filtered_text = self._apply_replacements(text, matches)
        return FilterResult(text=filtered_text, matches=matches)

    def reload_cache(self):
        """重新加载词库缓存"""
        self.registry.reload()
        self.matcher.build(self.registry.get_all_words())
```

#### 3.4.4 数据库设计

```sql
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
```

#### 3.4.5 API 设计

```
GET    /api/v1/forbidden-words              # 列表
POST   /api/v1/forbidden-words              # 新增
PUT    /api/v1/forbidden-words/{id}         # 更新
DELETE /api/v1/forbidden-words/{id}         # 删除
POST   /api/v1/forbidden-words/batch        # 批量导入
POST   /api/v1/forbidden-words/check        # 预检查
```

---

## 四、Phase 2：增强功能

### 4.1 自查询检索器 (SelfQueryRetriever)

#### 4.1.1 功能需求

- **意图解析**: LLM 自动提取搜索词 + 过滤条件
- **安全验证**: 防止注入攻击
- **多存储适配**: ChromaDB / PostgreSQL 语法转换

#### 4.1.2 核心组件

```python
# backend/app/rag/self_query_retriever.py

class SelfQueryRetriever:
    """自查询检索器 - LLM 解析用户意图"""

    def __init__(self, llm_provider, vector_retriever, bm25_retriever):
        self.intent_parser = IntentParser(llm_provider)
        self.filter_builder = MetadataFilterBuilder()
        self.validator = QueryValidator()

    async def retrieve(self, kb_id: int, query: str, top_k: int) -> list[dict]:
        """执行自查询检索"""
        # 1. LLM 解析意图
        intent = await self.intent_parser.parse(query)

        # 2. 验证意图（防止注入）
        if not self.validator.validate(intent):
            raise ValueError("Invalid query intent")

        # 3. 构建过滤条件
        filters = self.filter_builder.build(intent.filters)

        # 4. 执行带过滤的检索
        return await self._execute_with_filters(kb_id, intent.search_query, filters, top_k)
```

#### 4.1.3 LLM Prompt

```
你是一个查询解析器。从用户问题中提取：
1. 搜索关键词（去掉时间、限制条件）
2. 元数据过滤条件（时间范围、文档类型、部门等）

用户问题: {query}

可用元数据字段:
- year: 文档年份 (整数)
- document_type: 文档类型 (合同/政策/FAQ/公告)
- department: 部门名称
- created_at: 创建时间

请以 JSON 格式返回:
{
    "search_query": "提取的搜索关键词",
    "filters": {"field": "value", ...}
}
```

---

### 4.2 SPLADE 稀疏嵌入检索器 (SpladeRetriever)

#### 4.2.1 功能需求

- **语义稀疏向量**: 比 BM25 更强的语义理解
- **与 BM25 并存**: 作为独立检索选项
- **增量索引**: 支持文档更新

#### 4.2.2 核心组件

```python
# backend/app/rag/splade_retriever.py

class SpladeRetriever:
    """SPLADE 稀疏嵌入检索器"""

    def __init__(self, model_name: str = "naver/splade_v3_distil"):
        self.encoder = SpladeEncoder(model_name)
        self.store = SparseVectorStore()

    async def index(self, chunk_id: int, text: str):
        """索引单个 chunk"""
        sparse_vec = self.encoder.encode(text)
        await self.store.save(chunk_id, sparse_vec)

    async def retrieve(self, query: str, top_k: int) -> list[dict]:
        """检索相似文档"""
        query_vec = self.encoder.encode(query)
        return await self.store.search(query_vec, top_k)
```

#### 4.2.3 数据库设计

```sql
-- SPLADE 稀疏向量存储
CREATE TABLE splade_embeddings (
    chunk_id INT PRIMARY KEY REFERENCES chunks(id),
    sparse_vector JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_splade_chunk ON splade_embeddings(chunk_id);
```

---

## 五、配置汇总

```python
# backend/app/config.py 新增配置项

# ============ 缓存配置 ============
cache_enabled: bool = True
cache_default_ttl_seconds: int = 86400
cache_semantic_threshold: float = 0.95
cache_max_entries_per_kb: int = 1000

# ============ 降级配置 ============
retrieval_timeout_ms: int = 500
retrieval_fallback_enabled: bool = True
health_check_interval_seconds: int = 30

# ============ PII 配置 ============
pii_anonymization_enabled: bool = True
pii_types: list[str] = ["phone", "id_card", "bank_card", "email", "address", "name"]
pii_custom_rules: list[dict] = []

# ============ 禁用词配置 ============
forbidden_words_enabled: bool = True
forbidden_words_cache_ttl_seconds: int = 300
forbidden_words_default_action: str = "replace"

# ============ 自查询配置 ============
self_query_enabled: bool = True
self_query_llm_temperature: float = 0.1
self_query_max_filter_fields: int = 5

# ============ SPLADE 配置 ============
splade_enabled: bool = False
splade_model_name: str = "naver/splade_v3_distil"
splade_max_vocab_size: int = 30522
splade_threshold: float = 0.1
```

---

## 六、数据库迁移

```sql
-- 迁移文件: V20260303__algorithm_optimization.sql

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

## 七、实现计划

### Phase 1: 基础设施 (预计 8 天)

| 任务 | 预计时间 | 依赖 |
|------|---------|------|
| 1.1 查询缓存服务 | 3 天 | Redis |
| 1.2 降级策略服务 | 2 天 | 无 |
| 1.3 PII 匿名化服务 | 1.5 天 | 无 |
| 1.4 禁用词库服务 | 1.5 天 | 无 |

### Phase 2: 增强功能 (预计 4 天)

| 任务 | 预计时间 | 依赖 |
|------|---------|------|
| 2.1 自查询检索器 | 2 天 | LLM Provider |
| 2.2 SPLADE 检索器 | 2 天 | Phase 1 |

---

## 八、测试策略

每个模块遵循 TDD 流程：

1. **单元测试**: 核心逻辑测试
2. **集成测试**: 与现有系统集成测试
3. **性能测试**: 缓存命中率、检索延迟
4. **安全测试**: PII 漏检、注入攻击

---

## 九、验收标准

### Phase 1 验收标准

- [ ] 缓存命中率 ≥30%（热门查询）
- [ ] 降级切换时间 <100ms
- [ ] PII 检测准确率 ≥99%
- [ ] 禁用词过滤无遗漏

### Phase 2 验收标准

- [ ] 自查询意图解析准确率 ≥90%
- [ ] SPLADE 检索召回率提升 ≥10%
