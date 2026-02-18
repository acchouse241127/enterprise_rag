# 后端方案三预留说明（ToB 多租户、限流、审计）

- **状态**：本轮不实现，仅在模型与配置上预留扩展点。
- **预留内容**：
  - **tenant_id**：`knowledge_bases`、`users` 表已增加 `tenant_id` 字段（可为 NULL）；后续 ToB 多租户时按 tenant 过滤数据。
  - **限流**：按租户/用户的限流与配额接口或配置项，在 ToB 就绪阶段接入（如 RATE_LIMIT_PER_TENANT、QUOTA_PER_ORG）。
  - **审计**：操作与检索审计日志接口或表结构，在 ToB 就绪阶段接入（如 AUDIT_LOG_ENABLED、审计表）。
- **参考**：设计文档 `2026-02-18-enterprise-rag-reshaping-design.md` 第七节。
