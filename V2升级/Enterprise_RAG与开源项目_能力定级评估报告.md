# Enterprise RAG 与开源项目能力定级评估报告

> **文档版本**：v1.0
> **评估日期**：2026-02-23
> **评估基准**：《RAG 系统能力三级模型（L1/L2/L3）》
> **评估对象**：Enterprise RAG（最新版）、Haystack、Langchain-Chatchat、RAGFlow
> **评估人**：RAG 系统架构师 / RAG 产品经理

---

## 一、评估总览

| 系统 | 定级 | 精确位置 | 一句话定性 |
|------|------|---------|-----------|
| **Enterprise RAG**（最新版） | **L1.8** | L1 上限，触及 L2 门槛 | 检索链路完整且有工程深度，但缺少质量保障和自适应能力 |
| **Langchain-Chatchat** | **L1.5** | L1 中上 | 中文生态好，但架构受 LangChain 框架限制，自身创新有限 |
| **Haystack** | **L1.7 框架 + L2.3 工具箱** | 框架本身 L1，但提供了 L2 级别的评估工具 | 不是 RAG 产品，是构建 RAG 的工具箱，评估体系是其最大资产 |
| **RAGFlow** | **L2.2** | L2 初中期 | 三个项目中能力最强，文档理解和混合检索达到 L2 水平 |

---

## 二、Enterprise RAG（最新版）—— L1.8

### 2.1 达到 L1 上限的依据

| L1 能力项 | 实现情况 | 完成度 |
|-----------|---------|--------|
| 向量检索 | `VectorRetriever` + ChromaDB cosine | 100% |
| 关键词检索 | `KeywordRetriever`（向量候选+词频重排） | 80%（非真正 BM25） |
| Reranker | `BgeRerankerService`（CrossEncoder + fallback） | 100% |
| 去重 | SimHash + 汉明距离 | 100% |
| 查询扩展 | 规则/LLM/混合三模式 | 100% |
| 多策略检索 | 4 种预设策略（default/high_recall/high_precision/low_latency） | 100% |
| 流式输出 | SSE 流式 + 非流式双模式 | 100% |
| 引用标注 | 句子-Chunk 余弦相似度 + snippet 提取 | 100% |
| LLM 降级 | LLM 失败返回检索结果 | 100% |
| 动态阈值 | Reranker 分数阈值 + Chroma 距离阈值 | 100% |
| 检索日志 | RetrievalLog 全链路记录 | 100% |
| 多轮对话 | 内存 + 数据库双重持久化 | 100% |

### 2.2 未达到 L2 的依据

| L2 能力项 | 现状 | 缺失程度 |
|-----------|------|---------|
| 意图分析/问题路由 | 无，所有问题走同一条路 | 完全缺失 |
| 查询改写（口语→检索语言） | 无，查询扩展 ≠ 查询改写 | 完全缺失 |
| HyDE | 无 | 完全缺失 |
| 真正的 BM25 稀疏检索 | `KeywordRetriever` 只是向量候选的词频重排 | 大部分缺失 |
| RRF 多路融合 | 简单的 chunk_id 去重合并，不是加权融合 | 大部分缺失 |
| 幻觉检测 | 无 | 完全缺失 |
| 答案质量验证 | 无 | 完全缺失 |
| 置信度评估 | 无 | 完全缺失 |
| 场景适配 | 无，4 种策略只调参数，不改流程 | 完全缺失 |
| 结构化分块 | 无，纯字符/句子分块，不保留文档结构 | 完全缺失 |
| 全链路可观测 | 有 RetrievalLog，但无 Tracing | 部分缺失 |
| 离线评估体系 | 无，只有用户反馈 | 完全缺失 |

### 2.3 定级结论

L1 的所有能力都做到了，且做得比较扎实（SimHash 去重、动态阈值、多策略、查询扩展等超出基础 L1），但 L2 的 12 项核心能力一项都没有。**定为 L1.8**。

---

## 三、Langchain-Chatchat —— L1.5

