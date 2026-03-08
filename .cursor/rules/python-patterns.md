---
description: "Python patterns: Protocol for duck typing, dataclass DTOs, context managers, generators"
description_zh: "Python 模式：鸭子类型 Protocol、dataclass DTO、上下文管理器、生成器"
globs: ["**/*.py"]
alwaysApply: false
---

# Python Patterns / Python 模式

> This file extends [common/patterns.md](../common/patterns.md) with Python specific content.
> 本文件在 [common/patterns.md](../common/patterns.md) 基础上扩展 Python 特定内容。

## Protocol (Duck Typing) / Protocol（鸭子类型）

```python
from typing import Protocol

class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...
```

## Dataclasses as DTOs / Dataclass 作为 DTO

```python
from dataclasses import dataclass

@dataclass
class CreateUserRequest:
    name: str
    email: str
    age: int | None = None
```

## Context Managers & Generators / 上下文管理器与生成器

- Use context managers (`with` statement) for resource management
  用上下文管理器（`with`）管理资源
- Use generators for lazy evaluation and memory-efficient iteration
  用生成器做惰性求值和内存高效迭代

## Reference / 参考

See skill: `python-patterns` for comprehensive patterns including decorators, concurrency, and package organization.
参见 skill：`python-patterns` 获取包含装饰器、并发、包组织的完整模式。
