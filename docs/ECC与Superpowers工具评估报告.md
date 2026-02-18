# Enterprise RAG 项目 — ECC 与 Superpowers 工具评估报告

本文档基于当前已安装的 `.cursor` 配置，对 **Everything Claude Code (ECC)** 与 **Superpowers** 两套工具进行功能梳理，并对照 **enterprise_rag** 项目给出可优化点与使用建议，便于你充分了解并用好这两套能力。

---

## 一、项目概览（enterprise_rag）

| 维度 | 说明 |
|------|------|
| **定位** | 企业知识库问答系统，基于 RAG 的智能问答平台 |
| **后端** | FastAPI + SQLAlchemy + PostgreSQL |
| **向量库** | ChromaDB |
| **前端** | Streamlit |
| **认证** | JWT + TOTP 双因素认证 |
| **CI** | GitHub Actions：lint（ruff/black/isort）、单元测试、集成测试、Docker 构建、全栈回归 |

当前项目已有：分层结构（api/core/models/schemas/services）、pytest 与 markers（integration/slow/llm）、安全与限流、文档解析与 RAG 管道、异步任务、监控与健康检查等。下面两套工具可在**规范、测试、安全、流程、数据库与 API 设计**等方面进一步加持。

---

## 二、Everything Claude Code (ECC) 功能清单

ECC 提供**规则、代理、命令、技能**四类能力，安装在 `.cursor/rules`、`.cursor/agents`、`.cursor/commands`、`.cursor/skills`，并可选 `.cursor/mcp.json`。

### 2.1 规则（Rules）— 始终生效的约束

规则是「始终遵循」的指南，从 ECC 安装到 `.cursor/rules/` 后，会在 Cursor 对话中自动参与决策。

| 文件 | 描述 | 能帮你优化的方向 |
|------|------|------------------|
| **common-coding-style.md** | 核心编码风格：不可变性、文件组织、错误处理、输入校验、代码质量检查清单 | 避免就地修改、保持单文件 200–800 行、边界校验与错误处理统一 |
| **common-security.md** | 强制安全检查：提交前无硬编码密钥、输入校验、防 SQL 注入/XSS/CSRF、鉴权、限流、错误信息不泄露；密钥管理；安全事件响应 | 与现有 JWT/TOTP/限流 对齐，查漏补缺 |
| **common-testing.md** | 测试要求：80% 最低覆盖率、TDD 流程、单元/集成/E2E 分类、失败排查与代理支持 | 巩固 pytest markers、提升覆盖率与 TDD 习惯 |
| **common-git-workflow.md** | Git 提交格式、PR 流程、功能实现工作流 | 提交信息与分支策略规范化 |
| **common-patterns.md** | 通用设计模式：骨架项目、仓库模式、API 响应格式 | 服务层/仓储划分、统一 API 响应结构 |
| **common-performance.md** | 性能与模型选择、上下文窗口管理、扩展思考与构建排错 | 大模型调用与 token 使用策略（与 RAG 相关） |
| **common-hooks.md** | 钩子系统与 TodoWrite 最佳实践 | 任务拆解与进度管理 |
| **common-agents.md** | 代理编排：何时用哪个代理、并行执行、多视角分析 | 在 Cursor 中合理选用 planner/architect/code-reviewer 等 |
| **python-coding-style.md** | Python 编码风格：PEP 8、类型注解、frozen dataclass、black/isort/ruff | 与现有 ruff/black/isort CI 一致，强化类型与风格 |
| **python-patterns.md** | Python 模式：Protocol、dataclass DTO、上下文管理器、生成器 | 接口抽象、DTO 与资源管理 |
| **python-testing.md** | Python 测试：pytest、覆盖率、markers、测试组织 | 与 conftest/markers 对齐，补足用例与覆盖率 |
| **python-security.md** | Python 安全：dotenv 密钥管理、bandit 静态分析 | 密钥与依赖安全扫描 |
| **python-hooks.md** | Python 钩子：black/ruff 自动格式、mypy/pyright、print 警告 | 提交前/保存时格式与类型检查 |
| **superpowers-workflow.md** | Superpowers 工作流：新功能/大改时先查 `.cursor/skills/superpowers/` 并遵循流程 | 与 Superpowers 衔接，先澄清再实现 |