### 3.1 能力评估

| 能力项 | 实现情况 | 评价 |
|--------|---------|------|
| 向量检索 | FAISS/Chroma/Milvus 多后端 | L1 标准，后端选择比 Enterprise RAG 多 |
| BM25 检索 | `EnsembleRetriever`（BM25 + 向量，jieba 分词） | 有真正的 BM25，这点更强 |
| 混合检索融合 | 简单 0.5/0.5 权重 | L1 水平，不是 RRF |
| 中文分块 | `ChineseRecursiveTextSplitter`（递归分隔符） | 比字符窗口好，但仍是 L1 |
| 标题增强 | `zh_title_enhance`（规则识别标题） | 有创意，但是规则方法 |
| Reranker | CrossEncoder | L1 标准 |
| Agent | 针对 ChatGLM3/Qwen 的工具调用 | 有 Agent 雏形，但非常初级 |
| 评估体系 | 无 | 缺失 |
| 幻觉检测 | 无 | 缺失 |
| 质量保障 | 无 | 缺失 |

### 3.2 定级论证

核心优势是中文生态（中文分块、jieba BM25、标题增强）和多向量库支持。但架构深度不如 Enterprise RAG——没有 SimHash 去重、没有动态阈值、没有多策略检索、没有查询扩展、检索日志也不如 Enterprise RAG 完善。

有真正的 BM25 混合检索，这一点比 Enterprise RAG 强。但整体来看，是一个中文友好但架构较浅的 L1 系统。**定为 L1.5**。

---

## 四、Haystack —— L1.7 框架 + L2.3 工具箱

Haystack 不是 RAG 产品，而是构建 RAG 的框架，需要分两个维度评估。

### 4.1 作为 Pipeline 框架（L1.7）

| 能力项 | 实现情况 | 评价 |
|--------|---------|------|
| Pipeline 编排 | YAML/代码 Pipeline，组件串联 | 声明式编排，比硬编码好，但不是 L2 的条件路由 |
| 检索器 | 多种 Retriever（向量、BM25、MultiQuery、SentenceWindow、AutoMerging） | 组件丰富，但需要用户自己组装 |
| Reranker | CrossEncoder + LostInTheMiddle | L1 标准 + 一个有价值的创新 |
| 分块 | DocumentSplitter（多粒度）+ EmbeddingBasedDocumentSplitter（语义分块） | 语义分块触及 L2 |

### 4.2 作为评估工具箱（L2.3）

| 能力项 | 实现情况 | 评价 |
|--------|---------|------|
| 检索评估 | Recall、MAP、MRR、NDCG 四大指标 | **L2 标准能力** |
| 答案评估 | FaithfulnessEvaluator（幻觉检测）、ContextRelevanceEvaluator | **L2 核心能力** |
| LLM 评估 | LLMEvaluator（通用 LLM-as-Judge） | L2 标准 |
| 评估管理 | EvaluationRunResult（结构化存储+导出） | L2 标准 |

### 4.3 定级结论

框架本身是 L1 级别（Pipeline 是线性的，没有条件路由和自纠错）。但评估工具箱已达到 L2 水平。**定为 L1.7（框架）+ L2.3（工具箱）**。

---

## 五、RAGFlow —— L2.2

### 5.1 能力评估

| 能力项 | 实现情况 | 评价 |
|--------|---------|------|
| 文档理解 | DeepDoc：OCR + 布局识别（10类）+ 表结构识别 + 表格旋转 | **远超 L1**，L2 水平 |
| 分块 | Token 级分块 + 可配置分隔符 + 图文混排 | L2 水平 |
| 混合检索 | 全文 + 向量加权融合（0.05/0.95） | 真正的混合检索，L2 标准 |
| 多 Reranker 后端 | Jina API、Xinference、LocalAI、NVIDIA | 比单一 CrossEncoder 灵活 |
| 引用 Prompt | Jinja2 模板化的 citation_prompt | 比硬编码 Prompt 更灵活 |
| Benchmark CLI | 标准化基准测试工具 | L2 的质量保障基础设施 |
| GraphRAG | 有知识图谱能力 | 触及 L2-L3 边界 |
| Agent | 有 Agent + 工作流能力 | 初步的 L2-L3 能力 |

