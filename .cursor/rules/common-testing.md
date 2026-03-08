---
description: "Testing requirements: 80% minimum coverage, TDD workflow, test types"
description_zh: "测试要求：80% 最低覆盖率、TDD 工作流、测试类型"
alwaysApply: true
---

# Testing Requirements / 测试要求

## Minimum Test Coverage: 80% / 最低测试覆盖率：80%

Test Types (ALL required):
测试类型（均需）：
1. **Unit Tests** - Individual functions, utilities, components
   **单元测试** — 单独函数、工具、组件
2. **Integration Tests** - API endpoints, database operations
   **集成测试** — API 端点、数据库操作
3. **E2E Tests** - Critical user flows (framework chosen per language)
   **端到端测试** — 关键用户流程（按语言选框架）

## Test-Driven Development / 测试驱动开发

MANDATORY workflow:
必须遵循的工作流：
1. Write test first (RED)
   先写测试（红）
2. Run test - it should FAIL
   运行测试 — 应失败
3. Write minimal implementation (GREEN)
   写最小实现（绿）
4. Run test - it should PASS
   运行测试 — 应通过
5. Refactor (IMPROVE)
   重构（改进）
6. Verify coverage (80%+)
   验证覆盖率（80%+）

## Troubleshooting Test Failures / 排查测试失败

1. Use **tdd-guide** agent
   使用 **tdd-guide** 代理
2. Check test isolation
   检查测试隔离
3. Verify mocks are correct
   验证 mock 正确
4. Fix implementation, not tests (unless tests are wrong)
   修改实现而非测试（除非测试错误）

## Agent Support / 代理支持

- **tdd-guide** - Use PROACTIVELY for new features, enforces write-tests-first
  **tdd-guide** — 对新功能主动使用，强制先写测试
