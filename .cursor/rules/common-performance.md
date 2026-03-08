---
description: "Performance optimization: model selection strategy, context window management, extended thinking"
description_zh: "性能优化：模型选择策略、上下文窗口管理、延伸思考"
alwaysApply: true
---

# Performance Optimization / 性能优化

## Model Selection Strategy / 模型选择策略

**Haiku 4.5** (90% of Sonnet capability, 3x cost savings):
**Haiku 4.5**（Sonnet 能力约 90%，成本约省 3 倍）：
- Lightweight agents with frequent invocation
  频繁调用的轻量代理
- Pair programming and code generation
  结对编程与代码生成
- Worker agents in multi-agent systems
  多代理系统中的工作代理

**Sonnet 4.5** (Best coding model):
**Sonnet 4.5**（最佳编码模型）：
- Main development work
  主要开发工作
- Orchestrating multi-agent workflows
  编排多代理工作流
- Complex coding tasks
  复杂编码任务

**Opus 4.5** (Deepest reasoning):
**Opus 4.5**（最深推理）：
- Complex architectural decisions
  复杂架构决策
- Maximum reasoning requirements
  最大推理需求
- Research and analysis tasks
  研究与分析任务

## Context Window Management / 上下文窗口管理

Avoid last 20% of context window for:
避免将以下任务放在上下文窗口最后 20%：
- Large-scale refactoring
  大规模重构
- Feature implementation spanning multiple files
  跨多文件的功能实现
- Debugging complex interactions
  调试复杂交互

Lower context sensitivity tasks:
对上下文敏感度较低的任务：
- Single-file edits
  单文件编辑
- Independent utility creation
  独立工具创建
- Documentation updates
  文档更新
- Simple bug fixes
  简单 bug 修复

## Extended Thinking + Plan Mode / 延伸思考 + 计划模式

Extended thinking is enabled by default, reserving up to 31,999 tokens for internal reasoning.
延伸思考默认开启，为内部推理保留最多 31,999 token。

Control extended thinking via:
通过以下方式控制延伸思考：
- **Toggle**: Option+T (macOS) / Alt+T (Windows/Linux)
  **开关**：Option+T (macOS) / Alt+T (Windows/Linux)
- **Config**: Set `alwaysThinkingEnabled` in `~/.claude/settings.json`
  **配置**：在 `~/.claude/settings.json` 中设置 `alwaysThinkingEnabled`
- **Budget cap**: `export MAX_THINKING_TOKENS=10000`
  **预算上限**：`export MAX_THINKING_TOKENS=10000`
- **Verbose mode**: Ctrl+O to see thinking output
  **详细模式**：Ctrl+O 查看思考输出

For complex tasks requiring deep reasoning:
对需要深度推理的复杂任务：
1. Ensure extended thinking is enabled (on by default)
   确保开启延伸思考（默认开启）
2. Enable **Plan Mode** for structured approach
   开启**计划模式**以结构化推进
3. Use multiple critique rounds for thorough analysis
   多轮 critique 做全面分析
4. Use split role sub-agents for diverse perspectives
   使用分工子代理获得多视角

## Build Troubleshooting / 构建故障排除

If build fails:
若构建失败：
1. Use **build-error-resolver** agent
   使用 **build-error-resolver** 代理
2. Analyze error messages
   分析错误信息
3. Fix incrementally
   增量修复
4. Verify after each fix
   每次修复后验证
