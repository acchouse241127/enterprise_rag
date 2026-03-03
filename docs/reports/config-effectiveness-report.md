# 配置项有效性报告

> 审计日期：2026-02-21
> 审计范围：`backend/app/config.py`

---

## 一、配置项清单

### 1.1 应用配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| app_name | "Enterprise RAG System" | str | 应用名称 |
| app_version | "1.0.0" | str | 应用版本 |
| api_prefix | "/api" | str | API 前缀 |
| log_level | "INFO" | str | 日志级别 |
| env | "development" | str | 环境 |
| cors_origins | "http://localhost:3000,http://localhost:8501" | str | CORS 来源 |

### 1.2 数据库配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| postgres_host | "localhost" | str | PostgreSQL 主机 |
| postgres_port | 5432 | int | PostgreSQL 端口 |
| postgres_db | "enterprise_rag" | str | 数据库名 |
| postgres_user | "enterprise_rag" | str | 用户名 |
| postgres_password | "enterprise_rag" | str | 密码 |
| chroma_host | "localhost" | str | ChromaDB 主机 |
| chroma_port | 8001 | int | ChromaDB 端口 |
| chroma_collection_prefix | "kb" | str | 集合前缀 |

### 1.3 文档处理配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| upload_root_dir | "../data/uploads" | str | 上传目录 |
| max_file_size_mb | 200 | int | 单文件大小上限 |
| chunk_size | 800 | int | 默认分块大小 |
| chunk_overlap | 100 | int | 默认分块重叠 |

### 1.4 检索配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| embedding_model_name | "BAAI/bge-m3" | str | Embedding 模型 |
| embedding_fallback_dim | 64 | int | Embedding 降维维度 |
| retrieval_top_k | 5 | int | 默认检索数量 |
| retrieval_use_keyword | True | bool | 是否启用关键词召回 |
| retrieval_query_expansion_enabled | True | bool | 是否启用查询扩展 |
| retrieval_query_expansion_mode | "rule" | str | 查询扩展模式 |
| retrieval_strategy | "default" | str | 默认检索策略 |

### 1.5 Reranker 配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| reranker_enabled | True | bool | 是否启用 Reranker |
| reranker_model_name | "BAAI/bge-reranker-v2-m3" | str | Reranker 模型 |
| reranker_candidate_k | 12 | int | 候选数量 |

### 1.6 去重与阈值配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| dedup_enabled | True | bool | 是否启用去重 |
| dedup_simhash_threshold | 3 | int | SimHash 阈值 |
| dynamic_threshold_enabled | True | bool | 是否启用动态阈值 |
| dynamic_threshold_min | 0.0 | float | Reranker 最低分 |
| dynamic_threshold_fallback | 0.8 | float | Chroma 距离阈值 |

### 1.7 LLM 配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| llm_provider | "deepseek" | str | LLM 提供者 |
| llm_api_key | "" | str | API Key |
| llm_base_url | "https://api.deepseek.com/v1" | str | API 地址 |
| llm_model_name | "deepseek-chat" | str | 模型名称 |
| llm_timeout_seconds | 60 | int | 超时时间 |
| llm_max_retries | 3 | int | 最大重试次数 |
| llm_retry_base_delay | 1.0 | float | 重试延迟 |
| llm_temperature | 0.2 | float | 温度参数 |
| llm_task_overrides | None | dict | 任务级覆盖 |

### 1.8 认证配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| jwt_secret_key | "please-change-me" | str | JWT 密钥 |
| jwt_algorithm | "HS256" | str | JWT 算法 |
| access_token_expire_minutes | 30 | int | Token 过期时间 |
| refresh_token_expire_days | 7 | int | 刷新 Token 过期 |

### 1.9 功能模块配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| folder_sync_enabled | True | bool | 是否启用文件夹同步 |
| folder_sync_interval_minutes | 30 | int | 同步间隔 |
| folder_sync_batch_size | 50 | int | 批量大小 |
| retrieval_log_enabled | True | bool | 是否启用检索日志 |
| retrieval_log_max_chunks | 20 | int | 日志最大 chunk 数 |
| qa_history_max_turns | 6 | int | 历史轮数 |

### 1.10 Redis & Celery 配置

| 配置项 | 默认值 | 类型 | 说明 |
|--------|--------|------|------|
| redis_url | "redis://localhost:6379/0" | str | Redis 连接 |
| celery_broker_url | "" | str | Celery Broker |

---

## 二、配置项使用状态

### 2.1 完全生效

