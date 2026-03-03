# Enterprise RAG 前端对比：React SPA 与 Streamlit 详解

本文结合本项目，对两个前端入口做技术结构、功能与使用场景的详细说明。

---

## 一、React SPA 前端（frontend_spa，端口 3000）

### 1.1 技术栈与工程结构

| 项目 | 说明 |
|------|------|
| **技术栈** | Vite 5 + React 18 + TypeScript + React Router 6 |
| **包管理** | npm，`package.json` 中仅核心依赖：react、react-dom、react-router-dom |
| **构建** | `npm run dev` 开发（HMR），`npm run build` 产出静态资源，`npm run preview` 本地预览构建结果 |
| **入口** | `index.html` → `src/main.tsx` → `App.tsx`（路由在此配置） |

目录结构概览：

```
frontend_spa/
├── index.html
├── package.json
├── vite.config.ts          # 端口 3000，/api、/health 代理到 8000
├── src/
│   ├── main.tsx
│   ├── App.tsx              # 路由：/login, /, /knowledge-bases, /qa, /dashboard
│   ├── index.css            # 全局样式（极简：box-sizing + body + #root）
│   ├── auth.ts              # 登录态：localStorage 存 token，getToken/setToken/logout/isAuthenticated
│   ├── api.ts               # 封装 fetch：Bearer 鉴权、401 自动登出、统一 request + 具体接口
│   └── pages/
│       ├── Login.tsx
│       ├── Home.tsx
│       ├── KnowledgeBases.tsx
│       ├── QA.tsx
│       └── Dashboard.tsx
```

- **无 UI 组件库**：按钮、输入框、列表均为原生 HTML + 内联 style，风格极简。
- **无状态管理库**：仅用 React 本地 state（useState）和少量 useEffect 拉数。

### 1.2 路由与鉴权

- **路由**（`App.tsx`）：
  - `/login`：登录页，无鉴权。
  - `/`、`/knowledge-bases`、`/qa`、`/dashboard`：由 `RequireAuth` 包裹，未登录则重定向到 `/login`。
  - 其余路径 `*` → 重定向到 `/`。
- **鉴权**：`auth.ts` 用 `localStorage` 的 `enterprise_rag_token`；`api.ts` 的 `request()` 在 401 时调用 `logout()` 并抛错（前端会跳转登录）。

### 1.3 与后端对接

- **开发环境**：Vite 将 `/api`、`/health` 代理到 `http://localhost:8000`，因此相对路径请求会打到本机后端。
- **生产**：通过环境变量 `VITE_API_BASE` 配置后端根地址（同域可留空）。
- **接口使用**：
  - 登录：`POST /api/auth/login`，写入 token。
  - 当前用户：`GET /api/auth/me`（api 中有定义，未在页面中显式用到）。
  - 知识库：`GET /api/knowledge-bases`；文档：`GET /api/knowledge-bases/:id/documents`。
  - 问答流式：`POST /api/qa/stream`，读 `ReadableStream`，解析 SSE 风格 `data: {...}`，取 `type=== "chunk"` 的 content 拼成答案。
  - 看板：`GET /api/retrieval/dashboard`，结果以 JSON 展示。

### 1.4 各页面职责简述

| 路径 | 文件 | 功能 |
|------|------|------|
| `/login` | `Login.tsx` | 用户名/密码表单，提交调 login()，成功写 token 并跳转首页。错误信息在页上展示。 |
| `/` | `Home.tsx` | 首页：顶部导航（首页/知识库/问答/看板/退出），下方文案「请从上方导航进入…」。 |
| `/knowledge-bases` | `KnowledgeBases.tsx` | 拉取知识库列表，以列表展示 `name (ID: id)`，无创建/删除/上传。 |
| `/qa` | `QA.tsx` | 下拉选知识库、文本框输入问题、按钮「提问」；流式展示答案（拼接 chunk）；无历史、无引用来源 UI。 |
| `/dashboard` | `Dashboard.tsx` | 请求 `/api/retrieval/dashboard`，将返回的 `data` 用 `<pre>` 展示 JSON。 |

整体定位：**最小可用入口**——登录、看知识库、提问、看看板数据，满足「能跑通主流程」，不做文档上传、对话管理、任务列表等。

### 1.5 开发与部署

