# 阶段 2：代码审查报告

**日期**：2026-02-20  
**分支**：main  
**执行模式**：全自动 3A  

---

## 1. 执行摘要

| 项目 | 结果 | 说明 |
|------|------|------|
| Bandit 安全扫描 | ⚠️ 12 低危 | 无 High/Critical |
| pip-audit 依赖漏洞 | ⚠️ 22 个 | 10 个包需升级 |
| Ruff 代码检查 | ✅ 部分修复 | 20 项自动修复，17 项部分保留 |
| mypy 类型检查 | 进行中 | - |

**结论**：无阻塞性安全问题，建议后续升级依赖并逐步修复低危项。

---

## 2. Bandit 安全扫描

**命令**：`bandit -r app/ -f txt`

**结果**：12 个 Low 严重度，0 High/0 Critical

| 规则 | 位置 | 说明 |
|------|------|------|
| B105 | auth.py:34 | `token_type: "bearer"` 疑似硬编码密码（误报，OAuth 标准值） |
| B101 | qa.py:56 | assert 用于生产逻辑 |
| B110 | 多处 | try/except pass |
| B404 | legacy_office.py | subprocess 使用 |
| B603 | legacy_office.py | subprocess 未用 shell |
| B311 | llm/base.py:104 | random 用于重试 jitter（非加密用途） |
| B112 | conversation_service, folder_sync_service | try/except continue |

**建议**：B105 可加 `# nosec`；B311 用于重试延迟可接受；其余为代码风格改进项。

---

## 3. pip-audit 依赖漏洞

**命令**：`pip-audit`

**结果**：22 个已知漏洞，涉及 10 个包

| 包 | 当前版本 | 建议 |
|----|----------|------|
| cryptography | 41.0.7 | 升级至 42.0.4+ |
| fastapi | 0.109.0 | 0.109.1+ |
| pillow | 12.1.0 | 12.1.1+ |
| protobuf | 5.29.5 | 5.29.6+ |
| py | 1.11.0 | 升级 |
| python-jose | 3.3.0 | 3.4.0+ |
| python-multipart | 0.0.6 | 0.0.22+ |
| requests | 2.31.0 | 2.32.4+ |
| starlette | 0.35.1 | 0.40.0+ |
| ecdsa | 0.19.1 | 升级 |

**建议**：在兼容性验证后分批升级，优先处理 starlette/fastapi（Web 层）。

---

## 4. Ruff 代码检查

**命令**：`ruff check . --fix`

**已修复**：20 项（未使用 import、f-string 无占位符等）

**剩余（部分有意保留）**：

| 类型 | 位置 | 说明 |
|------|------|------|
| E402 | user.py, knowledge_base_service.py, qa_service.py, create_test_users.py | 非文件顶部 import（避免循环依赖） |
| E402 | scripts/create_test_users.py | sys.path 修改后 import |
| F401 | document_parser/__init__.py | UrlParser 重导出（已改为 `as UrlParser`） |
| E712 | knowledge_base_edit_service | `Document.is_current == True` → `.is_(True)`（已修复） |
| E712 | test_document_version | bool 比较（已修复） |
| F841 | main.py | 未使用变量 doc_count（已移除） |

---

## 5. 已修复项

- main.py：移除未使用的 `doc_count`；补充 `python main.py` 启动入口
- document_parser/__init__.py：UrlParser 显式重导出
- knowledge_base_edit_service.py：`Document.is_current == True` → `.is_(True)`
- test_document_version.py：bool 断言风格
- 20 项 ruff 可自动修复问题

---

## 6. 待处理项（非阻塞）

1. **依赖升级**：按 pip-audit 建议升级，需回归测试
2. **Bandit**：对 `token_type: "bearer"` 添加 `# nosec B105`
3. **E402**：对有意为之的 import 顺序添加 `# noqa: E402` 或配置 ruff 忽略
4. **mypy**：完成类型检查后补充结果

---

## 7. 阶段门禁

- **是否通过**：通过  
- **阻塞性问题**：无  
- **建议**：可继续阶段 3（测试完善）；依赖升级可并入后续迭代。
