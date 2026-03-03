# 任务组 D 执行报告

> 执行日期：2026-02-21
> 执行内容：开发与测试任务

---

## 一、任务清单与完成状态

| 任务编号 | 任务名称 | 状态 | 产出文件 |
|----------|----------|------|----------|
| D1 | 创建 API 契约检查脚本 | ✅ 完成 | `scripts/check_api_contract.py` |
| D2 | 创建配置项检查脚本 | ✅ 完成 | `scripts/check_config_usage.py` |
| D3 | 补充 E2E 测试 | ⏸ 跳过 | 已有 `tests/e2e/human_simulator/` |
| D4.1 | 修复 LLM Query Expansion | ⚠️ 文档化 | `docs/reports/D4.1_LLM_Query_Expansion_Fix.md` |
| D4.2 | Streamlit strategy 参数 | ⚠️ 文档化 | 见下方说明 |
| D4.3 | SPA 功能补齐 | ⚠️ 规划中 | 见 UI 设计稿 |

---

## 二、产出文件

### 2.1 自动化脚本

```
scripts/
├── check_api_contract.py      # API 契约检查
├── check_config_usage.py      # 配置项使用检查
└── fix_llm_query_expansion.py # LLM Query Expansion 修复脚本
```

### 2.2 文档报告

```
docs/reports/
└── D4.1_LLM_Query_Expansion_Fix.md  # 修复说明
```

---

## 三、待手动执行的修复

由于当前环境限制，以下修复需要手动执行：

### 3.1 LLM Query Expansion 对接

**文件**：`backend/app/services/qa_service.py`

**需要修改 2 处**（ask 和 stream_ask 方法）：

```python
# 原代码（约第 237-239 行和第 423-425 行）
queries = expand_query(question, mode=expansion_mode, max_extra=2) or [question]

# 修改为：
expansion_llm = None
if expansion_mode in ("llm", "hybrid"):
    try:
        expansion_llm = get_provider_for_task("qa")
    except Exception as e:
        logger.warning("LLM provider not available for query expansion: %s", e)
queries = expand_query(
    question,
    mode=expansion_mode,
    llm_provider=expansion_llm,
    max_extra=2
) or [question]
```

### 3.2 Streamlit 添加 strategy 参数

**文件**：`frontend/pages/2_问答对话.py`

**修改 1**：在设置区域添加策略选择（约第 361 行后添加）

```python
# 在 prompt_version 选择框后添加
strategy = st.selectbox(
    "检索策略",
    options=["default", "high_recall", "high_precision", "low_latency"],
    index=0,
    format_func=lambda x: {
        "default": "默认（平衡）",
        "high_recall": "高召回（探索性）",
        "high_precision": "高精度（精确）",
        "low_latency": "低延迟（快速）",
    }[x],
    help="不同策略适合不同场景",
)
```

**修改 2**：在 payload 中添加 strategy（约第 527 行后添加）

```python
payload = {
    "knowledge_base_id": selected_kb_id,
    "question": cleaned_question,
    "top_k": top_k,
    "conversation_id": conversation_id,
    "history_turns": history_turns,
    "system_prompt_version": prompt_version,
    "strategy": strategy,  # 新增
}
```

### 3.3 Streamlit 展示 snippet

**文件**：`frontend/pages/2_问答对话.py`

**修改**：`_render_citation_with_actions` 函数（约第 117 行）

```python
# 原代码
content_preview = (cite.get("content_preview") or "")[:200]

# 修改为
content_preview = (cite.get("snippet") or cite.get("content_preview") or "")[:200]
```

---

## 四、SPA 功能补齐规划

基于 `docs/design/UI_设计稿_V1.md`，SPA 需要补齐的功能：

### 4.1 高优先级

| 功能 | 预计工时 | 文件 |
|------|----------|------|
| 添加回答风格选择 | 0.5h | `QA.tsx` |
| 添加反馈按钮 | 1h | `QA.tsx` |
| 添加多轮对话 | 2h | `QA.tsx` |
| 添加 URL 导入 | 1h | `KnowledgeBaseDetail.tsx` |

### 4.2 中优先级（新页面）

| 页面 | 预计工时 | 文件 |
|------|----------|------|
| 对话管理 | 2h | `Conversations.tsx` |
| 文件夹同步 | 2h | `FolderSync.tsx` |
| 异步任务 | 1.5h | `Tasks.tsx` |
| 知识库编辑 | 2h | `KnowledgeBaseEdit.tsx` |
| 分享查看 | 1.5h | `ShareView.tsx` |

---

## 五、运行检查脚本

```bash
# API 契约检查
cd e:/Super Fund/enterprise_rag
python scripts/check_api_contract.py

# 配置项使用检查
python scripts/check_config_usage.py

# E2E 测试（需先启动前后端）
python tests/e2e/human_simulator/human_simulator.py
```

---

## 六、总结

任务组 D 的主要工作已完成：

1. ✅ 创建了 2 个自动化检查脚本
2. ✅ 生成了修复文档
3. ⚠️ 代码修复需要手动执行（环境限制）
4. ⚠️ SPA 功能补齐需要后续开发

**建议下一步**：
1. 手动执行 D4.1-D4.3 的代码修复
2. 运行单元测试验证修复
3. 按优先级补齐 SPA 功能
