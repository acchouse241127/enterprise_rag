-- V2.0 Optimization: Add composite indexes for common query patterns
-- Author: AI Assistant
-- Date: 2026-03-03

-- Documents: Knowledge base + status queries
CREATE INDEX IF NOT EXISTS idx_documents_kb_status 
ON documents(knowledge_base_id, status);

-- Documents: Knowledge base + created_at sorting
CREATE INDEX IF NOT EXISTS idx_documents_kb_created 
ON documents(knowledge_base_id, created_at DESC);

-- Documents: Knowledge base + file hash (for deduplication)
CREATE INDEX IF NOT EXISTS idx_documents_kb_hash 
ON documents(knowledge_base_id, file_hash);

-- Documents: User + created_at queries
CREATE INDEX IF NOT EXISTS idx_documents_user_created 
ON documents(created_by, created_at DESC);

-- Documents: Status + updated_at queries
CREATE INDEX IF NOT EXISTS idx_documents_status_updated 
ON documents(status, updated_at DESC);

-- Knowledge Bases: Name + created_at sorting
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_name_created 
ON knowledge_bases(name, created_at DESC);

-- User Knowledge Base Permissions: User + KB lookups
CREATE INDEX IF NOT EXISTS idx_user_kb_permissions_user_kb 
ON user_kb_permissions(user_id, knowledge_base_id);

-- Conversations: Knowledge base + created_at queries
CREATE INDEX IF NOT EXISTS idx_conversations_kb_created 
ON conversations(knowledge_base_id, created_at DESC);

-- Conversations: User + created_at queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_created 
ON conversations(created_by, created_at DESC);

-- Conversation Messages: Conversation + created_at queries
CREATE INDEX IF NOT EXISTS idx_conv_messages_conv_created 
ON conversation_messages(conversation_id, created_at DESC);

-- Retrieval Logs: Knowledge base + created_at queries
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_kb_created 
ON retrieval_logs(knowledge_base_id, created_at DESC);

-- Retrieval Feedback: Log + feedback_type queries
CREATE INDEX IF NOT EXISTS idx_retrieval_feedback_log_type 
ON retrieval_feedback(retrieval_log_id, feedback_type);

-- Async Tasks: Status + created_at queries
CREATE INDEX IF NOT EXISTS idx_async_tasks_status_created 
ON async_tasks(status, created_at DESC);

-- Folder Sync Logs: KB + status + created_at queries
CREATE INDEX IF NOT EXISTS idx_folder_sync_logs_kb_status 
ON folder_sync_logs(folder_sync_id, status, created_at DESC);

-- Analysis comment: These indexes optimize common query patterns
-- and prevent N+1 query issues by allowing efficient JOIN operations.
