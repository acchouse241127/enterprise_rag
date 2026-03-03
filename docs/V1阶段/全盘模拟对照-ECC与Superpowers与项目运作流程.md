# 全盘模拟对照：ECC、Superpowers 与 enterprise_rag 项目运作流程

本文档基于**项目全部文件**（含运作流程记录）与 **.cursor 下已安装的 ECC、Superpowers**，做**全盘模拟对照**：把两套工具的功能与流程，与项目当前阶段（V1 完成、测试中）、目录结构、CI、文档一一对应，便于你在测试期及后续开发中按场景选用。

---

## 一、需求与范围确认

- **项目状态**：V1 阶段开发已完成，当前在做测试。
- **已安装工具**：everything-claude-code（ECC）、superpowers，安装在 `enterprise_rag/.cursor`（rules、agents、commands、skills，其中 Superpowers 在 `skills/superpowers/`）。
- **本对照目标**：
  1. 完全依据两套工具的**功能与流程**（规则、代理、命令、技能及其串联方式）；
  2. 结合**整个项目**（README、docs、CI、backend/frontend 结构、测试、脚本等，含项目运作流程相关文档）；
  3. 做**全盘模拟对照**：按「项目里会发生什么活动」逐项对应到「该用哪条 ECC/Superpowers 能力、如何走流程」。

下文先提炼项目运作与两工具流程，再给出按活动与按文件/模块的对照表及当前阶段建议。

---

## 二、项目运作流程提炼（来自项目文件）

以下从 README、docs、CI、脚本等提炼出的「项目实际运作方式」。

### 2.1 项目定位与技术栈

| 维度 | 内容（与工具对照相关） |
|------|------------------------|
| 定位 | 企业知识库问答系统，RAG 智能问答平台 |
| 后端 | FastAPI + SQLAlchemy + PostgreSQL |
| 向量库 | ChromaDB |
| 前端 | Streamlit |
| 认证 | JWT + TOTP 双因素认证 |
| CI | GitHub Actions：lint（ruff/black/isort）、单元测试、集成测试、Docker 构建、全栈回归 |

### 2.2 项目结构（与 ECC/Superpowers 触达点）

```
enterprise_rag/
├── backend/app/          ← ECC python-* 规则/代理/技能、Superpowers 执行计划的主要范围
│   ├── api/               ← 接口层：code-review、python-review、security-review 重点
│   ├── core/              ← 安全、数据库、限流：security-review、database-reviewer
│   ├── models/            ← 数据模型：database-reviewer、postgres-patterns
│   ├── schemas/           ← 请求/响应：python-patterns、common-patterns
│   ├── services/          ← 业务逻辑：tdd、python-testing、planner
│   ├── document_parser/   ← 解析与输入：security、输入校验
│   ├── rag/               ← RAG 管道：architect、postgres/Chroma 职责
│   └── llm/               ← LLM 调用：安全与限流
├── frontend/              ← Streamlit：可借鉴 frontend-patterns，E2E 覆盖
├── tests/                 ← pytest、markers：common-testing、tdd-workflow、verification-before-completion
├── docs/                  ← 用户手册、设计、安装与评估文档：doc-updater、update-docs
├── scripts/               ← 启动、回归：verify、verification-before-completion
└── .github/workflows/     ← CI 与「发布前」对应：verify、test-coverage
```

### 2.3 项目里已记录的「运作流程」

- **开发指南**（README）：运行测试（单元/集成/覆盖率）、测试 markers（integration/slow/llm）、Docker 全栈回归、CI 步骤、代码检查（ruff/black/isort）。
- **保姆式使用说明**：五步优化流程——① 全面评估+安全审查 → ② 代码规范与 Python 审查 → ③ 测试与覆盖率 → ④ 文档更新 → ⑤ 发布前验证；每一步对应「你要发的那句话」，本质是 ECC 代理/技能 + Superpowers verification 的串联。
- **安装方案与评估报告**：方案 B（ECC + Superpowers）、新功能/大改用 brainstorming → writing-plans → executing-plans；修 bug 用 systematic-debugging；发布前用 verification-before-completion + verify。
- **版本历史**：v1.0.0 MVP → v2/v3/v4 Phase 2/3 功能，当前为 v4.0.0，说明项目有明确的阶段与发布节奏，与「发布前验证」「finishing-a-development-branch」直接相关。

