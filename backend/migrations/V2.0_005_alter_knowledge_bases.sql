-- V2.0_005: knowledge_bases 表新增分块与父文档检索配置
ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS chunk_mode VARCHAR(30) DEFAULT 'chinese_recursive';
ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS parent_retrieval_mode VARCHAR(20) DEFAULT 'dynamic';
ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS dynamic_expand_n INTEGER DEFAULT 2;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_chunk_mode') THEN
        ALTER TABLE knowledge_bases ADD CONSTRAINT check_chunk_mode
            CHECK (chunk_mode IN ('char', 'sentence', 'token', 'chinese_recursive'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_parent_retrieval_mode') THEN
        ALTER TABLE knowledge_bases ADD CONSTRAINT check_parent_retrieval_mode
            CHECK (parent_retrieval_mode IN ('physical', 'dynamic', 'off'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_dynamic_expand_n') THEN
        ALTER TABLE knowledge_bases ADD CONSTRAINT check_dynamic_expand_n
            CHECK (dynamic_expand_n >= 1 AND dynamic_expand_n <= 5);
    END IF;
END$$;
