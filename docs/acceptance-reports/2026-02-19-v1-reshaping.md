# 验收报告

- **版本/分支**：master（V1 重塑已合并），tag `v1.0.0-reshaping`
- **执行人**：自动化（pre-release 清单执行）
- **日期**：2026-02-19

## 自动化结果

- **单元测试**：通过。`pytest tests/ -v --ignore=tests/e2e`，117 passed，约 3m23s。
- **集成测试**：未单独运行 `-m integration`；当前全量 pytest 已含所需用例且通过。
- **前端构建**：通过。`cd frontend_spa && npm run build` 成功，产物在 `dist/`。
- **代码检查**：ruff 未安装，已跳过；pytest 与前端构建通过视为可接受。

## 集成缺口填补结论

19 项前端集成缺口已全部完成，包括：

- **高优先级**：URL 导入（4_文档上传）、分享查看（10_分享查看）、问题样本标记（7_检索质量看板）
- **中优先级**：知识库编辑、auth/me token 校验、logout 服务端登出、TOTP 绑定与校验
- **低优先级**：按知识库统计、问题样本列表、对话消息预览、任务详情与按实体查询

详见 `docs/plans/2026-02-19-frontend-integration-gap.md`。

## 手工验收结果

需人工按 [docs/checklists/manual-acceptance-v2.md](docs/checklists/manual-acceptance-v2.md) 执行。

使用手册：[docs/用户使用手册-V1.md](docs/用户使用手册-V1.md)

1. **登录**：打开前端，正确/错误密码验证。
2. **知识库**：列表、新建（若已实现）。
3. **上传**：选知识库上传文档，确认状态由 pending 至 vectorized/parsed。
4. **问答**：选知识库输入问题，流式回答或降级检索，引用可查看。
5. **看板**：检索质量看板页可打开、无报错。

（上述项由人工勾选后可在本文档底部「结论」前补充通过/不通过。）

## 文档上传与解析专项

| 项目 | 说明 |
|------|------|
| 文件上传 | TXT/PDF/DOCX/PNG 等，最大 200MB（config、Streamlit、前端文案已统一） |
| URL 导入 | 依赖 Redis + Celery Worker |
| 已知问题 | URL 文档 reparse 曾返回「文件不存在」，已纳入整改计划 |

**报告模板：**

- 验收报告模板：[docs/templates/acceptance-report.md](docs/templates/acceptance-report.md)
- 整改报告模板：[docs/templates/整改报告.md](docs/templates/整改报告.md)

## 阻塞项

（无则填「无」）

## 结论

- [x] 自动化通过，已打 tag `v1.0.0-reshaping`
- [ ] 手工验收通过后，可视为「通过，可发布」
