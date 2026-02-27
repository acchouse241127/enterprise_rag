"""
用户反馈服务。

V2.0: 支持评分（rating）和原因（reason）提交。
"""

from sqlalchemy.orm import Session

from app.models.retrieval_log import RetrievalFeedback
from app.services.retrieval_log_service import RetrievalLogService


class FeedbackService:
    """用户反馈业务逻辑服务。"""

    @staticmethod
    def submit_feedback(
        db: Session,
        retrieval_log_id: int,
        user_id: int | None,
        rating: int,
        reason: str | None = None,
        feedback_type: str | None = None,
        comment: str | None = None,
        is_sample_marked: bool = False,
    ) -> tuple[RetrievalFeedback | None, str | None]:
        """
        提交用户反馈。

        Args:
            db: 数据库会话
            retrieval_log_id: 检索日志 ID
            user_id: 用户 ID（可选）
            rating: 评分数值（1 为点赞，-1 为点踩）
            reason: 用户输入的原因（V2.0 新增）
            feedback_type: 反馈类型（兼容字段）
            comment: 用户评论文本（可选）
            is_sample_marked: 是否标记问题样本

        Returns:
            (feedback, error_message)
        """
        # V2.0: 如果 feedback_type 未提供，从 rating 推导
        if feedback_type is None:
            feedback_type = "helpful" if rating == 1 else "not_helpful"

        return RetrievalLogService.add_feedback(
            db=db,
            retrieval_log_id=retrieval_log_id,
            user_id=user_id,
            feedback_type=feedback_type,
            rating=rating,
            reason=reason,
            comment=comment,
            is_sample_marked=is_sample_marked,
        )

    @staticmethod
    def get_feedback_stats(db: Session, retrieval_log_id: int) -> dict:
        """
        获取检索日志的反馈统计。

        Args:
            db: 数据库会话
            retrieval_log_id: 检索日志 ID

        Returns:
            统计数据：{thumbs_up, thumbs_down, total_ratings}
        """
        feedbacks = RetrievalLogService.get_feedbacks_for_log(db, retrieval_log_id)

        thumbs_up = sum(1 for fb in feedbacks if fb.rating == 1)
        thumbs_down = sum(1 for fb in feedbacks if fb.rating == -1)

        return {
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "total_ratings": thumbs_up + thumbs_down,
            "feedbacks_count": len(feedbacks),
        }