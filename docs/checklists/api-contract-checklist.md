# API 契约清单

> 更新日期：2026-02-21
> 状态：审计中

---

## 一、认证模块 (auth)

### POST /api/auth/login

| 项目 | 说明 |
|------|------|
| 功能 | 用户登录 |
| 请求参数 | username, password, totp_code(可选) |
| 响应字段 | access_token, token_type |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ✅ 已调用 | - |

**问题**：无

---

### GET /api/auth/me

| 项目 | 说明 |
|------|------|
| 功能 | 获取当前用户信息 |
| 请求参数 | - |
| 响应字段 | id, username, is_active |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ❌ 未调用 | 优先级低 |
| SPA | ❌ 未调用 | 优先级低 |

**问题**：前后端均未使用

---

### POST /api/auth/totp/setup

| 项目 | 说明 |
|------|------|
| 功能 | 设置 TOTP |
| 请求参数 | - |
| 响应字段 | secret, qr_url |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ❌ 未调用 | 需补齐 |
| SPA | ❌ 未调用 | 需补齐 |

**问题**：后端已实现，前端未对接

---

## 二、知识库模块 (knowledge-bases)

### GET /api/knowledge-bases

| 项目 | 说明 |
|------|------|
| 功能 | 知识库列表 |
| 请求参数 | - |
| 响应字段 | id, name, description, chunk_size, chunk_overlap, created_at |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ✅ 已调用 | - |

**问题**：无

---

### POST /api/knowledge-bases

| 项目 | 说明 |
|------|------|
| 功能 | 创建知识库 |
| 请求参数 | name, description |
| 响应字段 | id, name, description |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ✅ 已调用 | - |

**问题**：无

---

### PUT /api/knowledge-bases/{id}

| 项目 | 说明 |
|------|------|
| 功能 | 更新知识库 |
| 请求参数 | name, description |
| 响应字段 | id, name, description |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ❌ 未调用 | 需补齐 |
| SPA | ❌ 未调用 | 需补齐 |

**问题**：后端已实现，前端未对接

---

### DELETE /api/knowledge-bases/{id}

| 项目 | 说明 |
|------|------|
| 功能 | 删除知识库 |
| 请求参数 | - |
| 响应字段 | - |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ✅ 已调用 | - |

**问题**：无

---

### GET /api/knowledge-bases/{id}/chunk-settings

| 项目 | 说明 |
|------|------|
| 功能 | 获取分块设置 |
| 请求参数 | - |
| 响应字段 | chunk_size, chunk_overlap, is_custom, global_defaults |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ❌ 未调用 | 需补齐 |

**问题**：SPA 未对接

---

### PUT /api/knowledge-bases/{id}/chunk-settings

| 项目 | 说明 |
|------|------|
| 功能 | 更新分块设置 |
| 请求参数 | chunk_size, chunk_overlap |
| 响应字段 | - |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ❌ 未调用 | 需补齐 |

**问题**：SPA 未对接

---

## 三、文档模块 (documents)

### POST /api/knowledge-bases/{id}/documents

| 项目 | 说明 |
|------|------|
| 功能 | 上传文档 |
| 请求参数 | file (multipart) |
| 响应字段 | id, filename, status |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ✅ 已调用 | - |

**问题**：无

---

### POST /api/knowledge-bases/{id}/documents/from-url

| 项目 | 说明 |
|------|------|
| 功能 | 从URL导入 |
| 请求参数 | url |
| 响应字段 | id, source_url, status |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ❌ 未调用 | 需补齐 |

**问题**：SPA 未对接

---

### GET /api/documents/{id}

| 项目 | 说明 |
|------|------|
| 功能 | 文档详情 |
| 请求参数 | - |
| 响应字段 | id, filename, status, parser_message |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ❌ 未调用 | 优先级低 |
| SPA | ❌ 未调用 | 优先级低 |

**问题**：前后端均未使用

---

### DELETE /api/documents/{id}

| 项目 | 说明 |
|------|------|
| 功能 | 删除文档 |
| 请求参数 | - |
| 响应字段 | - |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ✅ 已调用 | - |

**问题**：无

---

## 四、问答模块 (qa)

### POST /api/qa/ask

| 项目 | 说明 |
|------|------|
| 功能 | 非流式问答 |
| 请求参数 | knowledge_base_id, question, top_k, strategy, system_prompt_version, conversation_id, history_turns |
| 响应字段 | answer, citations, retrieved_count, llm_failed, retrieval_log_id |

