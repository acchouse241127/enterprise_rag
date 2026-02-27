-- V2.0_006: retrieval_logs 表扩展 - 支持答案质量保障验证结果存储
--
-- 新增字段：
-- confidence_score: 置信度分数 (0-1)
-- confidence_level: 置信度等级 (high/medium/low/refused)
-- faithfulness_score: 忠实度分数 (0-1)
-- has_hallucination: 是否检测到幻觉
-- retrieval_mode: 检索模式 (vector/bm25/hybrid)
-- refusal_reason: 拒答原因 (empty_retrieval/low_relevance/low_faithfulness)
-- citation_accuracy: 引用准确率 (0-1)
-- latency_breakdown: 各阶段耗时明细 (JSONB)

-- 添加验证结果字段
ALTER TABLE retrieval_logs
    ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(3, 2),
    ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(20),
    ADD COLUMN IF NOT EXISTS faithfulness_score NUMERIC(3, 2),
    ADD COLUMN IF NOT EXISTS has_hallucination BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS retrieval_mode VARCHAR(30) DEFAULT 'hybrid',
    ADD COLUMN IF NOT EXISTS refusal_reason VARCHAR(50),
    ADD COLUMN IF NOT EXISTS citation_accuracy NUMERIC(3, 2),
    ADD COLUMN IF NOT EXISTS latency_breakdown JSONB DEFAULT '{}';

-- 创建索引以支持按照置信度和验证结果过滤
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_confidence ON retrieval_logs(confidence_level);
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_mode ON retrieval_logs(retrieval_mode);
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_hallucination ON retrieval_logs(has_hallucination);

-- 添加字段注释
COMMENT ON COLUMN retrieval_logs.confidence_score IS '答案置信度分数 (0-1)';
COMMENT ON COLUMN retrieval_logs.confidence_level IS '置信度等级 (high/medium/low/refused)';
COMMENT ON COLUMN retrieval_logs.faithfulness_score IS 'NLI 忠实度分数 (0-1)';
COMMENT ON COLUMN retrieval_logs.has_hallucination IS '是否检测到幻觉';
COMMENT ON COLUMN retrieval_logs.retrieval_mode IS '检索模式 (vector/bm25/hybrid)';
COMMENT ON COLUMN retrieval_logs.refusal_reason IS '拒答原因 (empty_retrieval/low_relevance/low_faithfulness)';
COMMENT ON COLUMN retrieval_logs.citation_accuracy IS '引用准确率 (0-1)';
COMMENT ON COLUMN retrieval_logs.latency_breakdown IS '各阶段耗时明细 (JSONB)';