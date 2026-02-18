# 测试说明

## Phase 1.1 认证模块测试

### 前置条件

1. 启动 PostgreSQL：
   ```bash
   docker compose up -d postgres
   ```

2. 创建测试用户：
   ```bash
   python scripts/init_db.py
   ```
   将创建：admin/password123、admin_totp/password123

3. 安装测试依赖：
   ```bash
   cd backend && pip install -r requirements.txt
   ```

### 运行自动化测试

```bash
cd backend
pytest tests/ -v
```

### 测试用例文档

见 `Phase_1.1_认证模块测试用例.md`

---

## Phase 1.2 知识库与文档管理测试

### 前置条件

与 Phase 1.1 相同；另需（可选）：

- ChromaDB：`docker compose up -d chromadb`（未启动时向量存储降级，解析仍可测）
- 测试文档：运行 `python tests/scripts/generate_test_docs.py` 生成 docx/xlsx/pptx/pdf

### 运行自动化测试

```bash
cd backend
pytest tests/ -v
```

### 测试用例文档

- `Phase_1.2_知识库管理测试用例.md`
- `Phase_1.2_文档管理测试用例.md`
- `Phase_1.2_测试报告.md`

---

## Phase 1.3 RAG 问答测试

### 前置条件

与 Phase 1.2 相同；另需（可选）：

- LLM API：配置 `LLM_API_KEY` 后真实问答可用；自动化测试通过 mock 覆盖

### 运行自动化测试

```bash
cd enterprise_rag
python -m pytest backend/tests -v
```

### 测试用例文档

- `Phase_1.3_RAG问答测试用例.md`
- `Phase_1.3_测试报告.md`

---

## Phase 1.4 MVP 安全与性能测试

### 测试范围

- 全量回归（含 Phase 1.1~1.3 所有用例）
- 安全测试：API 认证、Token 校验、输入校验、SQL 注入防护
- 性能测试：健康/登录/KB 列表/问答 API 响应时间

### 前置条件

与 Phase 1.3 相同，需先执行 `init_db.py` 创建测试账号。

### 运行自动化测试

```bash
cd enterprise_rag/backend
python -m pytest tests/ -v
```

### 新增测试文件

- `backend/tests/test_security.py`：安全测试
- `backend/tests/test_performance.py`：性能测试

### 测试报告

- `Phase_1.4_测试报告.md`
