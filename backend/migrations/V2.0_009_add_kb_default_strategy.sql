-- V2.0_009: knowledge_bases 表新增默认检索策略字段
ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS default_retrieval_strategy VARCHAR(32) DEFAULT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_default_retrieval_strategy') THEN
        ALTER TABLE knowledge_bases ADD CONSTRAINT check_default_retrieval_strategy
            CHECK (default_retrieval_strategy IS NULL OR default_retrieval_strategy IN ('smart', 'precise', 'fast', 'deep'));
    END IF;
END$$;
