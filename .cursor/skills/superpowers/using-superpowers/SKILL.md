---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions
description_zh: 在开始任何对话时使用 — 确立如何查找和使用技能，要求在任何回复（含澄清问题）之前调用 Skill 工具
---

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.
若你认为有哪怕 1% 的可能某技能适用于你正在做的事，你必须调用该技能。

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.
若技能适用于你的任务，你没有选择。必须使用。

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
这不可协商。这不是可选项。你不能用理由绕过。
</EXTREMELY-IMPORTANT>

## How to Access Skills / 如何访问技能

**In Claude Code:** Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you—follow it directly. Never use the Read tool on skill files.
**在 Claude Code 中：** 使用 `Skill` 工具。调用技能时其内容会加载并呈现给你 — 直接遵循。切勿用 Read 工具读取技能文件。

**In other environments:** Check your platform's documentation for how skills are loaded.
**在其他环境中：** 查阅平台文档了解如何加载技能。

# Using Skills / 使用技能

## The Rule / 规则

**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means that you should invoke the skill to check. If an invoked skill turns out to be wrong for the situation, you don't need to use it.
**在任何回复或行动之前调用相关或被请求的技能。** 即便只有 1% 可能适用，也应调用技能检查。若调用的技能不适合该情境，则不必使用。

```dot
digraph skill_flow {
    "User message received" [shape=doublecircle];
    "About to EnterPlanMode?" [shape=doublecircle];
    "Already brainstormed?" [shape=diamond];
    "Invoke brainstorming skill" [shape=box];
    "Might any skill apply?" [shape=diamond];
    "Invoke Skill tool" [shape=box];
    "Announce: 'Using [skill] to [purpose]'" [shape=box];
    "Has checklist?" [shape=diamond];
    "Create TodoWrite todo per item" [shape=box];
    "Follow skill exactly" [shape=box];
    "Respond (including clarifications)" [shape=doublecircle];

    "About to EnterPlanMode?" -> "Already brainstormed?";
    "Already brainstormed?" -> "Invoke brainstorming skill" [label="no"];
    "Already brainstormed?" -> "Might any skill apply?" [label="yes"];
    "Invoke brainstorming skill" -> "Might any skill apply?";

    "User message received" -> "Might any skill apply?";
    "Might any skill apply?" -> "Invoke Skill tool" [label="yes, even 1%"];
    "Might any skill apply?" -> "Respond (including clarifications)" [label="definitely not"];
    "Invoke Skill tool" -> "Announce: 'Using [skill] to [purpose]'";
    "Announce: 'Using [skill] to [purpose]'" -> "Has checklist?";
    "Has checklist?" -> "Create TodoWrite todo per item" [label="yes"];
    "Has checklist?" -> "Follow skill exactly" [label="no"];
    "Create TodoWrite todo per item" -> "Follow skill exactly";
}
```

## Red Flags / 警示信号

These thoughts mean STOP—you're rationalizing:
出现这些想法意味着停下 — 你在合理化：

| Thought 想法 | Reality 实际情况 |
|---------|---------|
| "This is just a simple question" 这只是简单问题 | Questions are tasks. Check for skills. 问题即任务，检查技能。 |
| "I need more context first" 我需要先了解上下文 | Skill check comes BEFORE clarifying questions. 技能检查先于澄清问题。 |
| "Let me explore the codebase first" 让我先探索代码库 | Skills tell you HOW to explore. Check first. 技能告诉你如何探索，先检查。 |
| "I can check git/files quickly" 我快速查下 git/文件 | Files lack conversation context. Check for skills. 文件缺对话上下文，检查技能。 |
| "Let me gather information first" 让我先收集信息 | Skills tell you HOW to gather information. 技能告诉你如何收集信息。 |
| "This doesn't need a formal skill" 这不需要正式技能 | If a skill exists, use it. 若存在技能，就用。 |
| "I remember this skill" 我记得这个技能 | Skills evolve. Read current version. 技能会演进，读当前版本。 |
| "This doesn't count as a task" 这不算任务 | Action = task. Check for skills. 行动即任务，检查技能。 |
| "The skill is overkill" 技能杀鸡用牛刀 | Simple things become complex. Use it. 简单会变复杂，用吧。 |
| "I'll just do this one thing first" 我就先做这一件事 | Check BEFORE doing anything. 做事前先检查。 |
| "This feels productive" 这感觉很有成效 | Undisciplined action wastes time. Skills prevent this. 无纪律行动浪费时间，技能可避免。 |
| "I know what that means" 我知道那意思 | Knowing the concept ≠ using the skill. Invoke it. 知道概念≠使用技能，要调用。 |

## Skill Priority / 技能优先级

When multiple skills could apply, use this order:
当多个技能可能适用时，按此顺序：

1. **Process skills first** (brainstorming, debugging) - these determine HOW to approach the task
   **先流程类技能**（brainstorming、debugging）— 决定如何着手任务
2. **Implementation skills second** (frontend-design, mcp-builder) - these guide execution
   **再实现类技能**（frontend-design、mcp-builder）— 指导执行

"Let's build X" → brainstorming first, then implementation skills.
「让我们构建 X」→ 先 brainstorming，再实现技能。
"Fix this bug" → debugging first, then domain-specific skills.
「修复这个 bug」→ 先 debugging，再领域特定技能。

## Skill Types / 技能类型

**Rigid** (TDD, debugging): Follow exactly. Don't adapt away discipline.
**刚性**（TDD、debugging）：严格遵循。不要削弱纪律。

**Flexible** (patterns): Adapt principles to context.
**灵活**（patterns）：根据情境适配原则。

The skill itself tells you which.
技能本身会说明属于哪种。

## User Instructions / 用户指令

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip workflows.
指令说的是做什么，不是怎么做。「添加 X」或「修复 Y」不意味着跳过工作流。
