# Enterprise RAG SPA（前端）

- **技术栈**：Vite + React 18 + TypeScript + React Router
- **启动**：`npm install && npm run dev`，默认 http://localhost:3000
- **连接后端**：开发时 Vite 代理将 `/api`、`/health` 转发到 `http://localhost:8000`；生产环境配置 `VITE_API_BASE` 为后端地址（或同域则留空）。

## 页面

- `/login` 登录
- `/` 首页
- `/knowledge-bases` 知识库列表
- `/qa` 问答（流式）
- `/dashboard` 检索质量看板
