-- V2.0_002: 创建 chunks 表（BM25 全文检索 + 父文档关系）
-- document_id/knowledge_base_id 使用 INTEGER 匹配现有 schema

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    knowledge_base_id INTEGER NOT NULL REFERENCES knowledge_bases(id),
    collection_name VARCHAR(200) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_tsv tsvector,
    chunk_mode VARCHAR(30),
    token_count INTEGER,
    section_title VARCHAR(500),
    parent_chunk_id UUID REFERENCES chunks(id),
    is_parent BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON chunks USING GIN(content_tsv) WHERE content_tsv IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_chunks_kb_id ON chunks(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_chunks_kb_created ON chunks(knowledge_base_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chunks_collection_kb ON chunks(collection_name, knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_parent_idx ON chunks(parent_chunk_id, chunk_index) WHERE parent_chunk_id IS NOT NULL;
