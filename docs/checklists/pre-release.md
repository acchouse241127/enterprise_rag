# 发布前检查清单

- [ ] 代码：`cd backend && ruff check . && ruff format --check .`（若已配置）
- [ ] 单元测试：`cd backend && pytest tests/ -v --ignore=tests/e2e`（需 Postgres/Chroma/Redis 的测试可标记 skip 或 mock）
- [ ] 集成测试：按项目 markers 运行（如 `pytest -m integration`）
- [ ] 前端：`cd frontend_spa && npm run build` 无报错
- [ ] 环境变量：`.env` 与生产配置已核对，无敏感信息提交
- [ ] 文档：README 与部署说明已更新

## 命令汇总（示例）

```powershell
cd backend
pytest tests/ -v -x
cd ../frontend_spa
npm run build
```