### 2.2 代理（Agents）— 专项角色

代理是「按需调用」的专家角色，在对话中可通过 @ 或说明触发，用于规划、架构、审查、测试、修复等。

| 代理 | 描述 | 能帮你优化的方向 |
|------|------|------------------|
| **planner** | 复杂功能与重构的实施规划专家 | 新 Phase、大功能（如检索质量看板、异步任务）的步骤拆解与排期 |
| **architect** | 系统设计与可扩展性、技术决策 | RAG 管道、服务分层、ChromaDB/Postgres 职责划分、ADR 记录 |
| **code-reviewer** | 代码质量、安全与可维护性审查 | 每次 PR 或关键提交前的系统化审查 |
| **python-reviewer** | Python 专项：PEP 8、Pythonic、类型提示、安全与性能 | 后端与脚本的规范与最佳实践 |
| **tdd-guide** | TDD 专家：先写测试、80%+ 覆盖率 | 新接口、新服务的测试先行与覆盖率 |
| **security-reviewer** | 漏洞与配置风险：密钥、SSRF、注入、不安全加密、OWASP Top 10 | 认证、上传、QA 接口、环境变量与依赖 |
| **database-reviewer** | PostgreSQL：查询优化、表结构、索引、安全与性能 | SQLAlchemy 查询、迁移、ChromaDB 与 Postgres 分工 |
| **build-error-resolver** | 构建/TypeScript 错误快速修复（偏 TS/JS） | 若将来有 TS 前端可用来修构建 |
| **e2e-runner** | E2E 测试：Playwright、关键流程、截图/录屏/追溯 | 登录→知识库→上传→问答等关键路径 E2E |
| **doc-updater** | 文档与 codemap 更新 | README、API 文档、架构图与 CODEMAPS 维护 |
| **refactor-cleaner** | 死代码与重复代码清理（偏 Node/TS 工具链） | 若引入 TS 工具时可做前端/脚本清理 |

与 enterprise_rag **直接相关度最高**的代理：**planner**、**architect**、**code-reviewer**、**python-reviewer**、**tdd-guide**、**security-reviewer**、**database-reviewer**、**e2e-runner**、**doc-updater**。

### 2.3 命令（Commands）— 可复用的工作流入口

命令对应「做某一件完整事情」的流程说明，在 Cursor 中可通过自然语言引用（如「按 plan 命令做」「做一次 python-review」）。

