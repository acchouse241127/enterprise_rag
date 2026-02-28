# V2.0 模型分配规则 / Model Assignment Rules

> 开发过程中按任务类型选择模型，平衡质量与成本。

---

## 模型分配表

| 阶段 | 推荐模型 | 可选 Agent |
|------|----------|------------|
| 规划（brainstorming / writing-plans） | glm-4.7 | @planner, @architect |
| 执行（implementer） | glm-4.7 | - |
| 规格审查 | glm-4.7 | - |
| 代码质量审查 | glm-4.7 | @code-reviewer |
| 检查点写入 | composer1.5 | - |
| 阶段总结 | glm-4.7 | - |
| 构建 / 类型错误 | glm-4.7 | @build-error-resolver |
| 数据库 / 迁移 | glm-4.7 | @database-reviewer |

---

## 使用说明

- **glm-4.7**：Chat 模式下从模型下拉菜单选择
- **composer1.5**：Agent/Composer 模式下使用，适合检查点等轻量生成
- **@agent**：在输入时 @ 提及对应 Agent，自动使用其配置的模型
