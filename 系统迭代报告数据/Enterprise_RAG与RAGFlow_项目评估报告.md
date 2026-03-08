# Enterprise RAG 与 RAGFlow 项目评估报告

> **评估对象**：RAGFlow（`测试数据/ragflow-main`，infiniflow 开源 RAG 引擎）  
> **被评估项目**：Enterprise RAG（企业知识库问答系统）  
> **评估目的**：判断 RAGFlow 对 Enterprise RAG 项目迭代与优化的参考价值  
> **评估人**：C0（架构师）、X6（RAG 产品顾问）  
> **评估日期**：2026-02-15  

---

## 一、RAGFlow 项目概述

| 项目 | 内容 |
|------|------|
| 名称 | RAGFlow（infiniflow） |
| 定位 | 开源 RAG 引擎，融合 RAG 与 Agent 能力，提供端到端企业级 RAG 工作流 |
| 许可 | Apache-2.0 |
| 技术栈 | FastAPI、Docker、Infinity/ES/OceanBase、DeepDoc、GraphRAG |
| 部署 | Docker Compose，推荐 CPU≥4 核、RAM≥16GB、Disk≥50GB |

### 1.1 核心特性（摘自 README）

- **深度文档理解（DeepDoc）**：OCR、布局识别、表结构识别（TSR）、表格自动旋转
- **基于模板的智能分块**：多种分块模板、可解释、可配置
- **引用与低幻觉**：分块可视化、可手动调整，答案可溯源
- **多路召回 + 融合重排序**：全文 + 向量融合、多种 Reranker 后端
- **异构数据源**：Word、PPT、Excel、PDF、图片、网页、结构化数据等

### 1.2 与 Enterprise RAG 的架构差异

| 维度 | Enterprise RAG | RAGFlow |
|------|----------------|---------|
| 文档解析 | PyMuPDF + PaddleOCR（扫描 PDF 回退） | DeepDoc：布局识别、TSR、表格旋转、多解析方法 |
| 分块单位 | 字符（chunk_size=800） | Token（chunk_token_size=512）+ 可配置分隔符 |
| 检索 | 纯向量（ChromaDB cosine） | 全文 + 向量融合（weighted_sum 0.05/0.95） |
| 向量库 | ChromaDB | Infinity / Elasticsearch / OceanBase |
| 存储形态 | PostgreSQL 元数据 + Chroma | 自建 DocStore 抽象 |

---

## 二、RAGFlow 对 Enterprise RAG 有参考价值的模块

### 2.1 深度文档理解（DeepDoc）——**高价值**

| 项目 | 内容 |
|------|------|
| 路径 | `deepdoc/`（vision、parser） |
| 能力 | OCR、布局识别（10 类）、表结构识别（TSR）、表格自动旋转 |

**布局组件**：Text、Title、Figure、Figure caption、Table、Table caption、Header、Footer、Reference、Equation  

**价值**：  
- 我们：PDF 先 `get_text()`，文本 < 20 字时视为扫描 PDF 做 OCR  
- RAGFlow：先布局分析，区分正文/标题/表格/图片，表格走 TSR，再统一合并  
- 对复杂 PDF、表格密集文档，布局 + TSR 能显著提升结构化提取质量  

**适配建议**：  
- 深度集成 DeepDoc 成本高（依赖、模型、存储结构）  
- 可作为 Phase 4/5 的「增强解析模式」：对表格多、布局复杂的 PDF 调用 DeepDoc 或类似布局模型  
- 短期可参考其**表格自动旋转**逻辑：扫描 PDF 表格方向不正时，多角度 OCR 取最优  

---

### 2.2 分块逻辑（naive_merge）——**高价值**

| 项目 | 内容 |
|------|------|
| 路径 | `rag/nlp/__init__.py`，`naive_merge`、`naive_merge_with_images` |
| 单位 | **Token**（`num_tokens_from_string`），非字符 |
| 参数 | `chunk_token_num`、`delimiter`（默认 `\n。；！？`）、`overlapped_percent` |
| 重叠 | 按 `overlapped_percent` 计算重叠区间，避免在句中断开 |