| 配置项 | 使用位置 | 验证状态 |
|--------|----------|----------|
| postgres_* | database.py | ✅ 正常使用 |
| chroma_* | vector_store.py | ✅ 正常使用 |
| upload_root_dir | document_service.py | ✅ 正常使用 |
| max_file_size_mb | documents.py (API) | ✅ 正常使用 |
| chunk_size | chunker.py | ✅ 正常使用 |
| chunk_overlap | chunker.py | ✅ 正常使用 |
| retrieval_top_k | qa_service.py | ✅ 正常使用 |
| retrieval_use_keyword | qa_service.py | ✅ 正常使用 |
| retrieval_strategy | qa_service.py | ✅ 正常使用 |
| reranker_enabled | qa_service.py | ✅ 正常使用 |
| reranker_candidate_k | qa_service.py | ✅ 正常使用 |
| dedup_enabled | qa_service.py | ✅ 正常使用 |
| dedup_simhash_threshold | dedup.py | ✅ 正常使用 |
| dynamic_threshold_* | qa_service.py | ✅ 正常使用 |
| llm_* | llm/*.py | ✅ 正常使用 |
| jwt_* | security.py | ✅ 正常使用 |
| redis_url | celery_app.py | ✅ 正常使用 |
| folder_sync_enabled | folder_sync_service.py | ✅ 正常使用 |
| retrieval_log_enabled | retrieval_log_service.py | ✅ 正常使用 |

### 2.2 部分生效

| 配置项 | 问题 | 使用位置 | 修复建议 |
|--------|------|----------|----------|
| retrieval_query_expansion_mode | "llm" 模式未完全对接 | qa_service.py | 需要传递 llm_provider 参数 |
| llm_task_overrides | 代码中存在但未实际使用 | llm/__init__.py | 可选实现 |

### 2.3 未使用

| 配置项 | 说明 | 建议 |
|--------|------|------|
| app_name | 仅展示用 | 保留 |
| app_version | 仅展示用 | 保留 |
| qa_history_max_turns | 默认值，前端可覆盖 | 保留 |

---

## 三、问题配置项详情

### 3.1 retrieval_query_expansion_mode

**问题描述**：
- 配置项支持 "rule" / "llm" / "hybrid" 三种模式
- 当设置为 "llm" 或 "hybrid" 时，代码未传递 llm_provider 参数

**代码位置**：
```python
# qa_service.py 第 238-239 行
expansion_mode = getattr(settings, "retrieval_query_expansion_mode", "rule")
queries = expand_query(question, mode=expansion_mode, max_extra=2)
# ❌ 缺少 llm_provider 参数
```

**修复方案**：
```python
# 建议修改
from app.llm import get_provider_for_task

expansion_llm = None
if expansion_mode in ("llm", "hybrid"):
    try:
        expansion_llm = get_provider_for_task("qa")
    except Exception:
        logger.warning("LLM provider not available for query expansion")

queries = expand_query(
    question, 
    mode=expansion_mode, 
    llm_provider=expansion_llm,  # 新增
    max_extra=2
)
```

**影响范围**：
- 使用 "rule" 模式：无影响
- 使用 "llm" 或 "hybrid" 模式：退化为仅返回原始查询

---

## 四、配置建议

### 4.1 生产环境必改项

| 配置项 | 默认值 | 建议值 | 原因 |
|--------|--------|--------|------|
| jwt_secret_key | "please-change-me" | 随机 32+ 字符 | 安全 |
| llm_api_key | "" | 实际 API Key | 功能必需 |
| env | "development" | "production" | 减少错误信息泄露 |

### 4.2 可选项优化

| 配置项 | 默认值 | 建议场景 |
|--------|--------|----------|
| retrieval_query_expansion_mode | "rule" | 追求更全面检索时用 "hybrid" |
| reranker_candidate_k | 12 | 首字延迟高时降到 8 |
| dynamic_threshold_fallback | 0.8 | 结果太少时提高到 0.85 |

---

## 五、配置检查脚本

可使用以下脚本自动检查配置项是否被正确使用：

```bash
# 检查配置项使用情况
cd backend
grep -r "retrieval_query_expansion" app/
grep -r "llm_task_overrides" app/
```

---

## 六、修复计划

| 优先级 | 任务 | 预计工时 | 状态 |
|--------|------|----------|------|
| P0 | 修复 LLM Query Expansion 对接 | 0.5h | 待执行 |
| P1 | 添加配置项使用文档 | 1h | 待执行 |
| P2 | 实现配置项自动化检查脚本 | 2h | 待规划 |

---

**文档修订历史**

| 版本 | 日期 | 修订人 | 修订内容 |
|------|------|--------|----------|
| v1.0 | 2026-02-21 | 系统生成 | 配置项有效性审计 |
