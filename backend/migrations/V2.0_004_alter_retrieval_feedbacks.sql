-- 调整 retrieval_feedbacks 表以支持反馈评分和原因

-- 新增字段
ALTER TABLE retrieval_feedbacks
ADD COLUMN IF NOT EXISTS rating INTEGER CHECK (rating IN (1, -1)),
ADD COLUMN IF NOT EXISTS reason TEXT;

-- 数据回填：从 feedback_type 映射到 rating
UPDATE retrieval_feedbacks SET rating = 1 WHERE feedback_type = 'thumbs_up';
UPDATE retrieval_feedbacks SET rating = -1 WHERE feedback_type = 'thumbs_down';

-- 可选：在迁移后删除旧字段（谨慎操作）
-- ALTER TABLE retrieval_feedbacks DROP COLUMN IF EXISTS feedback_type;
