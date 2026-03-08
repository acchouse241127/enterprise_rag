# T0 模拟真人测试

基于 Playwright 的浏览器自动化，模拟真人使用 RAG 系统：鼠标点击、键盘键入、滚动。

## 安装

```bash
cd enterprise_rag/tests/e2e/human_simulator
pip install -r requirements.txt
playwright install chromium
```

## 运行前

1. 启动后端：`cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`
2. 启动前端：`cd frontend_spa && npm run dev`
3. 确保 Postgres、ChromaDB 已启动，并执行 `init_db.py` 创建测试账号

## 运行

```bash
# 有界面模式（可观察操作过程）
python human_simulator.py

# 无头模式
python human_simulator.py --headless

# 指定 URL 和报告路径
python human_simulator.py --url http://localhost:3000 --output ./report.json
```

## 输出

- 控制台打印错误与反馈摘要
- 报告文件：`human_simulator_report_YYYYMMDD_HHMMSS.json`

## 覆盖流程

1. 登录（admin / password123）
2. 知识库管理（创建知识库）
3. 文档上传（上传测试 txt）
4. RAG 问答（输入问题、等待回答、滚动查看）
