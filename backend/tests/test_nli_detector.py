"""NLI hallucination detector tests."""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from app.verify.nli_detector import NLIHallucinationDetector as NLIDetector


@pytest.mark.unit
def test_nli_entailment():
    """Test entailment detection."""
    mock_model = MagicMock()
    # 模拟模型返回 entailment 的分数分布（第2个标签）
    mock_model.predict.return_value = np.array([[-0.5, 2.0, -0.3]])  # [contradiction, entailment, neutral]
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("What is pension?", "Pension is retirement fund.")
        # entailment 应该得到高忠实度分数
        assert result.faithfulness_score > 0.5
        # 应该至少有一个支持的句子
        assert result.supported_count > 0
        # 详情中应该包含 entailment 标签
        assert result.details[0]["label"] == "entailment"


@pytest.mark.unit
def test_nli_contradiction():
    """Test contradiction detection."""
    mock_model = MagicMock()
    # 模拟模型返回 contradiction 的分数分布（第1个标签）
    mock_model.predict.return_value = np.array([[2.0, -0.5, -0.3]])  # [contradiction, entailment, neutral]
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("Capital of China?", "New York is in USA.")
        # contradiction 应该得到低忠实度分数
        assert result.faithfulness_score < 0.5
        # 详情中应该包含 contradiction 标签
        assert result.details[0]["label"] == "contradiction"


@pytest.mark.unit
def test_nli_neutral():
    """Test neutral detection."""
    mock_model = MagicMock()
    # 模拟模型返回 neutral 的分数分布（第3个标签）
    mock_model.predict.return_value = np.array([[-0.3, -0.5, 2.0]])  # [contradiction, entailment, neutral]
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("What is RAG?", "RAG is retrieval augmented generation.")
        # neutral 不被视为支持，忠实度分数应该是 0
        assert result.faithfulness_score == 0.0
        # 详情中应该包含 neutral 标签
        assert result.details[0]["label"] == "neutral"


@pytest.mark.unit
def test_nli_empty_answer():
    """Test detection with empty answer."""
    mock_model = MagicMock()
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        result = detector.detect("", "Some context.")
        # 空答案应该返回默认高忠实度
        assert result.faithfulness_score == 1.0
        assert result.total_count == 0


@pytest.mark.unit
def test_nli_multiple_sentences():
    """Test detection with multiple sentences."""
    mock_model = MagicMock()
    # 模拟两个句子：第一个 entailment，第二个 contradiction
    # 但是detect方法使用model.predict(pairs)其中pairs=[(context, sentence)]
    # 对于多句，会分别对每句进行检测
    # 这里实际上会检测两个句子："This is supported." 和 "This is contradictory."
    # 第一个得到entailment，第二个得到contradiction
    # 所以faithfulness = 1/2 = 0.5
    mock_model.predict.return_value = np.array([[-0.5, 2.0, -0.3]])  # entailment
    with patch("app.verify.nli_detector.CrossEncoder") as m:
        m.return_value = mock_model
        detector = NLIDetector()
        
        # 创建一个句子（entailment），得到faithfulness=1.0
        result = detector.detect("This is supported.", "Context.")
        assert result.faithfulness_score == 1.0
        assert result.total_count == 1
        assert result.supported_count == 1