| 命令 | 描述 | 能帮你优化的方向 |
|------|------|------------------|
| **plan** | 重述需求、评估风险、输出分步实施计划，等用户确认后再动代码 | 与 Superpowers 的 writing-plans 互补，做可执行任务列表 |
| **tdd** | 强制 TDD：先接口/测试、再最小实现、80%+ 覆盖率 | 新 API、新 service 时统一 TDD 节奏 |
| **code-review** | 触发代码审查流程 | 提交前或 PR 前做一次系统审查 |
| **python-review** | 调用 python-reviewer，做 PEP 8/类型/安全/习惯用法审查 | 后端与脚本的专项审查 |
| **test-coverage** | 测试覆盖率分析与报告 | 查缺口、补用例 |
| **verify** | 验证循环：检查点与持续验证 | 发布/合并前自动化检查 |
| **update-docs** | 更新文档 | 与 doc-updater 配合维护文档 |
| **update-codemaps** | 更新 codemap | 架构与模块依赖可视化 |
| **build-fix** | 修复构建错误（偏 TS/JS） | 前端或脚本构建失败时使用 |
| **e2e** | 生成并运行 Playwright E2E、截图/录屏/追溯 | 为关键用户路径补 E2E |
| **refactor-clean** | 死代码清理 | 配合 refactor-cleaner 使用 |
| **sessions** | 会话历史与别名管理 | 长周期需求拆成多次会话时使用 |
| **skill-create** | 从本地 git 历史提取模式并生成 SKILL.md | 把本项目惯例沉淀为项目级技能 |
| **instinct-status / instinct-import / instinct-export / evolve** | 持续学习 v2：本能记录、导入导出、聚类成技能 | 团队或跨项目复用经验 |
| **multi-plan / multi-execute / multi-backend / multi-frontend / multi-workflow** | 多模型协作规划与执行 | 复杂多模块时的分工与协作 |
| **pm2** | PM2 服务生命周期（Node 进程管理） | 若用 Node 跑脚本或服务时可用 |
| **go-review / go-test / go-build** | Go 专项审查与构建 | 本项目为 Python，可忽略 |
| **checkpoint / eval / learn** | 检查点、评估与模式提取 | 与验证循环、持续学习配合 |

与 enterprise_rag **最相关**的命令：**plan**、**tdd**、**code-review**、**python-review**、**test-coverage**、**verify**、**update-docs**、**update-codemaps**、**e2e**、**skill-create**。

### 2.4 技能（Skills）— 领域与流程知识

技能是「在特定场景下遵循」的详细流程或模式，放在 `.cursor/skills/`（不含 superpowers 子目录的为 ECC 技能）。

#### 与 Python / 后端 / 数据库 / 安全直接相关

| 技能 | 描述 | 能帮你优化的方向 |
|------|------|------------------|
| **python-patterns** | Pythonic 习惯、PEP 8、类型提示与可维护性 | 后端与脚本的写法统一 |
| **python-testing** | pytest、TDD、fixture、mock、参数化、覆盖率 | 与现有 pytest/conftest 一致，补用例与策略 |
| **django-patterns** | Django 架构、DRF、ORM、缓存、中间件（可部分借鉴到 FastAPI） | REST 设计、分层、缓存策略 |
| **django-security** | 认证、授权、CSRF、SQL 注入、XSS、安全配置 | 与 FastAPI 安全实践对照 |
| **django-tdd** | pytest-django、TDD、factory_boy、API 测试 | 测试策略可迁移到 FastAPI |
| **django-verification** | 迁移、lint、测试与覆盖率、安全扫描、发布前检查 | 可仿照做「FastAPI 发布前检查清单」 |
| **backend-patterns** | 后端架构、API 设计、数据库与服务端实践（Node/Next 为主，思路通用） | API 分层与错误处理 |
| **postgres-patterns** | PostgreSQL 查询优化、表设计、索引与安全（含 Supabase） | SQLAlchemy 与原生 SQL、迁移与索引 |
| **security-review** | 认证、用户输入、密钥、API、支付/敏感功能的安全清单与模式 | 登录、上传、QA、环境变量全面过一遍 |
| **security-scan** | 扫描 .claude/.cursor 配置中的漏洞与错误配置（如 AgentShield） | 若用 Claude Code 或更多 Cursor 配置时可做配置审计 |
| **tdd-workflow** | 新功能/修 bug/重构时的 TDD，含 80%+ 覆盖率与单/集/E2E | 与 common-testing、tdd 命令一致，强化流程 |
| **verification-loop** | 会话内验证体系：检查点与持续验证 | 发布前/合并前自检流程 |
| **project-guidelines-example** | 项目级技能模板与示例 | 可复制为「enterprise_rag 项目指南」技能 |

#### 与前端 / 全栈 / 通用相关

