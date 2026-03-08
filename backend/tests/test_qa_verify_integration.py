"""
QaService 与 Verify 模块集成测试

测试 QaService 的 ask 和 stream_ask 方法与 V2.0 质量保障模块的集成。

Author: C2
Date: 2026-03-03
"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.qa_service import QaService
from app.verify.verify_pipeline import VerifyPipeline, VerificationAction


@pytest.mark.integration
class TestQaServiceVerifyIntegration:
    """QaService 与 Verify 模块集成测试"""

    def test_ask_with_verification_disabled(self):
        """测试验证禁用时的行为"""
        with patch('app.config.settings.verification_enabled', False):
            # 模拟基础组件
            with patch('app.services.qa_service.QaService._retriever') as mock_retriever:
                mock_retriever.retrieve.return_value = [
                    {"id": 1, "content": "Test content", "distance": 0.3}
                ], None
                
                with patch('app.services.qa_service.get_provider_for_task') as mock_provider:
                    mock_provider.return_value = MagicMock(
                        generate=MagicMock(return_value="Test answer [ID:0].")
                    )
                    with patch('app.services.qa_service.QaService._embedding_service') as mock_embed:
                        mock_embed.embed.return_value = [[0.1, 0.2]]
                        
                        result, error = QaService.ask(
                            knowledge_base_id=1,
                            question="Test question"
                        )
                        
                        assert error is None
                        assert result is not None
                        assert result["answer"] == "Test answer [ID:0]."
                        # 验证禁用时，verification 应该是 None
                        assert result.get("verification") is None

    def test_ask_with_verification_enabled_pass(self):
        """测试验证启用且通过时的行为"""
        mock_verify_pipeline = MagicMock()
        mock_verify_pipeline.verify.return_value = MagicMock(
            action=VerificationAction.PASS,
            confidence_score=MagicMock(score=0.85),
            citation_result=MagicMock(citation_accuracy=0.9),
            reason="通过: 置信度=0.85"
        )
        
        with patch('app.services.qa_service.QaService._get_verify_pipeline', return_value=mock_verify_pipeline):
            with patch('app.services.qa_service.QaService._retriever') as mock_retriever:
                mock_retriever.retrieve.return_value = [
                    {"id": 1, "content": "Test content", "distance": 0.3, "chunk_id": 1}
                ], None
                
                with patch('app.services.qa_service.get_provider_for_task') as mock_provider:
                    mock_provider.return_value = MagicMock(
                        generate=MagicMock(return_value="Test answer [ID:0].")
                    )
                    with patch('app.services.qa_service.QaService._embedding_service') as mock_embed:
                        mock_embed.embed.return_value = [[0.1, 0.2]]
                        
                        result, error = QaService.ask(
                            knowledge_base_id=1,
                            question="Test question",
                            user_id=1
                        )
                        
                        assert error is None
                        assert result is not None
                        assert "verification" in result
                        assert result["verification"]["action"] == "pass"
                        assert result["verification"]["confidence_score"] == 0.85
                        assert result["verification"]["citation_accuracy"] == 0.9

    def test_ask_with_verification_enabled_refuse(self):
        """测试验证启用且拒答时的行为"""
        mock_verify_pipeline = MagicMock()
        mock_verify_pipeline.verify.return_value = MagicMock(
            action=VerificationAction.REFUSE,
            confidence_score=MagicMock(score=0.25),
            citation_result=MagicMock(citation_accuracy=0.5),
            reason="低置信度: 0.25"
        )
        
        with patch('app.services.qa_service.QaService._get_verify_pipeline', return_value=mock_verify_pipeline):
            with patch('app.services.qa_service.QaService._retriever') as mock_retriever:
                mock_retriever.retrieve.return_value = [
                    {"id": 1, "content": "Test content", "distance": 0.3, "chunk_id": 1}
                ], None
                
                with patch('app.services.qa_service.get_provider_for_task') as mock_provider:
                    mock_provider.return_value = MagicMock(
                        generate=MagicMock(return_value="Test answer [ID:0].")
                    )
                    with patch('app.services.qa_service.QaService._embedding_service') as mock_embed:
                        mock_embed.embed.return_value = [[0.1, 0.2]]
                        
                        result, error = QaService.ask(
                            knowledge_base_id=1,
                            question="Test question",
                            user_id=1
                        )
                        
                        assert error is None
                        assert result is not None
                        assert "verification" in result
                        assert result["verification"]["action"] == "refuse"
                        assert result["verification"]["confidence_score"] == 0.25

    def test_ask_with_verification_error(self):
        """测试验证流程出错时的降级行为"""
        mock_verify_pipeline = MagicMock()
        mock_verify_pipeline.verify.side_effect = Exception("NLI model error")
        
        with patch('app.services.qa_service.QaService._get_verify_pipeline', return_value=mock_verify_pipeline):
            with patch('app.services.qa_service.QaService._retriever') as mock_retriever:
                mock_retriever.retrieve.return_value = [
                    {"id": 1, "content": "Test content", "distance": 0.3, "chunk_id": 1}
                ], None
                
                with patch('app.services.qa_service.get_provider_for_task') as mock_provider:
                    mock_provider.return_value = MagicMock(
                        generate=MagicMock(return_value="Test answer [ID:0].")
                    )
                    with patch('app.services.qa_service.QaService._embedding_service') as mock_embed:
                        mock_embed.embed.return_value = [[0.1, 0.2]]
                        
                        # 验证失败不应该阻止答案返回
                        result, error = QaService.ask(
                            knowledge_base_id=1,
                            question="Test question",
                            user_id=1
                        )
                        
                        assert error is None
                        assert result is not None
                        # 验证失败时，verification 应该是 None
                        assert result.get("verification") is None

    def test_verify_pipeline_initialization(self):
        """测试 VerifyPipeline 延迟初始化"""
        # 禁用验证时，应该返回 None
        with patch('app.config.settings.verification_enabled', False):
            pipeline = QaService._get_verify_pipeline()
            assert pipeline is None
        
        # 启用验证时，应该初始化成功（使用 mock）
        with patch('app.config.settings.verification_enabled', True):
            with patch('app.verify.verify_pipeline.NLIHallucinationDetector') as mock_nli:
                mock_nli.return_value = MagicMock()
                # 清除缓存的 pipeline
                QaService._verify_pipeline = None
                pipeline = QaService._get_verify_pipeline()
                assert pipeline is not None

    @pytest.mark.skip(reason="需要真实的日志数据库连接")
    def test_verification_metrics_logged(self):
        """测试验证指标被正确记录到日志"""
        # 这个测试需要真实的数据库连接
        # 可以在集成测试环境中运行
        pass


@pytest.mark.integration
class TestQaServiceVerificationMetrics:
    """测试 QaService 返回的验证指标"""

    def test_verification_response_structure(self):
        """测试验证响应的数据结构"""
        mock_verify_pipeline = MagicMock()
        mock_verify_pipeline.verify.return_value = MagicMock(
            action=VerificationAction.PASS,
            confidence_score=MagicMock(score=0.8),
            citation_result=MagicMock(citation_accuracy=0.9),
            reason="通过"
        )
        
        with patch('app.services.qa_service.QaService._get_verify_pipeline', return_value=mock_verify_pipeline):
            with patch('app.services.qa_service.QaService._retriever') as mock_retriever:
                mock_retriever.retrieve.return_value = [
                    {"id": 1, "content": "Test", "distance": 0.3, "chunk_id": 1}
                ], None
                
                with patch('app.services.qa_service.get_provider_for_task') as mock_provider:
                    mock_provider.return_value = MagicMock(
                        generate=MagicMock(return_value="Answer")
                    )
                    with patch('app.services.qa_service.QaService._embedding_service') as mock_embed:
                        mock_embed.embed.return_value = [[0.1, 0.2]]
                        
                        result, _ = QaService.ask(
                            knowledge_base_id=1,
                            question="Test",
                            user_id=1
                        )
                        
                        # 验证响应结构
                        assert "answer" in result
                        assert "citations" in result
                        assert "verification" in result
                        
                        # 验证 verification 字段结构
                        verification = result["verification"]
                        assert "action" in verification
                        assert "confidence_score" in verification
                        assert "citation_accuracy" in verification

    def test_verification_nil_on_empty_retrieval(self):
        """测试无检索结果时验证为空"""
        with patch('app.services.qa_service.QaService._retriever') as mock_retriever:
            # 模拟无检索结果
            mock_retriever.retrieve.return_value = [], None
            
            with patch('app.services.qa_service.QaService._filter_by_similarity') as mock_filter:
                mock_filter.return_value = []
                
                result, _ = QaService.ask(
                    knowledge_base_id=1,
                    question="Test"
                )
                
                # 无检索结果时，应该返回无答案文本
                assert result["answer"] is not None
                assert result["retrieved_count"] == 0
                # 验证应该为 None（因为没有答案需要验证）
                assert result.get("verification") is None
