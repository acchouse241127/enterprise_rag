---
description: Activate Superpowers workflow assistant. Auto-enable Superpowers process and guide user through commands, skills, and subagents.
description_zh: 启用 Superpowers 工作流助手。自动进入 Superpowers 流程，并引导使用命令、技能与子代理。
disable-model-invocation: true
---

Invoke the superpowers:using-superpowers skill and follow it exactly as presented to you.

Then do the following:

1. Tell the user Superpowers is active for this session.
2. Give a compact capability map:
   - Commands: /brainstorm, /write-plan, /execute-plan
   - Core skills: brainstorming, writing-plans, executing-plans, test-driven-development, systematic-debugging, verification-before-completion, requesting-code-review, receiving-code-review, finishing-a-development-branch, dispatching-parallel-agents, subagent-driven-development, using-git-worktrees
   - Subagent: code-reviewer
3. Explain the default workflow:
   - Creative/new feature work: brainstorming first
   - Multi-step tasks: writing-plans before implementation
   - Implementation in batches: executing-plans
   - Completion claims: verification-before-completion first
4. Ask one focused question: "你当前要推进的任务是什么？我将用 Superpowers 流程带你推进。"
5. Continue assisting with Superpowers-first behavior in subsequent turns.

If the user asks in plain text "use Superpowers" (or equivalent), treat it as a request to run this command behavior.