**实现要点**：  
- 按 delimiter 切分，合并到不超过 `chunk_token_num * (100 - overlapped_percent) / 100`  
- 支持自定义分隔符（如 `` `表格` ``）  
- 支持图文混排（`naive_merge_with_images`）  

**价值**：  
- 我们以字符为粒度，Token 更贴合 LLM 上下文限制  
- 默认分隔符 `\n。；！？` 与中文断句习惯一致  

**适配建议**：  
- 在 `TextChunker` 中增加「按 Token 分块」选项  
- 使用 `tiktoken` 或 `transformers` 的 tokenizer 估算 token 数  
- 分隔符可配置为 `\n`、`。`、`；`、`！`、`？` 等  

---

### 2.3 混合检索（全文 + 向量融合）——**高价值**

| 项目 | 内容 |
|------|------|
| 路径 | `rag/nlp/search.py`，`Dealer.search` |
| 实现 | `FusionExpr("weighted_sum", topk, {"weights": "0.05,0.95"})` |
| 含义 | 5% 全文权重 + 95% 向量权重，多路召回后加权融合 |

**价值**：  
- 架构 Phase 4 规划了混合检索  
- ChromaDB 无内置全文，需配合 BM25 或外部全文引擎  
- RAGFlow 的权重设计（0.05/0.95）可作为默认参考  

**适配建议**：  
- 若引入 BM25（如 Langchain-Chatchat 评估报告所述），可参考该权重做 RRF 或加权融合  
- 权重可配置，便于按业务调优  

---

### 2.4 分块参数与模板——**中高价值**

| 项目 | 内容 |
|------|------|
| 路径 | `rag/flow/splitter/splitter.py` |
| 参数 | `chunk_token_size`、`delimiters`、`overlapped_percent`、`children_delimiters` |
| 扩展 | `table_context_size`、`image_context_size`（表格/图片上下文） |

**价值**：  
- 分隔符、重叠比例可按文档类型配置  
- `children_delimiters` 支持二级切分（如按自定义 `` `表格` `` 再切）  

**适配建议**：  
- 知识库级分块参数我们已有，可补充「分隔符列表」配置  
- 表格/图片上下文扩展可作为长期方向  

---

### 2.5 引用与 Prompt 模板——**中价值**

| 项目 | 内容 |
|------|------|
| 路径 | `rag/prompts/generator.py` |
| 能力 | `citation_prompt`、`citation_plus`，Jinja2 模板 |

**价值**：  
- 我们已有按句相似度插入 `[ID:x]` 的引用逻辑  
- 可参考其 citation 相关 prompt 设计，优化「如何让 LLM 更好利用引用」  

**适配建议**：  
- 查阅 `citation_prompt`、`citation_plus` 模板内容  
- 在 `RagPipeline.build_prompt_messages` 中适度融入其思路  

---

### 2.6 基准测试 CLI——**中价值**

| 项目 | 内容 |
|------|------|
| 路径 | `test/benchmark/` |
| 能力 | HTTP 基准测试，支持 chat、retrieval，可创建 dataset、上传文档、解析、运行、输出报告 |

**价值**：  
- 我们缺少标准化 benchmark 工具  
- 可借鉴其设计：CLI、数据集创建、检索/对话 benchmark、JSON 报告  

**适配建议**：  
- 在 `enterprise_rag` 下新增 `scripts/benchmark/` 或类似目录  
- 实现轻量版：给定问题列表 + 知识库，批量调用 `/api/qa/ask`，汇总耗时、成功率等  

---

### 2.7 Reranker 多后端——**参考价值**

| 项目 | 内容 |
|------|------|
| 路径 | `rag/llm/rerank_model.py` |
| 后端 | Jina API、Xinference、LocalAI、NVIDIA、OpenAI 兼容 API |

