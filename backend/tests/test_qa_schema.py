"""Schema tests for QA request payload."""

from app.schemas.qa import QaAskRequest


def test_qa_request_accepts_query_expansion_fields() -> None:
    req = QaAskRequest.model_validate(
        {
            "knowledge_base_id": 1,
            "question": "测试问题",
            "query_expansion_mode": "hybrid",
            "query_expansion_target": "cloud",
            "query_expansion_llm": {
                "provider": "openai",
                "model_name": "kimi-k2.5",
                "base_url": "https://example.com/v1",
                "api_key": "sk-test",
                "temperature": 0.5,
                "timeout_seconds": 30,
                "max_retries": 2,
                "retry_base_delay": 0.2,
            },
        }
    )
    assert req.query_expansion_mode == "hybrid"
    assert req.query_expansion_target == "cloud"
    assert req.query_expansion_llm is not None
    assert req.query_expansion_llm.model_name == "kimi-k2.5"
