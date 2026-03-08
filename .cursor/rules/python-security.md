---
description: "Python security: dotenv secret management, bandit static analysis"
description_zh: "Python 安全：dotenv 密钥管理、bandit 静态分析"
globs: ["**/*.py"]
alwaysApply: false
---

# Python Security / Python 安全

> This file extends [common/security.md](../common/security.md) with Python specific content.
> 本文件在 [common/security.md](../common/security.md) 基础上扩展 Python 特定内容。

## Secret Management / 密钥管理

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]  # Raises KeyError if missing
```

## Security Scanning / 安全扫描

- Use **bandit** for static security analysis:
  使用 **bandit** 做静态安全分析：
  ```bash
  bandit -r src/
  ```

## Reference / 参考

See skill: `django-security` for Django-specific security guidelines (if applicable).
参见 skill：`django-security` 获取 Django 安全指南（如适用）。
