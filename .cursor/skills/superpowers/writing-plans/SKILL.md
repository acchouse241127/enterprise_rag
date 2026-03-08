---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
description_zh: 当你有规格或需求用于多步骤任务时、在写代码之前使用
---

# Writing Plans / 编写计划

## Overview / 概述

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.
编写全面的实现计划，假定工程师对本代码库零了解且品味存疑。记录他们需要知道的一切：每项任务涉及的文件、代码、测试、可能需要查阅的文档、如何测试。将整体计划拆成小块任务。DRY、YAGNI、TDD、频繁提交。

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.
假定他们是熟练开发者，但对我们的工具集或问题域几乎一无所知。假定他们对良好测试设计不甚了解。

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."
**开始时宣布：** "我正使用 writing-plans 技能创建实现计划。"

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).
**上下文：** 应在专用 worktree 中运行（由 brainstorming 技能创建）。

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`
**计划保存到：** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Bite-Sized Task Granularity / 小块任务粒度

**Each step is one action (2-5 minutes):**
**每步为一个动作（2–5 分钟）：**
- "Write the failing test" - step
  「编写失败测试」— 一步
- "Run it to make sure it fails" - step
  「运行以确认失败」— 一步
- "Implement the minimal code to make the test pass" - step
  「实现使测试通过的最小代码」— 一步
- "Run the tests and make sure they pass" - step
  「运行测试并确认通过」— 一步
- "Commit" - step
  「提交」— 一步

## Plan Document Header / 计划文档头部

**Every plan MUST start with this header:**
**每个计划必须以以下头部开头：**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]
**目标：** [一句话描述构建内容]

**Architecture:** [2-3 sentences about approach]
**架构：** [2–3 句话描述方案]

**Tech Stack:** [Key technologies/libraries]
**技术栈：** [关键技术/库]

---
```

## Task Structure / 任务结构

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Remember / 记住
- Exact file paths always
  始终使用精确文件路径
- Complete code in plan (not "add validation")
  计划中写出完整代码（而不是「添加验证」）
- Exact commands with expected output
  精确命令及预期输出
- Reference relevant skills with @ syntax
  用 @ 语法引用相关技能
- DRY, YAGNI, TDD, frequent commits
  DRY、YAGNI、TDD、频繁提交

## Execution Handoff / 执行交接

After saving the plan, offer execution choice:
保存计划后，提供执行选项：

**"Plan complete and saved to `docs/plans/<filename>.md`. Two execution options:"**
**「计划已完成并保存到 `docs/plans/<filename>.md`。两种执行方式：」**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration
**1. 子代理驱动（本会话）** — 每任务派遣新子代理，任务间审查，快速迭代

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints
**2. 并行会话（独立）** — 用 executing-plans 开新会话，带检查点批量执行

**Which approach?"**
**选择哪种方式？」**

**If Subagent-Driven chosen:**
**若选子代理驱动：**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
  **必须子技能：** 使用 superpowers:subagent-driven-development
- Stay in this session
  保持在本会话
- Fresh subagent per task + code review
  每任务新子代理 + 代码审查

**If Parallel Session chosen:**
**若选并行会话：**
- Guide them to open new session in worktree
  引导在 worktree 中开新会话
- **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans
  **必须子技能：** 新会话使用 superpowers:executing-plans
