---
description: "Hook system guidelines and TodoWrite best practices"
description_zh: "钩子系统指南与 TodoWrite 最佳实践"
alwaysApply: true
---

# Hooks System / 钩子系统

## Hook Types / 钩子类型

- **PreToolUse**: Before tool execution (validation, parameter modification)
  **PreToolUse**：工具执行前（验证、参数修改）
- **PostToolUse**: After tool execution (auto-format, checks)
  **PostToolUse**：工具执行后（自动格式化、检查）
- **Stop**: When session ends (final verification)
  **Stop**：会话结束时（最终验证）

## Auto-Accept Permissions / 自动接受权限

Use with caution:
谨慎使用：
- Enable for trusted, well-defined plans
  对可信、定义清晰的计划启用
- Disable for exploratory work
  探索性工作中禁用
- Never use dangerously-skip-permissions flag
  切勿使用 dangerously-skip-permissions 标志
- Configure `allowedTools` in `~/.claude.json` instead
  改为在 `~/.claude.json` 中配置 `allowedTools`

## TodoWrite Best Practices / TodoWrite 最佳实践

Use TodoWrite tool to:
使用 TodoWrite 工具来：
- Track progress on multi-step tasks
  跟踪多步骤任务进度
- Verify understanding of instructions
  验证对指令的理解
- Enable real-time steering
  支持实时导向
- Show granular implementation steps
  展示细粒度实现步骤

Todo list reveals:
待办列表可暴露：
- Out of order steps
  步骤顺序错误
- Missing items
  遗漏项
- Extra unnecessary items
  多余不必要项
- Wrong granularity
  粒度不当
- Misinterpreted requirements
  误解的需求
