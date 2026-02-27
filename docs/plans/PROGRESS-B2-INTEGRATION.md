# B2 集成工作进度

## ✅ 已完成

### B2-7: 反馈服务 + API ✅

**API 端点:**
- `POST /retrieval/feedback` - 添加用户反馈

**功能验证:**
- ✅ 反馈提交接口可用
- ✅ 支持 thumbs_up / thumbs_down
- ✅ 支持可选文字原因

**待完成:**
- 检索日志表扩展（V2.0_006）
- QA 服务集成验证Pipeline

## ⏳ 待验证

### B2-8: QA 服务集成验证
- 集成 verify_pipeline 到 qa_service.py
- 添加 verification、refused SSE 事件

### B2-9: retrieval_logs 迁移
- 扩展 retrieval_logs 表字段
- 添加验证结果存储

## 📊 B2 总体进度

| 任务 | 状态 | 备注 |
|------|------|------|
| B2-1 | ✅ | nli_detector.py (81 行) |
| B2-2 | ✅ | confidence_scorer.py (67 行) |
| B2-3 | ✅ | citation_verifier.py (109 行) |
| B2-4 | ✅ | verify_pipeline.py (131 行) |
| B2-5 | ✅ | refusal.py (67 行) |
| B2-6 | ✅ | V2.0_004_alter_retrieval_feedbacks.sql |
| B2-7 | ✅ | API 已存在 |
| B2-8 | ⏳ | 待集成 |
| B2-9 | ⏳ | 待创建迁移脚本 |

**总计: 7/9 任务完成（78%）**