**与我们的对比**：  
- 我们：仅 BGE CrossEncoder 本地  
- RAGFlow：支持云 API（Jina、NVIDIA）与本地（Xinference、LocalAI）  

**适配建议**：  
- Phase 4 若考虑云 Reranker（如 Jina），可参考其 `similarity()` 接口与归一化逻辑  

---

## 三、集成成本与风险评估

### 3.1 全项目集成（不推荐）

| 风险 | 说明 |
|------|------|
| 架构差异 | DocStore、Parser、Flow 与现有 PostgreSQL + Chroma + 自建服务层不兼容 |
| 依赖重 | DeepDoc、Infinity/ES、多模型服务，部署复杂 |
| 功能冗余 | Agent、GraphRAG、多租户等超出当前 Phase |
| 存储迁移 | 需从 Chroma 迁至 Infinity/ES 等，迁移成本高 |

**结论**：不建议将 RAGFlow 作为主框架集成。

### 3.2 按需借鉴（推荐）

| 策略 | 说明 |
|------|------|
| 算法抽取 | 抽取 naive_merge 的 Token 分块、分隔符、重叠逻辑 |
| 思路参考 | 混合检索权重、引用 prompt、benchmark CLI 设计 |
| 可选增强 | 表格旋转、布局分析作为远期增强解析选项 |

---

## 四、对项目迭代/优化的具体建议

### 4.1 短期（Phase 3 收尾 / Phase 4 初期）

| 序号 | 建议 | 参考来源 | 优先级 |
|------|------|----------|--------|
| 1 | 分块改为按 Token 控制 + 可配置分隔符 | naive_merge | 高 |
| 2 | 引用相关 Prompt 优化 | citation_prompt、citation_plus | 中 |

### 4.2 中期（Phase 4）

| 序号 | 建议 | 参考来源 | 优先级 |
|------|------|----------|--------|
| 3 | 实现全文 + 向量混合检索（含权重配置） | FusionExpr、Dealer.search | 高 |
| 4 | 增加 benchmark CLI（检索/对话） | test/benchmark | 中 |

### 4.3 长期（Phase 5+）

| 序号 | 建议 | 参考来源 | 优先级 |
|------|------|----------|--------|
| 5 | 复杂 PDF 的布局 + 表格增强解析 | DeepDoc | 中低 |
| 6 | 表格自动旋转（扫描 PDF） | DeepDoc Table Auto-Rotation | 低 |

---

## 五、评估结论

| 维度 | 结论 |
|------|------|
| **是否值得研究** | 是，尤其分块、混合检索、DeepDoc 思路 |
| **是否建议全项目集成** | 否，架构与依赖差异大 |
| **建议使用方式** | 抽取算法与设计，在现有架构下自建实现 |
| **最高价值模块** | naive_merge（Token 分块 + 分隔符）、FusionExpr（全文+向量融合）、DeepDoc 思路 |
| **与 Haystack / Langchain-Chatchat 的互补** | Haystack：评估；Langchain-Chatchat：中文分块、混合检索；RAGFlow：Token 分块、混合检索权重、DeepDoc、benchmark |

---

## 六、附录：RAGFlow 关键路径速查

```
测试数据/ragflow-main/
├── deepdoc/                    # 深度文档理解
│   ├── vision/                 # OCR、布局识别、TSR
│   └── parser/                 # PDF 等解析器
├── rag/
│   ├── nlp/
│   │   ├── __init__.py         # naive_merge、naive_merge_with_images
│   │   └── search.py           # Dealer.search、FusionExpr
│   ├── flow/
│   │   ├── splitter/splitter.py
│   │   └── parser/parser.py
│   ├── llm/
│   │   └── rerank_model.py     # Jina、Xinference、NVIDIA 等
│   ├── prompts/generator.py    # citation_prompt
│   └── app/                    # 各类型解析（paper、book、qa 等）
└── test/benchmark/             # HTTP benchmark CLI
```

---

*报告完成。如有疑问可联系 C0 或 X6 补充。*
