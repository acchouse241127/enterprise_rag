---
description: "Core coding style rules: immutability, file organization, error handling, input validation"
description_zh: "核心编码风格规则：不可变性、文件组织、错误处理、输入验证"
alwaysApply: true
---

# Coding Style / 编码风格

## Immutability (CRITICAL) / 不可变性（关键）

ALWAYS create new objects, NEVER mutate existing ones:
始终创建新对象，切勿原地修改现有对象：

```
// Pseudocode
WRONG:  modify(original, field, value) → changes original in-place
CORRECT: update(original, field, value) → returns new copy with change
```

Rationale: Immutable data prevents hidden side effects, makes debugging easier, and enables safe concurrency.
理由：不可变数据可避免隐藏副作用、便于调试并支持安全并发。

## File Organization / 文件组织

MANY SMALL FILES > FEW LARGE FILES:
多小文件优于少大文件：
- High cohesion, low coupling
  高内聚、低耦合
- 200-400 lines typical, 800 max
  典型 200–400 行，最多 800 行
- Extract utilities from large modules
  从大模块抽取工具函数
- Organize by feature/domain, not by type
  按功能/领域组织，不按类型

## Error Handling / 错误处理

ALWAYS handle errors comprehensively:
始终全面处理错误：
- Handle errors explicitly at every level
  在每一层显式处理错误
- Provide user-friendly error messages in UI-facing code
  在面向 UI 的代码中提供友好错误信息
- Log detailed error context on the server side
  在服务端记录详细错误上下文
- Never silently swallow errors
  切勿静默吞掉错误

## Input Validation / 输入验证

ALWAYS validate at system boundaries:
始终在系统边界验证：
- Validate all user input before processing
  处理前验证所有用户输入
- Use schema-based validation where available
  在可用处使用基于 schema 的验证
- Fail fast with clear error messages
  快速失败并给出清晰错误信息
- Never trust external data (API responses, user input, file content)
  切勿信任外部数据（API 响应、用户输入、文件内容）

## Code Quality Checklist / 代码质量检查清单

Before marking work complete:
标记工作完成前：
- [ ] Code is readable and well-named
   代码可读、命名清晰
- [ ] Functions are small (<50 lines)
   函数简短（<50 行）
- [ ] Files are focused (<800 lines)
   文件聚焦（<800 行）
- [ ] No deep nesting (>4 levels)
   无深层嵌套（>4 层）
- [ ] Proper error handling
   错误处理得当
- [ ] No hardcoded values (use constants or config)
   无硬编码（使用常量或配置）
- [ ] No mutation (immutable patterns used)
   无原地修改（使用不可变模式）