| 技能 | 描述 | 能帮你优化的方向 |
|------|------|------------------|
| **frontend-patterns** | React/Next.js、状态、性能与 UI 实践 | Streamlit 可借鉴状态与性能思路 |
| **coding-standards** | TS/JS/React/Node 通用标准 | 若有前端脚本或未来 TS 可参考 |
| **strategic-compact** | 在逻辑断点建议手动压缩上下文 | 长对话时保留关键上下文 |
| **iterative-retrieval** | 子代理上下文渐进式检索 | 大任务拆子代理时的上下文策略 |
| **continuous-learning** | 从会话中自动提取可复用模式并保存为技能 | 把本项目常见操作沉淀为技能 |
| **continuous-learning-v2** | 基于本能的学习与聚类为技能/命令/代理 | 与 skill-create、instinct-* 配合 |
| **configure-ecc** | ECC 交互式安装与配置 | 增删规则/技能时使用 |
| **eval-harness** | 形式化评估框架（EDD） | 对 RAG 答案质量做评估时可用 |
| **nutrient-document-processing** | 使用 Nutrient API 做文档处理/OCR/提取等 | 若引入第三方文档能力可参考 |

其余技能（springboot-*、golang-*、cpp-*、clickhouse-io、jpa-patterns、java-coding-standards）与当前技术栈关系较弱，可按需浏览。

---

## 三、Superpowers 功能清单

Superpowers 强调**流程**：从「澄清需求」到「计划」再到「执行与收尾」，所有技能安装在 `.cursor/skills/superpowers/`，由规则 **superpowers-workflow.md** 在「新功能/大改/规划」时引导使用。

### 3.1 技能列表与用途

| 技能 | 描述 | 能帮你优化的方向 |
|------|------|------------------|
| **using-superpowers** | 对话开始时建立「先查技能再响应」的纪律，强制在适用时调用技能 | 避免一上来就写代码，先走流程 |
| **brainstorming** | **任何创造性工作前必须使用**：澄清用户意图、需求与设计，再实现 | 新 Phase、新功能前先做需求与方案小节，再开发 |
| **writing-plans** | 有多步任务的需求/规格时，在写代码前拆成可执行计划 | 与 ECC 的 plan 命令配合，产出可执行任务列表 |
| **executing-plans** | 已有书面实施计划时，在独立会话中按计划执行，带审查检查点 | 大需求拆成多会话、每段按计划执行 |
| **subagent-driven-development** | 按实施计划执行时，每个任务用子代理、两阶段审查（规格符合→代码质量） | 复杂需求时在 Cursor 内拆子任务并分步审查 |
| **test-driven-development** | 实现任何功能或修 bug **前**：先写测试、看失败、写最少代码、重构 | 与 ECC 的 tdd-workflow/tdd-guide 一致，强化「先测后写」 |
| **verification-before-completion** | 在声称「完成/修好/通过」**前**：必须跑验证命令并确认输出，证据优先 | 合并/发布前强制跑测试与检查 |
| **requesting-code-review** | 完成任务、实现重要功能或合并前，按清单请求代码审查 | 与 ECC 的 code-review/python-review 衔接 |
| **receiving-code-review** | 收到审查意见后，在改代码前：技术严谨、验证后再改，不盲目采纳 | 提高审查反馈的落实质量 |
| **using-git-worktrees** | 需要与当前工作区隔离或执行实施计划前：创建独立 git worktree、目录选择与安全校验 | 大功能分支、并行实验不污染主工作区 |
| **finishing-a-development-branch** | 实现完成、测试通过后：选择合并/PR/保留/丢弃，并做收尾 | 功能完成后的决策与清理 |
| **dispatching-parallel-agents** | 有 2+ 个无共享状态、无顺序依赖的独立任务时，并行派发 | 多模块可并行开发时的分工 |
| **systematic-debugging** | 遇到 bug、测试失败或异常行为**时**：四阶段根因分析后再提修复 | 减少「猜原因改代码」，先复现、假设、验证 |
| **writing-skills** | 创建/编辑/验证新技能时使用，含测试方法论 | 为 enterprise_rag 写项目专属技能时遵循 |