因此，项目运作可归纳为：**日常开发（含新功能/修 bug）→ 测试与覆盖率 → 发布/合并前验证**；文档中已把 ECC 与 Superpowers 嵌入了这条链路。

---

## 三、两套工具的功能与流程摘要（用于对照）

### 3.1 ECC（Everything Claude Code）

- **规则**（`.cursor/rules/`）：始终生效。含 common-*（编码风格、安全、测试、Git、模式、性能、钩子、代理）、python-*（风格、模式、测试、安全、钩子）、superpowers-workflow（新功能/大改时先查 Superpowers 技能）。
- **代理**（`.cursor/agents/`）：按需调用。与本项目最相关：planner、architect、code-reviewer、python-reviewer、tdd-guide、security-reviewer、database-reviewer、e2e-runner、doc-updater。
- **命令**（`.cursor/commands/`）：可复用工作流。与本项目最相关：plan、tdd、code-review、python-review、test-coverage、verify、update-docs、update-codemaps、e2e、skill-create。
- **技能**（`.cursor/skills/`，不含 superpowers 子目录）：与 Python/后端/数据库/安全直接相关的如 python-patterns、python-testing、postgres-patterns、security-review、tdd-workflow、verification-loop、project-guidelines-example 等。

### 3.2 Superpowers（`.cursor/skills/superpowers/`）

- **流程导向**：由规则 `superpowers-workflow.md` 在「新功能/大改/规划」时引导先查 Superpowers 技能。
- **核心技能与顺序**：
  - **brainstorming**：任何创造性工作前必须用；澄清意图与需求 → 提出方案 → 设计确认 → 写设计 doc → **必然后接 writing-plans**。
  - **writing-plans**：有多步任务时，在写代码前拆成可执行计划；保存到 `docs/plans/YYYY-MM-DD-<feature-name>.md`；计划头部要求用 executing-plans 按任务执行。
  - **executing-plans**：按计划分批执行（默认先 3 个任务）、每批后报告并等待反馈；全部完成后**必须**调用 finishing-a-development-branch。
  - **test-driven-development**：实现或修 bug 前先写测试、看失败、最小实现、重构。
  - **verification-before-completion**：在声称完成/修好/通过前，必须运行验证命令并确认输出；禁止无证据的结论。
  - **requesting-code-review / receiving-code-review**：完成任务或合并前按清单请求审查；收到意见后严谨验证再改。
  - **finishing-a-development-branch**：实现完成、测试通过后，选择合并/PR/保留/丢弃并收尾。
  - **systematic-debugging**：遇 bug/测试失败时四阶段根因分析后再提修复。
  - **dispatching-parallel-agents**：多任务无顺序依赖时可并行派发；**using-git-worktrees**：需隔离时创建 worktree。

---

## 四、按「项目活动」的全盘模拟对照

下面按「你在项目里会做的事」逐项模拟：该活动对应哪些文件/流程，以及应使用的 ECC/Superpowers 能力与顺序。

### 4.1 当前阶段：V1 完成，正在做测试

| 项目活动 | 涉及项目文件/流程 | ECC 能力 | Superpowers 能力 | 模拟对照说明 |
|----------|-------------------|----------|-------------------|--------------|
| 跑通单元/集成测试、看覆盖率 | `backend/tests/`、README 测试命令、CI | common-testing、python-testing 规则；**test-coverage** 命令；tdd-guide、python-reviewer | **verification-before-completion**（每次声称通过前必须跑命令并看输出） | 测试阶段每次说「通过」前，必须执行 verification-before-completion：运行 `pytest`/集成命令，贴出真实输出再下结论。用 test-coverage 出覆盖率报告。 |
| 补测、提高覆盖率 | `backend/tests/`、conftest、markers | **tdd** 命令、**python-testing** 技能、tdd-workflow | **test-driven-development**（先写失败测试再实现） | 补哪块就先写/补对应测试，再跑通；与 CI 的 unit-tests/integration-tests 对齐。 |
| 测试期发现 bug | 任意 backend/app、frontend、tests | code-reviewer、python-reviewer（修完可审查） | **systematic-debugging**（复现→假设→验证再改） | 先走 systematic-debugging 再做修复与回归；修完后可用 verification-before-completion 再跑一遍。 |
| 发布前/合并前检查 | CI 流程、README、scripts | **verify** 命令、**security-reviewer**、**test-coverage** | **verification-before-completion**、**requesting-code-review**、**finishing-a-development-branch** | 先跑 verify + test-coverage + 安全审查；再按 verification-before-completion 出证据；最后用 finishing-a-development-branch 做合并/PR/保留决策。 |

