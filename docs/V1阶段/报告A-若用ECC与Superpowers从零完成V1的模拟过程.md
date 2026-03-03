# 报告 A：若用 ECC 与 Superpowers 从零完成 V1 的详细模拟过程

本文档严格依据 **ECC（Everything Claude Code）** 与 **Superpowers** 的已安装能力与流程，模拟「从项目启动到 V1（MVP）完成」的**完整过程**，并详细记录每一步应发生的事、产出的文档、以及用到的规则/代理/命令/技能。V1 范围以 README 中 v1.0.0 MVP 为准：用户认证（JWT + TOTP）、知识库管理、文档处理（多格式）、RAG 智能问答（流式、引用溯源）、QA 降级展示等。

---

## 一、前提与约定

- **工具**：项目已按方案 B 安装 ECC（rules/agents/commands/skills）与 Superpowers（.cursor/skills/superpowers/），且规则 **superpowers-workflow.md** 已启用（新功能/大改时先查 Superpowers 技能）。
- **流程原则**：新功能/大改必须先走 **brainstorming**，禁止未澄清需求、未获设计确认就写代码；设计确认后必须接 **writing-plans**；实施时用 **executing-plans** 或 **subagent-driven-development**；完成前必须 **verification-before-completion**，收尾必须 **finishing-a-development-branch**。
- **ECC 配合**：单点能力（规划、TDD、审查、安全、数据库、文档、验证）用 ECC 的 plan/tdd/code-review/python-review/security-reviewer/database-reviewer/doc-updater/verify/test-coverage 等。

---

## 二、阶段 0：项目启动与 ECC 规则生效

| 步骤 | 动作 | 产出 / 说明 |
|------|------|-------------|
| 0.1 | 在 Cursor 中打开项目，确认 .cursor/rules 已存在 | ECC 的 common-*、python-*、superpowers-workflow 在对话中自动参与决策 |
| 0.2 | 用户提出「做一个企业知识库 RAG 问答系统，要能登录、建知识库、上传文档、基于文档问答」 | 触发 superpowers-workflow：属于「新功能/大改」，应先查 .cursor/skills/superpowers/ |
| 0.3 | AI 读取 **using-superpowers** 与 **brainstorming**，宣布先做需求与设计，不写代码 | 建立「先查技能再响应」的纪律，进入 brainstorming 流程 |

**所用能力**：superpowers-workflow（规则）、using-superpowers、brainstorming（技能）。

---

## 三、阶段 1：需求澄清与设计（Superpowers：brainstorming）

Brainstorming 技能要求：探索项目背景 → 逐条澄清问题 → 提出 2～3 种方案与取舍 → 分节呈现设计并每节获用户确认 → 写设计文档 → **终止状态是调用 writing-plans**，不得调用任何实现类技能。

| 步骤 | 动作 | 产出 / 说明 |
|------|------|-------------|
| 1.1 | **Explore project context**：查看当前目录、是否有既有代码或文档 | 确认是绿场项目或已有骨架 |
| 1.2 | **Ask clarifying questions**：一次一问，澄清目标用户、部署方式、是否要双因素认证、文档格式范围、是否必须流式输出、是否有离线/降级需求等 | 记录约束与成功标准 |
| 1.3 | **Propose 2–3 approaches**：例如（A）单体 FastAPI+Streamlit + ChromaDB，（B）前后端分离 + 向量库托管，（C）纯本地无后端；给出推荐（如 A）及理由 | 方案对比与推荐 |
| 1.4 | **Present design**：分节呈现（架构、认证、知识库与文档、RAG 管道、前端交互、错误与降级），每节后问「这样是否合适？」 | 用户逐节确认 |
| 1.5 | **User approves design**：用户对整体设计说「可以」 | 设计确认 |
| 1.6 | **Write design doc**：保存到 `docs/plans/YYYY-MM-DD-enterprise-rag-v1-design.md`（或等价路径），并提交 | 可追溯的设计文档 |
| 1.7 | **Transition to implementation**：**仅**调用 **writing-plans** 技能，不调用 frontend-design、mcp-builder 等实现技能 | 进入计划编写阶段 |

**所用能力**：brainstorming（技能）；可选 ECC **plan** 命令与 **planner** 代理在需求重述与风险识别上做补充。

---

## 四、阶段 2：实施计划编写（Superpowers：writing-plans）

