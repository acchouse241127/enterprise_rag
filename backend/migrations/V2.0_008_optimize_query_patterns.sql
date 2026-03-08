-- V2.0 Optimization: Optimize query patterns to prevent N+1
-- Author: AI Assistant
-- Date: 2026-03-03

-- Enable query logging (optional, for debugging)
-- ALTER SYSTEM SET log_min_duration_statement = 100;

-- Analyze tables after index creation
ANALYZE documents;
ANALYZE knowledge_bases;
ANALYZE users;
ANALYZE conversations;
ANALYZE conversation_messages;
ANALYZE retrieval_logs;
ANALYZE retrieval_feedback;
ANALYZE async_tasks;

-- Set appropriate work_mem for sorts (PostgreSQL-specific)
-- Adjust based on available RAM
-- SET work_mem = '256MB';

-- Create partial indexes for large tables
-- These help with range queries on sorted data
CREATE INDEX IF NOT EXISTS idx_documents_kb_partial_status 
ON documents(knowledge_base_id, status)
WHERE status IN ('parsed', 'vectorized');

CREATE INDEX IF NOT EXISTS idx_conversations_partial_created 
ON conversations(created_at DESC)
WHERE created_at > NOW() - INTERVAL '30 days';

-- Cleanup old data (retention policy)
-- Optional: uncomment if data cleanup is needed
-- DELETE FROM retrieval_logs WHERE created_at < NOW() - INTERVAL '90 days';
-- DELETE FROM retrieval_feedback WHERE created_at < NOW() - INTERVAL '90 days';

-- Create materialized view for dashboard stats (refresh periodically)
-- This improves query performance for dashboard endpoints
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_knowledge_base_stats AS
SELECT 
    kb.id AS knowledge_base_id,
    kb.name,
    kb.created_at,
    COUNT(DISTINCT d.id) AS document_count,
    COUNT(DISTINCT CASE WHEN d.status = 'vectorized' THEN d.id END) AS vectorized_count,
    COUNT(DISTINCT c.id) AS conversation_count,
    MAX(d.created_at) AS last_document_updated_at
FROM knowledge_bases kb
LEFT JOIN documents d ON d.knowledge_base_id = kb.id
LEFT JOIN conversations c ON c.knowledge_base_id = kb.id
GROUP BY kb.id, kb.name, kb.created_at;

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_mv_knowledge_base_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_knowledge_base_stats;
END;
$$ LANGUAGE plpgsql;

-- Comment: Materialized views significantly improve read performance
-- for dashboard and list endpoints by pre-computing aggregations.