| 参数 | 后端 | Streamlit | SPA |
|------|------|-----------|-----|
| knowledge_base_id | ✅ | ✅ | ✅ |
| question | ✅ | ✅ | ✅ |
| top_k | ✅ | ✅ | ❌ |
| strategy | ✅ | ❌ | ✅ |
| system_prompt_version | ✅ | ✅ | ❌ |
| conversation_id | ✅ | ✅ | ❌ |
| history_turns | ✅ | ✅ | ❌ |

**问题**：
1. Streamlit 未传 strategy 参数
2. SPA 未传 top_k, system_prompt_version, conversation_id, history_turns

---

### POST /api/qa/stream

| 项目 | 说明 |
|------|------|
| 功能 | 流式问答 (SSE) |
| 请求参数 | 同 /api/qa/ask |
| 响应事件 | answer(delta), citations(data), retrieval_log_id(data), llm_failed(data), error(message) |

| 参数 | 后端 | Streamlit | SPA |
|------|------|-----------|-----|
| strategy | ✅ | ❌ | ✅ |
| system_prompt_version | ✅ | ✅ | ❌ |

**问题**：同 /api/qa/ask

---

### GET /api/qa/strategies

| 项目 | 说明 |
|------|------|
| 功能 | 获取检索策略列表 |
| 请求参数 | - |
| 响应字段 | name, description |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ❌ 未调用 | 需补齐 |
| SPA | ✅ 已调用 | - |

**问题**：Streamlit 未对接

---

## 五、检索日志模块 (retrieval)

### GET /api/retrieval/dashboard

| 项目 | 说明 |
|------|------|
| 功能 | 看板统计数据 |
| 请求参数 | kb_id(可选) |
| 响应字段 | total_queries, avg_top_score, avg_chunks_returned, avg_response_time_ms, helpful_count, not_helpful_count, not_helpful_ratio, sample_count |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ❌ 未调用 | 使用 stats 代替 |
| SPA | ✅ 已调用 | - |

**问题**：Streamlit 使用其他接口代替

---

### POST /api/retrieval/feedback

| 项目 | 说明 |
|------|------|
| 功能 | 提交反馈 |
| 请求参数 | retrieval_log_id, feedback_type |
| 响应字段 | - |

| 对接状态 | Streamlit | SPA |
|----------|-----------|-----|
| 后端 | ✅ 已实现 | - |
| Streamlit | ✅ 已调用 | - |
| SPA | ❌ 未调用 | 需补齐 |

**问题**：SPA 未对接反馈功能

---

## 六、问题汇总

### 高优先级

| 问题 | 影响 | 修复建议 |
|------|------|----------|
| Streamlit 未传 strategy | 用户无法选择检索策略 | 在问答页添加策略下拉框 |
| SPA 未传 system_prompt_version | 用户无法选择回答风格 | 在问答页添加风格下拉框 |
| SPA 未对接反馈 | 无法收集用户反馈 | 在问答页添加反馈按钮 |
| SPA 未对接 URL 导入 | 无法从网址导入 | 在文档页添加 URL 输入 |

### 中优先级

| 问题 | 影响 | 修复建议 |
|------|------|----------|
| SPA 未对接分块设置 | 无法调整分块参数 | 新增知识库编辑页 |
| TOTP 设置未对接 | 无法绑定双因素 | 在设置页添加 TOTP 功能 |
| 知识库编辑未对接 | 无法编辑知识库 | 在列表页添加编辑功能 |

### 低优先级

| 问题 | 影响 | 修复建议 |
|------|------|----------|
| /auth/me 未使用 | 无用户信息展示 | 可选：在 Header 显示用户信息 |
| 文档详情未使用 | 无单文档详情页 | 可选：添加文档详情页 |

---

## 七、修复计划

| 序号 | 任务 | 优先级 | 预计工时 | 负责前端 |
|------|------|--------|----------|----------|
| 1 | Streamlit 添加 strategy 参数 | P0 | 0.5h | Streamlit |
| 2 | SPA 添加 system_prompt_version | P0 | 0.5h | SPA |
| 3 | SPA 添加反馈按钮 | P0 | 1h | SPA |
| 4 | SPA 添加 URL 导入 | P0 | 1h | SPA |
| 5 | SPA 添加分块设置 | P1 | 2h | SPA |
| 6 | SPA 添加多轮对话 | P1 | 2h | SPA |

---

**文档修订历史**

| 版本 | 日期 | 修订人 | 修订内容 |
|------|------|--------|----------|
| v1.0 | 2026-02-21 | 系统生成 | API 契约审计 |