### 3.2 典型流程串联（与 ECC 的配合）

1. **新功能 / 大改**  
   使用 **brainstorming** → 产出需求与设计要点 → 使用 **writing-plans**（或 ECC **plan**）→ 产出分步计划 → 用户确认后，用 **subagent-driven-development** 或 **executing-plans** 执行，中间用 **test-driven-development** 与 **requesting-code-review**（或 **python-review**）保证质量，最后用 **verification-before-completion** 与 **finishing-a-development-branch** 收尾。

2. **修 bug**  
   使用 **systematic-debugging** 做根因分析 → 用 **test-driven-development** 先写回归测试再修 → 用 **verification-before-completion** 确认。

3. **多任务并行**  
   用 **dispatching-parallel-agents** 拆独立任务，必要时 **using-git-worktrees** 隔离分支。

上述流程与 ECC 的 **planner**、**architect**、**tdd-guide**、**code-reviewer**、**python-reviewer** 可混合使用：流程用 Superpowers，单点能力用 ECC。

---

## 四、针对 enterprise_rag 的优化映射

按领域把「当前项目现状」与「两套工具能带来的优化」对应起来，便于你按需选用。

### 4.1 代码规范与风格

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| 已有 ruff/black/isort CI | common-coding-style、python-coding-style、python-patterns、python-hooks | — | 在对话中显式引用「按 ECC Python 规则」，并可选启用 python-hooks 的本地检查 |
| 服务层与 API 分层清晰 | common-patterns、backend-patterns、python-patterns | — | 新模块按 patterns 做 DTO/Protocol/分层，避免单文件过大（common 的 200–800 行） |
| 希望统一错误处理与边界校验 | common-coding-style（错误处理、输入校验） | — | 在 API 与 service 边界显式校验与错误处理，可让 **python-reviewer** 做专项审查 |

### 4.2 测试与覆盖率

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| pytest、conftest、integration/slow/llm markers | common-testing、python-testing、tdd-workflow、python-testing skill | test-driven-development、verification-before-completion | 新功能前用 **tdd** 或 **test-driven-development**；发布前用 **verification-before-completion** + **test-coverage**；目标 80%+ |
| 有集成测试，E2E 可能不足 | e2e-runner、e2e 命令 | — | 用 **e2e** 为登录→知识库→上传→问答等路径补 Playwright E2E，并纳入 CI |
| 想固化「先测后写」 | tdd-guide、tdd 命令 | test-driven-development | 在 prompt 中约定「新 API/新 service 先走 TDD 技能」 |

### 4.3 安全

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| JWT + TOTP、限流、环境变量 | common-security、python-security、security-review、security-reviewer | — | 用 **security-reviewer** 或 **security-review** 技能做一次全面清单（上传、QA、依赖、错误信息泄露）；与 common-security 对齐提交前检查 |
| 敏感配置在 .env | python-security（dotenv）、common-security（密钥管理） | — | 确保无硬编码、启动时校验必填项；可加 bandit 到 CI |

### 4.4 数据库与 RAG

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| PostgreSQL + SQLAlchemy、ChromaDB | postgres-patterns、database-reviewer | — | 新迁移或复杂查询前用 **database-reviewer**；索引与 N+1 用 **postgres-patterns**；ChromaDB 与 Postgres 职责划分可用 **architect** |
| RAG 管道、检索与排序 | — | — | 逻辑与可观测性可用 **architect** + **doc-updater** 做文档与决策记录 |

### 4.5 API 与文档

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| FastAPI、Swagger/ReDoc | backend-patterns、common-patterns（API 响应） | — | 统一错误响应与分页格式；新接口用 **python-reviewer** 过一遍 |
| README、用户手册、CI 说明 | doc-updater、update-docs、update-codemaps | — | 大改动后用 **update-docs** 或 **doc-updater** 更新 README 与架构说明 |

