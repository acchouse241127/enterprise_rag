---
description: "Agent orchestration guidelines for parallel task execution and multi-perspective analysis"
description_zh: "代理编排指南：并行任务执行与多视角分析"
alwaysApply: true
---

# Agent Orchestration / 代理编排

## Available Agents / 可用代理

Located in `~/.claude/agents/`:
位于 `~/.claude/agents/`：

| Agent 代理 | Purpose 用途 | When to Use 使用时机 |
|-------|---------|-------------|
| planner | Implementation planning 实现规划 | Complex features, refactoring 复杂功能、重构 |
| architect | System design 系统设计 | Architectural decisions 架构决策 |
| tdd-guide | Test-driven development 测试驱动开发 | New features, bug fixes 新功能、修复 |
| code-reviewer | Code review 代码审查 | After writing code 写代码后 |
| security-reviewer | Security analysis 安全分析 | Before commits 提交前 |
| build-error-resolver | Fix build errors 修复构建错误 | When build fails 构建失败时 |
| e2e-runner | E2E testing 端到端测试 | Critical user flows 关键用户流程 |
| refactor-cleaner | Dead code cleanup 死代码清理 | Code maintenance 代码维护 |
| doc-updater | Documentation 文档 | Updating docs 更新文档 |

## Immediate Agent Usage / 即时使用代理

No user prompt needed:
无需用户提示：
1. Complex feature requests - Use **planner** agent
   复杂功能请求 — 使用 **planner** 代理
2. Code just written/modified - Use **code-reviewer** agent
   刚写好/修改的代码 — 使用 **code-reviewer** 代理
3. Bug fix or new feature - Use **tdd-guide** agent
   修复 bug 或新功能 — 使用 **tdd-guide** 代理
4. Architectural decision - Use **architect** agent
   架构决策 — 使用 **architect** 代理

## Parallel Task Execution / 并行任务执行

ALWAYS use parallel Task execution for independent operations:
始终对独立操作使用并行 Task 执行：

```markdown
# GOOD: Parallel execution 推荐：并行执行
Launch 3 agents in parallel:
并行启动 3 个代理：
1. Agent 1: Security analysis of auth module
   代理 1：auth 模块安全分析
2. Agent 2: Performance review of cache system
   代理 2：缓存系统性能审查
3. Agent 3: Type checking of utilities
   代理 3：工具类型检查

# BAD: Sequential when unnecessary 不推荐：不必要的串行
First agent 1, then agent 2, then agent 3
先代理 1，再代理 2，再代理 3
```

## Multi-Perspective Analysis / 多视角分析

For complex problems, use split role sub-agents:
对复杂问题，使用分工子代理：
- Factual reviewer
  事实审查员
- Senior engineer
  高级工程师
- Security expert
  安全专家
- Consistency reviewer
  一致性审查员
- Redundancy checker
  冗余检查员
