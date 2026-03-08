---
description: "Python hooks: black/ruff auto-format, mypy/pyright type checking, print() warnings"
description_zh: "Python 钩子：black/ruff 自动格式化、mypy/pyright 类型检查、print() 警告"
globs: ["**/*.py"]
alwaysApply: false
---

# Python Hooks / Python 钩子

> This file extends [common/hooks.md](../common/hooks.md) with Python specific content.
> 本文件在 [common/hooks.md](../common/hooks.md) 基础上扩展 Python 特定内容。

## PostToolUse Hooks / PostToolUse 钩子

Configure in `~/.claude/settings.json`:
在 `~/.claude/settings.json` 中配置：

- **black/ruff**: Auto-format `.py` files after edit
  **black/ruff**：编辑后自动格式化 `.py` 文件
- **mypy/pyright**: Run type checking after editing `.py` files
  **mypy/pyright**：编辑 `.py` 文件后运行类型检查

## Warnings / 警告

- Warn about `print()` statements in edited files (use `logging` module instead)
- 对编辑文件中的 `print()` 发出警告（改用 `logging` 模块）