### 4.2 新功能 / 大改（Phase 2/3 或新需求）

| 项目活动 | 涉及项目文件/流程 | ECC 能力 | Superpowers 能力 | 模拟对照说明 |
|----------|-------------------|----------|-------------------|--------------|
| 接到新需求、先澄清与设计 | docs/plans/、backend 模块划分 | **plan** 命令、planner 代理 | **brainstorming**（必选：澄清→方案→设计确认→写设计 doc→**接着 writing-plans**） | 新功能/大改必须先 brainstorming，禁止直接写代码；设计定稿后必须接 writing-plans，不能接其他实现类技能。 |
| 把需求拆成可执行任务 | docs/plans/YYYY-MM-DD-*.md | plan 命令输出、planner | **writing-plans**（保存到 docs/plans/，计划内注明用 executing-plans） | 与 ECC plan 可二选一或互补：Superpowers 强调「可执行步骤+文件级」；ECC plan 强调风险与阶段。 |
| 按计划实施 | backend/app、tests、docs | tdd 命令、python-reviewer、code-reviewer | **executing-plans**（分批执行、每批后报告）、**subagent-driven-development**（子任务+两阶段审查） | 按计划每步跑验证；每批后用 verification-before-completion 再确认；全部完成后必须走 finishing-a-development-branch。 |
| 多模块并行开发 | 多个 api/services 或 frontend/backend 并行 | planner、multi-* 命令（若用多模型） | **dispatching-parallel-agents**、**using-git-worktrees**（隔离分支） | 无共享状态、无顺序依赖时用 dispatching-parallel-agents；需隔离时用 using-git-worktrees。 |

### 4.3 代码质量与安全（日常与发布前）

| 项目活动 | 涉及项目文件/流程 | ECC 能力 | Superpowers 能力 | 模拟对照说明 |
|----------|-------------------|----------|-------------------|--------------|
| 代码风格、类型、单文件过长 | backend/app、.cursor/rules | **python-review** 命令、**python-reviewer** 代理、python-coding-style/python-patterns 规则 | — | 按保姆式说明第 2 步：用 python-reviewer 审查 backend，明确问题直接改。 |
| 安全审查（密钥、输入、限流、错误信息） | backend、.env.example、api/core | **security-reviewer** 代理、**security-review** 技能、common-security 规则 | — | 按保姆式说明第 1 步：全面安全审查，出报告并修明显问题。 |
| 数据库/查询/迁移 | backend/app/models、SQL、ChromaDB 使用 | **database-reviewer**、**postgres-patterns** 技能 | — | 新迁移或复杂查询前用 database-reviewer；索引与 N+1 用 postgres-patterns。 |
| 架构决策与文档 | README、docs、架构说明 | **architect** 代理、**doc-updater**、**update-docs**/ **update-codemaps** | — | 大改动后用 update-docs 或 doc-updater 更新 README 与架构；决策可记入 ADR。 |

### 4.4 文档与沉淀

| 项目活动 | 涉及项目文件/流程 | ECC 能力 | Superpowers 能力 | 模拟对照说明 |
|----------|-------------------|----------|-------------------|--------------|
| 更新 README、用户手册 | README.md、docs/用户使用手册.md | **update-docs** 命令、**doc-updater** 代理 | — | 与保姆式第 4 步一致。 |
| 为项目沉淀惯例、项目级技能 | .cursor/skills/、docs | **skill-create**、**project-guidelines-example** | **writing-skills** | 用 skill-create 从历史抽模式；用 project-guidelines-example 复制为「enterprise_rag 指南」；新技能按 writing-skills 编写与验证。 |

---

## 五、项目文件/模块与 ECC、Superpowers 映射表

便于你按「改的是哪一块」快速选能力。