Writing-plans 要求：计划保存到 `docs/plans/YYYY-MM-DD-<feature-name>.md`；每个任务是 2～5 分钟可完成的一步（如「写失败测试」「运行确认失败」「写最小实现」「运行确认通过」「提交」）；计划头部注明「必须用 executing-plans 按任务实施」。

| 步骤 | 动作 | 产出 / 说明 |
|------|------|-------------|
| 2.1 | 宣布使用 writing-plans 技能，根据设计文档拆解 V1 为可执行任务 | — |
| 2.2 | 计划文档**头部**包含：Goal、Architecture、Tech Stack，以及「For Claude: REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task」 | 符合 writing-plans 规范 |
| 2.3 | 任务粒度示例：Task 1 项目骨架（目录、依赖、Docker）；Task 2 数据库与 User 模型；Task 3 认证 API（登录、JWT）；Task 4 知识库 CRUD；Task 5 文档上传与解析；Task 6 向量化与 ChromaDB；Task 7 RAG 检索与 LLM 调用；Task 8 流式 API 与引用溯源；Task 9 QA 降级逻辑；Task 10 Streamlit 前端（登录/知识库/文档/问答）；Task 11 安全与限流；Task 12 测试与文档……每个 Task 内再拆为「写失败测试→跑失败→写实现→跑通过→提交」等子步 | `docs/plans/YYYY-MM-DD-enterprise-rag-v1-implementation.md` |
| 2.4 | 用户确认计划后，进入执行阶段 | 明确「按此计划执行」 |

**所用能力**：writing-plans（技能）；可与 ECC **plan** 命令输出做对照或合并。

---

## 五、阶段 3：按计划执行（Superpowers：executing-plans 或 subagent-driven-development）

### 5.1 执行方式二选一

- **executing-plans**：在**独立会话**中按计划执行；默认先执行前 3 个任务 → 报告与验证输出 → 等待反馈 → 下一批；全部完成后**必须**调用 **finishing-a-development-branch**。
- **subagent-driven-development**：在**当前会话**中，每个任务派发子代理；每任务完成后先「规格符合」审查再「代码质量」审查；通过后标记完成，继续下一任务；全部完成后同样必须 **finishing-a-development-branch**。

以下按 **executing-plans** 的节奏描述（subagent 方式在「每任务两阶段审查」上更细，其余一致）。

### 5.2 执行循环（每批任务）

| 步骤 | 动作 | 产出 / 说明 |
|------|------|-------------|
| 3.1 | **Load and Review Plan**：读取计划文件，批判性审阅，有疑问先与用户确认再开始 | 无异议则创建 TodoWrite，开始执行 |
| 3.2 | **Execute Batch**（如首批 3 个任务）：每任务内严格按计划的子步执行（写测试→跑失败→实现→跑通过）；每步若计划要求「运行 pytest/某命令」，必须实际运行并查看输出 | 代码与提交 |
| 3.3 | **Report**：本批完成后展示「实现了什么」「验证命令的完整输出」；说「Ready for feedback」 | 证据化汇报 |
| 3.4 | 用户反馈后：如需修改则修改；否则执行下一批任务，重复 3.2–3.4 | 直至所有任务完成 |
| 3.5 | **完成开发后**：宣布使用 **finishing-a-development-branch**，并**必须**调用该技能 | 进入收尾阶段 |

### 5.3 执行过程中的强制约束（来自 Superpowers）

- **test-driven-development**：实现任何功能或修 bug **前**先写测试、看失败、写最少代码、重构；与 ECC **tdd** 命令 / **tdd-guide** 一致。
- **verification-before-completion**：在声称「完成/通过」**前**必须运行验证命令并确认输出；禁止无证据的「应该通过了」。
- 遇 **bug/测试失败**：先用 **systematic-debugging**（复现→假设→验证）再提修复，再跑验证。
- 执行中若计划要求「用 ECC 做审查」，则在该任务或该批后调用 **python-review** / **code-review** 或 **security-reviewer**（按需）。

**所用能力**：executing-plans 或 subagent-driven-development、test-driven-development、verification-before-completion、systematic-debugging（遇 bug 时）；ECC 的 tdd、python-review、code-review、security-reviewer、database-reviewer（按计划或规则触发）。

---

## 六、阶段 4：收尾（Superpowers：finishing-a-development-branch）