### 5.2 未达到完整 L2 的部分

| L2 能力项 | RAGFlow 现状 |
|-----------|-------------|
| 意图分析/问题路由 | 未见明确实现 |
| 查询改写/HyDE | 未见 |
| NLI 幻觉检测 | 未见独立的幻觉检测模块 |
| 自适应策略选择 | 检索策略是固定的 |
| 离线评估指标 | 有 Benchmark CLI，但不如 Haystack 完整 |

### 5.3 定级结论

三个项目中能力最强。文档理解能力（DeepDoc 布局识别 + TSR）明确超出 L1。混合检索是真正的全文+向量加权融合。但缺少 L2 的"智能查询层"和"质量保障层"。**定为 L2.2**。

---

## 六、四系统能力雷达对比

```
                    Enterprise RAG   Chatchat   Haystack   RAGFlow
                    ──────────────   ────────   ────────   ───────
文档解析深度              ★★★☆☆        ★★☆☆☆     ★★☆☆☆     ★★★★★
分块智能度                ★★☆☆☆        ★★★☆☆     ★★★★☆     ★★★★☆
检索多样性                ★★★☆☆        ★★★★☆     ★★★★☆     ★★★★★
重排序能力                ★★★★☆        ★★★☆☆     ★★★★☆     ★★★★☆
去重/后处理               ★★★★★        ★★☆☆☆     ★★☆☆☆     ★★★☆☆
查询扩展/改写             ★★★★☆        ★☆☆☆☆     ★★★☆☆     ★★☆☆☆
质量保障(幻觉检测)        ☆☆☆☆☆        ☆☆☆☆☆     ★★★★☆     ★☆☆☆☆
评估体系                  ★★☆☆☆        ☆☆☆☆☆     ★★★★★     ★★★☆☆
场景适配                  ★★☆☆☆        ★☆☆☆☆     ★★☆☆☆     ★★☆☆☆
Agent/自治能力            ☆☆☆☆☆        ★☆☆☆☆     ★☆☆☆☆     ★★☆☆☆
工程完整度(产品级)        ★★★★★        ★★★★☆     ★★☆☆☆     ★★★★☆
可观测性                  ★★★★☆        ★★☆☆☆     ★★☆☆☆     ★★★☆☆
```

### 关键发现

1. **Enterprise RAG 在工程完整度和可观测性上是最强的**——完整的产品（前后端）、RetrievalLog、多策略、动态阈值、SimHash 去重，这些其他三个项目都没有做到这个程度
2. **最大的短板是质量保障（0星）和评估体系（2星）**——这恰好是 Haystack 最强的地方
3. **第二大短板是文档解析深度（3星）**——这恰好是 RAGFlow 最强的地方
4. **第三大短板是检索多样性（3星）**——BM25 混合检索是 Chatchat 和 RAGFlow 都有的

---

## 七、三个项目对 Enterprise RAG 演进的具体价值

### 7.1 Haystack → 帮助跨入 L2（质量保障层）—— 价值最高

| 可借鉴模块 | 对应 L2 演进目标 | 借鉴方式 | 优先级 |
|-----------|-----------------|---------|--------|
| FaithfulnessEvaluator | 幻觉检测 | 抽取算法：将答案拆成陈述，逐条用 NLI/LLM 判断是否被上下文蕴含 | **最高** |
| ContextRelevanceEvaluator | 检索质量在线评估 | 抽取算法：判断检索到的上下文与问题的相关性 | **高** |
| DocumentRecall/MAP/MRR/NDCG | 离线评估体系 | 在 `app/evaluation/` 下实现轻量版 | **高** |
| EvaluationRunResult | 评估结果管理 | 参考其结构设计 eval_runs 表 | **中** |
| LLMEvaluator | LLM-as-Judge | 抽取通用 LLM 评分框架 | **中** |
| EmbeddingBasedDocumentSplitter | 语义分块 | 长期方向 | **低** |
| LostInTheMiddle | Prompt 优化 | 在 build_prompt_messages 中调整 chunk 排列顺序 | **中** |

