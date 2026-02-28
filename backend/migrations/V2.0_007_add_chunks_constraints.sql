-- V2.0_007: Add chunks content length constraint and business constraints
-- Author: C2
-- Date: 2026-02-28

-- 1. Add chunks content length constraint
DO `$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_chunks_content_length'
    ) THEN
        ALTER TABLE chunks
        ADD CONSTRAINT check_chunks_content_length
        CHECK (char_length(content) <= 100000);
    END IF;
END`$;

-- 2. Add knowledge_bases business constraints
DO `$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_chunk_mode'
    ) THEN
        ALTER TABLE knowledge_bases
        ADD CONSTRAINT check_chunk_mode
        CHECK (chunk_mode IN ('char', 'sentence', 'token', 'chinese_recursive'));
    END IF;
END`$;

DO `$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_parent_retrieval_mode'
    ) THEN
        ALTER TABLE knowledge_bases
        ADD CONSTRAINT check_parent_retrieval_mode
        CHECK (parent_retrieval_mode IN ('physical', 'dynamic', 'off'));
    END IF;
END`$;

-- 3. Add retrieval_logs score constraints
DO `$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_confidence_score_range'
    ) THEN
        ALTER TABLE retrieval_logs
        ADD CONSTRAINT check_confidence_score_range
        CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1));
    END IF;
END`$;

DO `$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_faithfulness_score_range'
    ) THEN
        ALTER TABLE retrieval_logs
        ADD CONSTRAINT check_faithfulness_score_range
        CHECK (faithfulness_score IS NULL OR (faithfulness_score >= 0 AND faithfulness_score <= 1));
    END IF;
END`$;

DO `$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_citation_accuracy_range'
    ) THEN
        ALTER TABLE retrieval_logs
        ADD CONSTRAINT check_citation_accuracy_range
        CHECK (citation_accuracy IS NULL OR (citation_accuracy >= 0 AND citation_accuracy <= 1));
    END IF;
END`$;