| 步骤 | 动作 | 产出 / 说明 |
|------|------|-------------|
| 4.1 | **Verify Tests**：运行项目测试套件（如 `pytest backend/tests/ -v`），查看完整输出与退出码；若失败则展示失败信息，**不进入 Step 4.2** | 测试通过的证据或失败列表 |
| 4.2 | **Determine Base Branch**：确认当前分支基于 main/master | — |
| 4.3 | **Present Options**：向用户呈现 4 选 1：① 合并回 base 分支（本地）；② 推送并建 PR；③ 保留分支稍后处理；④ 丢弃本分支工作 | 用户选择 |
| 4.4 | **Execute Choice**：按用户选择执行合并/推送/保留/丢弃及后续清理 | 分支状态明确 |

**所用能力**：finishing-a-development-branch（技能）；验证步骤与 **verification-before-completion** 一致。

---

## 七、阶段 5：发布前验证与文档（ECC + Superpowers）

在合并/发布前，按 ECC 与 Superpowers 的推荐再做一轮「发布前」动作（可与 4.1 合并或紧接其后）：

| 步骤 | 动作 | 产出 / 说明 |
|------|------|-------------|
| 5.1 | **verification-before-completion**：再次运行测试/ lint/ 安全相关命令，在回复中贴出**完整输出**，再声称「通过」 | 证据化验证 |
| 5.2 | **verify** 命令 / **test-coverage**：跑覆盖率（如 `pytest --cov`），查缺口；与 **common-testing**（80% 目标）对照 | 覆盖率报告或缺口列表 |
| 5.3 | **security-reviewer** 或 **security-review**：对认证、上传、QA 接口、环境变量、错误信息做一次清单式审查 | 安全审查报告或已修复项 |
| 5.4 | **update-docs** / **doc-updater**：更新 README、用户使用手册（若存在）、API/ 部署说明，与当前功能一致 | 文档更新摘要 |
| 5.5 | **requesting-code-review**（Superpowers）：若团队有审查习惯，按清单请求代码审查；**receiving-code-review**：收到意见后先理解与验证再改 | 可选，视是否有人力 |

**所用能力**：verification-before-completion、verify、test-coverage、security-reviewer/security-review、update-docs/doc-updater、requesting-code-review/receiving-code-review。

---

## 八、全流程串联小结（若用 ECC+Superpowers 从零做 V1）

1. **启动**：用户提出 V1 需求 → superpowers-workflow + using-superpowers + **brainstorming**（澄清→方案→设计确认→写设计 doc→**仅**接 **writing-plans**）。
2. **计划**：**writing-plans** 产出 `docs/plans/YYYY-MM-DD-enterprise-rag-v1-implementation.md`，任务粒度 2～5 分钟/步，计划头要求用 **executing-plans** 实施。
3. **执行**：**executing-plans**（或 subagent-driven-development）分批执行，每步 **test-driven-development**，声称通过前 **verification-before-completion**，遇 bug 用 **systematic-debugging**；按需穿插 ECC 的 tdd、python-review、code-review、security-reviewer、database-reviewer。
4. **收尾**：所有任务完成后 **finishing-a-development-branch**（先验证测试通过→呈现 4 选 1→执行选择）。
5. **发布前**：**verification-before-completion** + **verify** + **test-coverage** + **security-reviewer** + **update-docs**，可选 **requesting-code-review**。

**关键文档产出**：`docs/plans/` 下至少包含设计文档与实施计划；每次「通过」都有对应命令的完整输出作为证据；分支收尾有明确选项与执行结果。

---

## 九、与「实际过程」的差异（供报告 C 对照）

- **需求与设计**：本模拟强制「先 brainstorming → 设计确认 → 写设计 doc → writing-plans」，且禁止在未确认设计前写代码；实际过程有 design_system/ui_specs，但无成文的需求澄清与 `docs/plans/` 实施计划。
- **实施**：本模拟要求「按计划任务逐步执行、每步 TDD、每步验证有输出」；实际过程有 Phase 1.1～1.4 测试分期，但无「可执行计划文档」与「每步验证证据」的书面记录。
- **收尾与发布**：本模拟要求 finishing-a-development-branch（验证→四选一→执行）及发布前 verification + security + docs；实际过程版本历史存在，但未在文档中固定「发布前必须通过的清单」与「分支收尾选项」。

以上差异将在报告 C 中归纳为「你当前逻辑中的问题」，并严格基于 ECC 与 Superpowers 能力给出改进建议。
