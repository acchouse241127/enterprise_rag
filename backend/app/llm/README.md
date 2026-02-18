# LLM 按任务类型抽象（策略 B 预留）

- **策略 A**：所有调用使用 `get_provider_for_task(None)` 或 `get_provider_for_task("qa")` 等，均返回同一默认 provider。
- **策略 B**：在配置中为部分 `task_type` 指定不同 model/endpoint，例如：
  - `llm_task_overrides = {"qa": {"model_name": "strong-model"}, "rewrite": {"model_name": "fast-model"}}`
- **预留的 task_type**：`qa`（RAG 生成）、`rewrite`、`summary`、`explain`、`grounding`、`session_summary`、`feedback`、`error_suggestion`、`suggest_question`、`follow_up`、`context_help`、`moderation` 等（见设计文档档三模型配置表）。
