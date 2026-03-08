---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
description_zh: 当你有一份写好的实现计划，需要在独立会话中执行并有审查检查点时使用
---

# Executing Plans / 执行计划

## Overview / 概述

Load plan, review critically, execute tasks in batches, report for review between batches.
加载计划，审慎审查，分批执行任务，批次间汇报供审查。

**Core principle:** Batch execution with checkpoints for architect review.
**核心原则：** 分批执行，带检查点供架构师审查。

**Announce at start:** "I'm using the executing-plans skill to implement this plan."
**开始时宣布：** "我正使用 executing-plans 技能实现此计划。"

## The Process / 流程

### Step 1: Load and Review Plan / 步骤 1：加载并审查计划
1. Read plan file
   读取计划文件
2. Review critically - identify any questions or concerns about the plan
   审慎审查 — 识别对计划的疑问或顾虑
3. If concerns: Raise them with your human partner before starting
   若有顾虑：开始前向人类伙伴提出
4. If no concerns: Create TodoWrite and proceed
   若无顾虑：创建 TodoWrite 并继续

### Step 2: Execute Batch / 步骤 2：执行批次
**Default: First 3 tasks**
**默认：前 3 个任务**

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Report / 步骤 3：汇报
When batch complete:
批次完成时：
- Show what was implemented
  展示已实现内容
- Show verification output
  展示验证输出
- Say: "Ready for feedback."
  说明：「等待反馈。」

### Step 4: Continue / 步骤 4：继续
Based on feedback:
根据反馈：
- Apply changes if needed
- Execute next batch
- Repeat until complete

### Step 5: Complete Development / 步骤 5：完成开发

After all tasks complete and verified:
所有任务完成并验证后：
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
  宣布：「我正使用 finishing-a-development-branch 技能完成此工作。」
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
  **必须子技能：** 使用 superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice
  按该技能验证测试、呈现选项、执行选择

## When to Stop and Ask for Help / 何时停止并求助

**STOP executing immediately when:**
**立即停止执行当：**
- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
  批次中遇到阻塞（依赖缺失、测试失败、指令不明）
- Plan has critical gaps preventing starting
  计划存在阻碍启动的关键缺口
- You don't understand an instruction
  不理解某条指令
- Verification fails repeatedly
  验证反复失败

**Ask for clarification rather than guessing.**
**请求澄清，不要猜测。**

## When to Revisit Earlier Steps / 何时回到早期步骤

**Return to Review (Step 1) when:**
**回到审查（步骤 1）当：**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember / 记住
- Review plan critically first
  先审慎审查计划
- Follow plan steps exactly
  严格按计划步骤执行
- Don't skip verifications
  不要跳过验证
- Reference skills when plan says to
  计划要求时引用技能
- Between batches: just report and wait
  批次间：只汇报并等待
- Stop when blocked, don't guess
  遇到阻塞时停止，不要猜测
- Never start implementation on main/master branch without explicit user consent
  未经用户明确同意，切勿在 main/master 分支上开始实现

## Integration / 集成

**Required workflow skills:**
**必需工作流技能：**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
  **superpowers:using-git-worktrees** — 必须：开始前设置隔离工作区
- **superpowers:writing-plans** - Creates the plan this skill executes
  **superpowers:writing-plans** — 创建本技能执行的计划
- **superpowers:finishing-a-development-branch** - Complete development after all tasks
  **superpowers:finishing-a-development-branch** — 所有任务后完成开发