- **本地开发**：`cd frontend_spa && npm install && npm run dev`，浏览器访问 http://localhost:3000 。
- **部署**：`npm run build` 生成 `dist/`，由任意静态服务器托管（Nginx、对象存储等）；需保证 `/api`、`/health` 反向代理到后端或前端配置 `VITE_API_BASE` 指向后端。

### 1.6 在本项目中的优缺点（简要）

- **优点**：纯前端、路由清晰、易扩展为产品级 UI；与后端解耦；可做 SEO/ PWA 等。
- **缺点**：当前功能少（无上传、无对话管理、无任务、无知识库编辑）；样式简单；需自己实现更多页面和交互。

---

## 二、Streamlit 前端（frontend，端口 8501）

### 2.1 技术栈与工程结构

| 项目 | 说明 |
|------|------|
| **技术栈** | Python 3.11 + Streamlit + requests |
| **依赖** | `requirements.txt` 仅 streamlit、requests；运行环境多为 Docker（见 `Dockerfile`）。 |
| **入口** | `系统介绍.py`（`streamlit run 系统介绍.py`），侧边栏自动根据 `pages/` 下文件名生成多页。 |
| **端口** | 8501（可在 `config.toml` 与 Docker 映射中修改）。 |

目录结构概览：

```
frontend/
├── 系统介绍.py              # 入口：系统介绍首页 + 功能导航说明
├── Dockerfile               # Python 3.11-slim，streamlit run 系统介绍.py
├── requirements.txt
├── .streamlit/
│   └── config.toml          # server/browser/runner 配置，headless、端口等
├── feedback.py              # 统一反馈：loading、err_network、err_timeout、err_business、success_msg 等
├── operation_log.py         # 请求封装：logged_get、logged_post 等（可带操作名，便于排查）
├── pages/
│   ├── 1_登录.py
│   ├── 2_问答对话.py
│   ├── 3_知识库管理.py
│   ├── 4_文档上传.py
│   ├── 5_对话管理.py
│   ├── 6_文件夹同步.py
│   ├── 7_检索质量看板.py
│   ├── 8_异步任务.py
│   └── 9_知识库编辑.py
```

- **页面顺序**：由文件名前的数字决定侧边栏顺序（1 登录 → 2 问答 → … → 9 知识库编辑）。
- **共享逻辑**：`feedback.py` 统一加载/错误/成功提示；`operation_log.py` 统一发请求；各页通过 `st.session_state["access_token"]` 存 token，`build_headers()` 统一带 Authorization。

### 2.2 鉴权与后端对接

- **鉴权**：登录页 `1_登录.py` 调用 `POST .../auth/login`（支持 username、password、totp_code），成功将 `access_token` 写入 `st.session_state["access_token"]`；各功能页开头 `check_auth()`，无 token 则提示并引导到登录页。
- **后端地址**：环境变量 `API_BASE_URL`（默认 `http://localhost:8000/api`），Docker 中常设为 `http://backend:8000/api`。
- **请求**：各页用 `logged_get` / `logged_post` 等，自动带 `build_headers()` 的 Bearer；超时、连接错误等由 `feedback` 模块统一提示（如「无法连接到服务器」）。

### 2.3 各页面职责简述

| 侧边栏 | 文件 | 功能 |
|--------|------|------|
| 系统介绍 | `系统介绍.py` | 首页：登录状态提示、系统介绍文案、功能导航卡片（登录/知识库/文档上传/RAG 问答/对话管理/看板与其它）、快速开始步骤、支持格式说明。 |
| 登录 | `1_登录.py` | 表单：用户名、密码、TOTP；提交后写 session_state，支持「退出登录」；页底有测试账号说明。 |
| 问答对话 | `2_问答对话.py` | 选知识库、输入问题；可配置回答风格（A/B/C）、检索数等；流式输出；问题完善度检查与风格化提示；展示引用来源；多轮对话与历史。 |
| 知识库管理 | `3_知识库管理.py` | 知识库列表（支持排序）、创建、删除；进入某知识库可看文档列表、解析/向量化状态、下载、删除文档。 |
| 文档上传 | `4_文档上传.py` | 选择知识库 → 上传文件（多文件）；展示该库下文档列表与状态。 |
| 对话管理 | `5_对话管理.py` | 对话列表（可按知识库筛选）；导出为 MD/PDF/Word；生成分享链接（免登录查看）。 |
| 文件夹同步 | `6_文件夹同步.py` | 配置与知识库绑定的本地/远程文件夹同步任务，查看同步状态（idle/running/success/failed）等。 |
| 检索质量看板 | `7_检索质量看板.py` | 按知识库、日期范围拉取检索统计；图表/表格展示；与后端 `/api/retrieval/stats`、`/api/retrieval/stats/by-date` 等对接。 |
| 异步任务 | `8_异步任务.py` | 异步任务列表，按类型、状态筛选；查看任务进度与结果。 |
| 知识库编辑 | `9_知识库编辑.py` | 选择知识库与文档，在线编辑内容或调整分块参数等。 |