### 4.6 需求与实施流程

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| Phase 2/3 多需求并行 | planner、plan 命令 | brainstorming、writing-plans、executing-plans、subagent-driven-development | 新 Phase 或大需求：先 **brainstorming** → **plan** 或 **writing-plans** → 确认后 **executing-plans** 或 **subagent-driven-development**；多模块可 **dispatching-parallel-agents** |
| 希望减少「一上来就写代码」 | — | using-superpowers、brainstorming | 在规则或项目说明中强调「新功能先走 Superpowers 流程」 |
| 合并/发布前检查 | verify、test-coverage、security-reviewer | verification-before-completion、requesting-code-review、finishing-a-development-branch | 合并前：**verification-before-completion** + **test-coverage** + **python-review** 或 **code-review**；收尾用 **finishing-a-development-branch** |

### 4.7 调试与收尾

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| 偶发失败或难复现问题 | — | systematic-debugging | 用 **systematic-debugging** 做复现、假设、验证再改代码 |
| 功能完成后的分支处理 | — | finishing-a-development-branch | 完成一坨功能后按选项：合并/PR/保留/丢弃并清理 |

### 4.8 持续沉淀

| 现状 | ECC 能力 | Superpowers 能力 | 建议 |
|------|----------|------------------|------|
| 项目特有惯例未成文 | skill-create、project-guidelines-example、continuous-learning-v2 | writing-skills | 用 **skill-create** 从 git 历史抽模式生成 SKILL；用 **project-guidelines-example** 复制为「enterprise_rag 指南」；新技能按 **writing-skills** 写与验证 |

---

## 五、推荐使用方式速查

- **开新功能 / 大改**：先 **brainstorming**（Superpowers）→ **plan** 或 **writing-plans** → 确认后 **executing-plans** / **subagent-driven-development**，中间用 **test-driven-development** + **python-review** / **code-review**，最后 **verification-before-completion** + **finishing-a-development-branch**。  
- **写新接口 / 新服务**：用 **tdd** 或 **test-driven-development**，再让 **python-reviewer** 或 **code-reviewer** 过一遍。  
- **修 bug**：用 **systematic-debugging** 分析，再 **test-driven-development** 补测与修。  
- **发布/合并前**：**verification-before-completion** + **test-coverage** + **security-review**（或 **security-reviewer**）+ **python-review**。  
- **数据库/查询/迁移**：**database-reviewer** + **postgres-patterns**。  
- **架构决策与文档**：**architect** + **doc-updater** / **update-docs** / **update-codemaps**。  
- **为项目沉淀惯例**：**skill-create**、**project-guidelines-example**、**writing-skills**。

---

## 六、小结表

| 工具 | 核心侧重 | 规则数 | 代理数 | 命令数 | 技能数（约） | 与 enterprise_rag 最相关的部分 |
|------|----------|--------|--------|--------|--------------|----------------------------------|
| **ECC** | 规范、测试、安全、审查、规划、文档、数据库、TDD、验证与持续学习 | 14 | 13 | 30+ | 33（不含 Superpowers） | Python 规则/代理/技能、postgres、security、tdd、plan、e2e、doc、skill-create |
| **Superpowers** | 流程：澄清→计划→执行→审查→收尾 | 1（workflow） | 0 | 0 | 14 | brainstorming、writing-plans、executing-plans、subagent-driven-development、test-driven-development、verification-before-completion、requesting-code-review、systematic-debugging、finishing-a-development-branch |

两者结合使用：**流程用 Superpowers，单点能力与规范用 ECC**，即可在保持当前技术栈与 CI 的前提下，系统化提升需求质量、实施质量和发布前质量。

---

*报告基于当前 `.cursor` 安装内容生成；若你后续增删规则/技能，可据此文档自行更新对应小节。*