### 7.2 RAGFlow → 补齐检索+分块 —— 价值第二

| 可借鉴模块 | 对应 L2 演进目标 | 借鉴方式 | 优先级 |
|-----------|-----------------|---------|--------|
| naive_merge（Token 分块） | 分块精度提升 | 在 TextChunker 中增加 token 模式 | **高** |
| 全文+向量加权融合 | 真正的混合检索 | 引入 BM25，实现 RRF 融合 | **高** |
| 融合权重 0.05/0.95 | 混合检索默认参数 | 作为初始参数参考 | **中** |
| DeepDoc 布局识别 | 复杂 PDF 解析 | 长期方向 | **低** |
| Benchmark CLI | 标准化测试 | 在 scripts/benchmark/ 下实现轻量版 | **中** |

### 7.3 Langchain-Chatchat → 中文能力锦上添花 —— 价值最低但最易落地

| 可借鉴模块 | 对应改进目标 | 借鉴方式 | 优先级 |
|-----------|------------|---------|--------|
| ChineseRecursiveTextSplitter | 中文分块质量 | 在 chunker.py 中增加中文递归分块模式 | **中高** |
| zh_title_enhance | 检索上下文质量 | 分块后增加标题增强步骤 | **中** |
| jieba BM25 | 中文 BM25 分词 | 与 RAGFlow 的混合检索结合 | **中** |

---

## 八、综合演进路线图

```
当前 L1.8
  │
  ├─ 第一步：质量保障层（主要借鉴 Haystack）
  │   ├─ FaithfulnessEvaluator（幻觉检测）
  │   ├─ 置信度评估（多信号加权）
  │   ├─ 离线评估指标（Recall/MAP/MRR）
  │   └─ 答案不合格时的降级策略
  │
  ├─ 第二步：检索能力升级（主要借鉴 RAGFlow + Chatchat）
  │   ├─ 真正的 BM25（rank_bm25 + jieba）
  │   ├─ RRF 混合检索融合
  │   ├─ Token 级分块
  │   └─ 中文递归分块 + 标题增强
  │
  ├─ 第三步：智能查询层（自研为主）
  │   ├─ 意图分析 + 问题路由
  │   ├─ 查询改写
  │   └─ LostInTheMiddle Prompt 优化（借鉴 Haystack）
  │
  ╰─→ 达到 L2.0
  │
  ├─ 第四步：场景适配 + 评估可观测 + 性能缓存
  │
  ╰─→ 达到 L2.8（V2 目标）
  │
  ├─ 未来：Agent 能力（进入 L3）
  │
  ╰─→ L3.0
```

---

## 九、结论

1. **Enterprise RAG 并不弱**。在工程完整度和可观测性上已超过 Langchain-Chatchat，与 RAGFlow 持平。差距不在"基础功能"，而在"智能化和质量保障"。

2. **Haystack 对 Enterprise RAG 价值最大**，核心是评估体系（Faithfulness + Recall/MAP/MRR），这是从 L1 跨入 L2 的关键钥匙。

3. **RAGFlow 价值第二**，核心是 Token 级分块 + 真正的混合检索。DeepDoc 布局识别是长期方向。

4. **Langchain-Chatchat 价值最低**，但中文递归分块和标题增强值得花半天时间抽取。

5. **三个项目都没有达到 L3**。L3（自治级 Agentic RAG）在开源界还没有成熟的完整实现，这是 Enterprise RAG 未来可以差异化的方向。

---

**文档修订历史**

| 版本 | 日期 | 修订人 | 修订内容 |
|------|------|--------|----------|
| v1.0 | 2026-02-23 | RAG 架构师 | 基于 L1/L2/L3 模型重新评估 |
