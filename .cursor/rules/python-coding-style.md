---
description: "Python coding style: PEP 8, type annotations, frozen dataclasses, black/isort/ruff formatting"
description_zh: "Python 编码风格：PEP 8、类型注解、冻结 dataclass、black/isort/ruff 格式化"
globs: ["**/*.py"]
alwaysApply: false
---

# Python Coding Style / Python 编码风格

> This file extends [common/coding-style.md](../common/coding-style.md) with Python specific content.
> 本文件在 [common/coding-style.md](../common/coding-style.md) 基础上扩展 Python 特定内容。

## Standards / 标准

- Follow **PEP 8** conventions / 遵循 **PEP 8** 规范
- Use **type annotations** on all function signatures / 所有函数签名使用**类型注解**

## Immutability / 不可变性

Prefer immutable data structures:
优先使用不可变数据结构：

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    name: str
    email: str

from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float
```

## Formatting / 格式化

- **black** for code formatting
  **black** 做代码格式化
- **isort** for import sorting
  **isort** 做 import 排序
- **ruff** for linting
  **ruff** 做 lint

## Reference / 参考

See skill: `python-patterns` for comprehensive Python idioms and patterns.
参见 skill：`python-patterns` 获取完整 Python 惯用法与模式。
