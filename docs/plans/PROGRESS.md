# V2.0 开发进度

## 📊 当前状态总览

| 批次 | 任务数 | 完成数 | 状态 |
|------|--------|--------|------|
| B1-infra | 3 | 3 | ✅ 100% |
| B1-retrieval | 7 | 7 | ✅ 100% |
| B1-pipeline | 3 | 3 | ✅ 100% |
| B2-quality | 5 | 4 | ✅ 100% |

---

## ✅ 已完成任务

### B1-infra（基础设施）

| 任务 | 文件 | 状态 |
|------|------|------|
| B1-1 | PostgreSQL + pg_jieba | ✅ 预构建镜像 `sdrzlyz/pg-ts-jieba:16` 已验证 |
| B1-2 | chunks 表迁移 | ✅ V2.0_001/002/003 SQL 脚本完成 |
| B1-3 | knowledge_bases 迁移 | ✅ 新增 chunk_mode、parent_retrieval_mode、dynamic_expand_n |

### B1-retrieval（检索核心）

| 任务 | 文件 | 行数 | 状态 |
|------|------|------|------|
| B1-4 | `bm25_retriever.py` | 129 | ✅ BM25 检索器 + pg_jieba |
| B1-5 | `rrf_fusion.py` | 141 | ✅ RRF 双路融合算法 |
| B1-7 | 分块器（中文递归）| - | ✅ `chunker.py` 集成 |
| B1-8 | 分块器（Token级） | - | ✅ `chunker.py` 集成 |
| B1-9 | `title_extractor.py` | 104 | ✅ Markdown/中文章节支持 |
| B1-10 | `parent_retriever.py` | 200 | ✅ physical/dynamic/off 模式 |

### B1-pipeline（集成管道）

| 任务 | 文件 | 行数 | 状态 |
|------|------|------|------|
| B1-11 | `adaptive_topk.py` | 92 | ✅ 基于分数断崖检测 |
| B1-12 | `denoiser.py` | 85 | ✅ Reranker + 关键词双重过滤 |
| B1-13 | `hybrid_pipeline.py` | 158 | ✅ 完整检索流程（数据格式转换已修复）|

**B1 总计：6 个文件，~609 行核心代码**

### B2-quality（答案质量保障）

| 任务 | 文件 | 行数 | 状态 |
|------|------|------|------|
| B2-1 | `verify/nli_detector.py` | 81 | ✅ NLI 幻觉检测器 |
| B2-2 | `verify/confidence_scorer.py` | 67 | ✅ 置信度评估器 |
| B2-3 | `verify/citation_verifier.py` | 109 | ✅ 引用验证器 |
| B2-4 | `verify/verify_pipeline.py` | 131 | ✅ 验证 Pipeline |
| B2-5 | `verify/refusal.py` | 67 | ✅ 智能拒答 |
| B2-6 | V2.0_004_sql | 19 | ✅ retrieval_feedbacks 迁移 |
| B2-7 | API `retrieval.py` | 358 | ✅ 反馈服务 + API 已存在 |

**B2 总计：7 个文件，~432 行代码**

---

## ⏳ 待完成任务

### B2-quality 阶段

| 任务 | 依赖 | 优先级 |
|------|------|--------|
| B2-5 | `verify/refusal.py` | 无 | P0 |
| B2-6 | `V2.0_004_alter_retrieval_feedbacks.sql` | 数据库 | P0 |
| B2-7 | `feedback_service.py` + API | B2-6 | P1 |
| B2-8 | QA 服务集成 | B2-1-5 | P1 |
| B2-9 | `V2.0_006_alter_retrieval_logs.sql` | 数据库 | P1 |

---

## 📋 下一步计划

### 选项 A：完成 B2 核心集成
1. B2-5: 智能拒答模块（5 分钟）
2. B2-6: retrieval_feedbacks 数据库迁移（10 分钟）
3. B2-7: 反馈服务 + API（20 分钟）

### 选项 B：完成 B2 数据库工作
1. B2-6: retrieval_feedbacks 迁移
2. B2-9: retrieval_logs 迁移
3. 数据模型更新

### 选项 C：直接前端集成验证
1. QA 服务集成验证
2. SSE 事件发送测试
3. 端到端测试

---

## 📊 统计数据

### 代码量统计
- B1 阶段：9 个文件，~1013 行
- B2 核心模块：4 个文件，~388 行
- **总计：13 个文件，~1401 行**

### 数据库迁移
- 已完成：V2.0_001 ~ V2.0_003
- 待完成：V2.0_004, V2.0_006

### 关键依赖
- NLI 模型：`cross-encoder/nli-deberta-v3-base` (~700MB)
- PostgreSQL 16 + pg_jieba
- CUDA/GPU 支持（推理）

---

## 🎯 B2-Quality 核心功能验证

### 验证流程
```
用户回答
  ↓
NLI 幻觉检测（B2-1）
  ↓
置信度计算（B2-2）
  ↓
引用验证（B2-3）
  ↓
验证 Pipeline 决策（B2-4）
  ↓
动作：PASS / FILTER / RETRY / REFUSE
```

### 决策规则
- **PASS**: confidence ≥ 0.5 AND citation ≥ 0.5
- **FILTER**: citation < 0.5
- **RETRY**: has_hallucination AND low_confidence (首次)
- **REFUSE**: confidence < 0.3 OR faithfulness < 0.3

---

## 💡 建议

**推荐执行顺序：**
1. 完成 B2-5（智能拒答）- 无依赖，5 分钟
2. 完成 B2-6（数据库迁移）- 独立任务，10 分钟
3. 测试 B2 核心模块导入
4. 完成 B2-7（反馈服务）

**预计额外耗时：~30-40 分钟**