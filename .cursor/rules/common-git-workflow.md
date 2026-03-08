---
description: "Git commit message format, PR workflow, and feature implementation workflow"
description_zh: "Git 提交信息格式、PR 工作流及功能实现工作流"
alwaysApply: true
---

# Git Workflow / Git 工作流

## Commit Message Format / 提交信息格式

```
<type>: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci
类型：feat、fix、refactor、docs、test、chore、perf、ci

Note: Attribution disabled globally via ~/.claude/settings.json.
注意：通过 ~/.claude/settings.json 全局禁用归属。

## Pull Request Workflow / 拉取请求工作流

When creating PRs:
创建 PR 时：
1. Analyze full commit history (not just latest commit)
   分析完整提交历史（不仅是最近一次）
2. Use `git diff [base-branch]...HEAD` to see all changes
   使用 `git diff [base-branch]...HEAD` 查看全部变更
3. Draft comprehensive PR summary
   起草全面的 PR 摘要
4. Include test plan with TODOs
   包含带 TODO 的测试计划
5. Push with `-u` flag if new branch
   若为新分支，使用 `-u` 标志推送

## Feature Implementation Workflow / 功能实现工作流

1. **Plan First / 先规划**
   - Use **planner** agent to create implementation plan
     使用 **planner** 代理创建实现计划
   - Identify dependencies and risks
     识别依赖与风险
   - Break down into phases
     拆分为阶段

2. **TDD Approach / TDD 方法**
   - Use **tdd-guide** agent
     使用 **tdd-guide** 代理
   - Write tests first (RED)
     先写测试（红）
   - Implement to pass tests (GREEN)
     实现使测试通过（绿）
   - Refactor (IMPROVE)
     重构（改进）
   - Verify 80%+ coverage
     验证 80%+ 覆盖率

3. **Code Review / 代码审查**
   - Use **code-reviewer** agent immediately after writing code
     写代码后立即使用 **code-reviewer** 代理
   - Address CRITICAL and HIGH issues
     处理 CRITICAL 与 HIGH 问题
   - Fix MEDIUM issues when possible
     尽可能修复 MEDIUM 问题

4. **Commit & Push / 提交与推送**
   - Detailed commit messages
     详细的提交信息
   - Follow conventional commits format
     遵循 conventional commits 格式