| 项目路径/模块 | 主要活动 | 推荐 ECC | 推荐 Superpowers |
|---------------|----------|----------|-------------------|
| `backend/app/api/*` | 接口变更、新 API | python-review、code-review、security-reviewer、tdd | test-driven-development、verification-before-completion |
| `backend/app/core/` | 安全、限流、数据库、异常 | security-reviewer、common-security、database-reviewer | verification-before-completion |
| `backend/app/models/` | 表结构、迁移 | database-reviewer、postgres-patterns | — |
| `backend/app/services/` | 业务逻辑、新服务 | tdd、python-reviewer、planner | brainstorming→writing-plans→executing-plans（大改时） |
| `backend/app/rag/` | RAG 管道、检索、向量 | architect、postgres-patterns、database-reviewer | — |
| `backend/app/document_parser/` | 解析、上传、输入 | security-review、python-reviewer、输入校验规则 | — |
| `backend/app/llm/` | LLM 调用、配置 | security、common-performance | — |
| `backend/tests/` | 补测、覆盖率、回归 | test-coverage、tdd、python-testing、common-testing | test-driven-development、verification-before-completion |
| `frontend/` | Streamlit 页面、交互 | 可参考 frontend-patterns；e2e-runner、e2e 命令补 E2E | verification-before-completion（前端验证命令若存在） |
| `docs/` | 用户手册、设计、计划 | doc-updater、update-docs | brainstorming 产出 → docs/plans/；writing-plans 产出 → docs/plans/ |
| `.github/workflows/ci.yml` | CI、发布前 | verify、test-coverage、lint 与测试命令 | verification-before-completion（本地/CI 跑完再声称通过） |
| `scripts/` | 启动、回归脚本 | verify | verification-before-completion（跑回归后再下结论） |

---

## 六、当前阶段（V1 测试期）推荐使用顺序

结合「项目已完成 V1 开发、正在做测试」的现状，推荐按以下顺序做一轮全盘对照使用：

1. **测试与证据**  
   每次声称「测试通过」或「修好」前：  
   - 使用 **verification-before-completion**：实际运行 `pytest`（及集成/回归命令），把完整输出贴出，再下结论。  
   - 使用 **test-coverage**：生成覆盖率报告，与 common-testing（80% 目标）对照。

2. **发现 bug 时**  
   使用 **systematic-debugging**：复现 → 假设 → 验证，再提修复；修完后再次用 verification-before-completion 跑相关用例。

3. **补测与质量**  
   使用 **tdd** 或 **test-driven-development** 补核心 API、认证、RAG 相关测试；用 **python-review** 做一轮 backend 规范与类型审查。

4. **发布/合并前**  
   使用 **verify** + **test-coverage** + **security-reviewer**（或 security-review）做发布前验证；用 **verification-before-completion** 出证据；用 **finishing-a-development-branch** 做合并/PR/保留决策。

5. **后续新功能/Phase**  
   新功能或大改：先 **brainstorming** → **writing-plans**（或 ECC **plan**）→ 确认后 **executing-plans** 或 **subagent-driven-development**；中间用 **test-driven-development** 与 **python-review**/ **code-review**，最后仍用 **verification-before-completion** 与 **finishing-a-development-branch**。

---

## 七、小结

- **全盘模拟对照**：已按「项目活动」（测试、修 bug、新功能、代码质量、安全、文档、发布前）与「项目文件/模块」分别对应到 ECC 与 Superpowers 的具体规则、代理、命令、技能及串联方式。  
- **流程一致**：项目内已有文档（保姆式说明、安装方案、评估报告）中描述的流程，与本对照表一致；当前阶段（V1 测试）重点为 **verification-before-completion**、**test-coverage**、**systematic-debugging**（遇 bug）、以及发布前的 **verify** + **finishing-a-development-branch**。  
- **两套工具分工**：**流程用 Superpowers**（澄清→计划→执行→验证→收尾），**单点能力与规范用 ECC**（审查、覆盖率、安全、数据库、文档、TDD）；两者在 `.cursor` 中已并存，可按上表按场景选用。

若你希望，我可以再根据某一条「项目活动」或某一目录，拆成更细的步骤清单（例如「测试阶段每日检查清单」或「发布前逐条检查命令」）。
