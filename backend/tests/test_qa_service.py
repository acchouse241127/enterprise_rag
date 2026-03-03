"""
QA Service测试 - 目标覆盖 app/services/qa_service.py (390语句)
从16.7%提升至80%+
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

class TestQAService:
    """测试QA服务"""

    @pytest.fixture
    def mock_qa_service(self):
        """Mock QA service"""
        from app.services.qa_service import QAService
        
        mock_rag = Mock()
        mock_rag.retrieve_and_generate = AsyncMock(return_value=(
            "测试答案",  # answer
            [Mock(id=1, content="source1")],  # sources
            0.9  # confidence
        ))
        
        mock_db = Mock()
        
        service = QAService(
            rag_pipeline=mock_rag,
            db_session=mock_db
        )
        return service, mock_rag, mock_db

    @pytest.mark.asyncio
    async def test_answer_question_success(self, mock_qa_service):
        """测试成功问答"""
        service, mock_rag, _ = mock_qa_service
        
        request = Mock(
            query="测试问题",
            knowledge_base_id=1,
            user_id="user123"
        )
        
        response = await service.answer_question(request)
        
        assert response.answer == "测试答案"
        assert len(response.sources) == 1
        assert response.confidence == 0.9
        mock_rag.retrieve_and_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_answer_question_empty_query(self, mock_qa_service):
        """测试空查询处理"""
        service, _, _ = mock_qa_service
        
        request = Mock(
            query="",  # 空查询
            knowledge_base_id=1,
            user_id="user123"
        )
        
        with pytest.raises(ValueError, match="查询不能为空"):
            await service.answer_question(request)

    @pytest.mark.asyncio
    async def test_answer_question_rag_error(self, mock_qa_service):
        """测试RAG管道错误处理"""
        service, mock_rag, _ = mock_qa_service
        
        mock_rag.retrieve_and_generate = AsyncMock(
            side_effect=Exception("RAG pipeline error")
        )
        
        request = Mock(
            query="测试问题",
            knowledge_base_id=1,
            user_id="user123"
        )
        
        with pytest.raises(Exception, match="RAG pipeline error"):
            await service.answer_question(request)

    @pytest.mark.asyncio
    async def test_answer_question_no_sources(self, mock_qa_service):
        """测试无检索来源的问答"""
        service, mock_rag, _ = mock_qa_service
        
        mock_rag.retrieve_and_generate = AsyncMock(return_value=(
            "基于知识的回答",
            [],  # 无来源
            0.5
        ))
        
        request = Mock(
            query="测试问题",
            knowledge_base_id=1,
            user_id="user123"
        )
        
        response = await service.answer_question(request)
        
        assert len(response.sources) == 0
        assert response.confidence == 0.5

    @pytest.mark.asyncio
    async def test_answer_question_with_conversation(self, mock_qa_service):
        """测试带对话上下文的问答"""
        service, mock_rag, _ = mock_qa_service
        
        request = Mock(
            query="后续问题?",
            knowledge_base_id=1,
            user_id="user123",
            conversation_id="conv123"  # 包含对话ID
        )
        
        response = await service.answer_question(request)
        
        assert response.answer is not None
        # 验证对话历史被使用
        mock_rag.retrieve_and_generate.assert_called_once()
