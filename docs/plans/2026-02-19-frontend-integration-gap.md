# 前端集成缺口填补计划（完整版）

> **For AI:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 填补后端已实现但 Streamlit 前端未集成的全部缺口，实现开发与测试闭环。

**Architecture:** 在现有 Streamlit 前端 pages/ 下新增/修改页面，调用现有后端 API。

**Tech Stack:** Python, Streamlit, Requests

---

## 全部未对齐项（共 19 项）

| 优先级 | 模块 | 接口 | 前端缺口 | 状态 |
|--------|------|------|----------|------|
| 高 | documents | POST /documents/from-url | 4_文档上传无入口 | ✅ 已完成 |
| 高 | conversations | GET /conversations/share/{token} | 无分享查看页 | ✅ 已完成 |
| 中 | retrieval | POST /feedback/{id}/mark-sample | 无操作按钮 | ✅ 已完成 |
| 中 | knowledge_bases | PUT /knowledge-bases/{id} | 无编辑入口 | ✅ 已完成 |
| 中 | auth | GET /auth/me | token 校验 | ✅ 已完成 |
| 中 | auth | POST /auth/logout | 服务端登出 | ✅ 已完成 |
| 中 | auth | POST /auth/totp/setup | TOTP 绑定 | ✅ 已完成 |
| 中 | auth | POST /auth/totp/verify | TOTP 校验 | ✅ 已完成 |
| 低 | knowledge_bases | GET /knowledge-bases/{id} | 单库详情 | ✅ 已完成 |
| 低 | documents | GET /documents/{id} | 单文档详情 | ✅ 已完成 |
| 低 | retrieval | GET /retrieval/logs/{id} | 单条日志详情 | ✅ 已完成 |
| 低 | retrieval | GET /stats/by-knowledge-base | 按知识库统计 | ✅ 已完成 |
| 低 | retrieval | GET /retrieval/samples | 问题样本列表 | ✅ 已完成 |
| 低 | conversations | GET /conversations/{id} | 单条对话详情 | ✅ 已完成 |
| 低 | conversations | GET /conversations/{id}/messages | 对话消息列表 | ✅ 已完成 |
| 低 | tasks | GET /tasks/{id} | 任务详情 | ✅ 已完成 |
| 低 | tasks | GET /tasks/entity/{type}/{id} | 按实体查任务 | ✅ 已完成 |
| 运维 | system | GET /system/health | 健康检查 | 前端无需 |
| 运维 | system | GET /metrics | Prometheus | 前端无需 |

---

## 执行批次

### 批次 1：高优先级（✅ 已完成）
- Task 1: URL 导入 ✅
- Task 2: 分享查看页 ✅
- Task 3: 问题样本标记 ✅

### 批次 2：中优先级（✅ 已完成）
- Task 4: 知识库编辑 ✅
- Task 5: 登录页增加 token 校验和服务端登出 ✅
- Task 6: TOTP 绑定与校验流程 ✅

### 批次 3：低优先级（详情展示）（✅ 已完成）
- Task 7: 检索日志详情展开 ✅
- Task 8: 对话详情与消息预览 ✅
- Task 9: 任务详情展示 ✅
- Task 10: 按知识库统计与问题样本列表 ✅

### 批次 4：验证与闭环（✅ 已完成）
- Task 11: 后端单元测试验证 ✅
- Task 12: 前端功能手工验收清单 ✅（见 [manual-acceptance-v2.md](../checklists/manual-acceptance-v2.md)）

---

## 完成标准

1. 所有接口在前端有调用入口
2. 后端测试通过：`pytest tests/ -v`
3. 前端构建通过：`npm run build`
4. 人工验收清单全部勾选
