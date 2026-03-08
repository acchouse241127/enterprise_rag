---
description: "Common design patterns: skeleton projects, repository pattern, API response format"
description_zh: "通用设计模式：骨架项目、仓库模式、API 响应格式"
alwaysApply: true
---

# Common Patterns / 通用模式

## Skeleton Projects / 骨架项目

When implementing new functionality:
实现新功能时：
1. Search for battle-tested skeleton projects
   搜索久经考验的骨架项目
2. Use parallel agents to evaluate options:
   使用并行代理评估选项：
   - Security assessment
     安全评估
   - Extensibility analysis
     扩展性分析
   - Relevance scoring
     相关性评分
   - Implementation planning
     实现规划
3. Clone best match as foundation
   克隆最佳匹配作为基础
4. Iterate within proven structure
   在验证过的结构中迭代

## Design Patterns / 设计模式

### Repository Pattern / 仓库模式

Encapsulate data access behind a consistent interface:
将数据访问封装在统一接口之后：
- Define standard operations: findAll, findById, create, update, delete
  定义标准操作：findAll、findById、create、update、delete
- Concrete implementations handle storage details (database, API, file, etc.)
  具体实现处理存储细节（数据库、API、文件等）
- Business logic depends on the abstract interface, not the storage mechanism
  业务逻辑依赖抽象接口，而非存储实现
- Enables easy swapping of data sources and simplifies testing with mocks
  便于切换数据源、简化 mock 测试

### API Response Format / API 响应格式

Use a consistent envelope for all API responses:
对所有 API 响应使用一致的封装格式：
- Include a success/status indicator
  包含 success/status 标识
- Include the data payload (nullable on error)
  包含数据负载（错误时可空）
- Include an error message field (nullable on success)
  包含错误信息字段（成功时可空）
- Include metadata for paginated responses (total, page, limit)
  分页响应包含元数据（total、page、limit）