可见 Streamlit 端**覆盖了当前后端暴露的主要能力**：登录（含 TOTP）、知识库 CRUD、文档上传与列表、RAG 问答（含风格与引用）、对话管理与导出/分享、文件夹同步、检索看板、异步任务、知识库编辑。

### 2.4 配置与运行方式

- **本地**：安装依赖后 `streamlit run 系统介绍.py --server.port=8501`（或使用 `run.bat`）；需本机可访问后端（如 8000）。
- **Docker**：`docker compose --profile full up -d` 会启动 `frontend` 服务，映射 `FRONTEND_PORT:8501`，环境变量 `API_BASE_URL=http://backend:8000/api`，与 backend、postgres、chromadb、redis、worker 等同网。

### 2.5 在本项目中的优缺点（简要）

- **优点**：功能完整，与后端一一对应；Python 写页面，后端开发者易维护；统一反馈与请求封装，体验一致；适合内部/运维/演示。
- **缺点**：UI 和交互由 Streamlit 框架决定，定制程度不如 React；多页重跑脚本、状态在 session_state，复杂交互需理解 rerun 与 cache；不适合做强品牌化、强交互的产品前台。

---

## 三、对比小结与使用建议

### 3.1 功能覆盖（本项目内）

| 能力 | React SPA (3000) | Streamlit (8501) |
|------|------------------|------------------|
| 登录（含 TOTP） | 仅账号密码 | 账号密码 + TOTP |
| 首页/系统介绍 | 简单导航文案 | 详细说明 + 功能导航 |
| 知识库列表/创建/删除 | 仅列表 | 列表 + 创建 + 删除 + 文档列表与状态 |
| 文档上传 | 无 | 有 |
| RAG 问答 | 选库 + 问题 + 流式答案 | 同上 + 风格/检索数/引用/多轮/完善度提示 |
| 对话管理（导出/分享） | 无 | 有 |
| 文件夹同步 | 无 | 有 |
| 检索质量看板 | 有（原始 JSON） | 有（图表/筛选/日期） |
| 异步任务 | 无 | 有 |
| 知识库编辑 | 无 | 有 |

### 3.2 技术维度简要对比

| 维度 | React SPA | Streamlit |
|------|-----------|-----------|
| 语言/栈 | TypeScript/React/Vite | Python/Streamlit |
| 状态 | 组件 state + localStorage | st.session_state + @st.cache_data |
| 请求 | fetch 封装（api.ts） | requests + operation_log + feedback |
| 样式 | 手写 CSS/内联，极简 | 框架默认 + 少量 st 布局 |
| 路由/多页 | React Router 单页 | 多脚本多页（文件名即菜单） |
| 部署 | 静态资源 + 反向代理 | 容器跑 Streamlit 进程 |

### 3.3 使用建议（结合本项目）

- **以「功能全、快速用、内部用」为主**：用 **Streamlit（8501）**，上传、对话管理、任务、知识库编辑等都可用。
- **以「对外产品、长期迭代 UI/UX」为主**：用 **React SPA（3000）** 作为主入口，按需在 SPA 中补齐上传、对话管理、看板可视化等（调用现有后端 API）。
- **两者可并存**：同一后端，不同入口；例如日常用 3000 做问答，需要上传或任务时开 8501。

---

## 四、文档与引用

- SPA：`frontend_spa/README.md`，路由与代理见 `frontend_spa/vite.config.ts`、`frontend_spa/src/App.tsx`。
- Streamlit：入口与页面见 `frontend/系统介绍.py`、`frontend/pages/*.py`；运行与 Docker 见 `frontend/Dockerfile`、项目根 `docker-compose.yml`（profile full）。
- 后端 CORS 已允许 `http://localhost:3000` 等前端 origin，两个前端均可与同一后端协同工作。
