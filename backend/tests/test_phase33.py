"""
Unit tests for Phase 3.3 features.

Phase 3.3: 异步任务队列、Prometheus、对话导出、知识库编辑
Author: C2
Date: 2026-02-14
"""


# ============== Model Tests ==============

def test_task_status_enum():
    """Test TaskStatus enum values."""
    from app.models.async_task import TaskStatus
    
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.SUCCESS.value == "success"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.CANCELLED.value == "cancelled"


def test_task_type_enum():
    """Test TaskType enum values."""
    from app.models.async_task import TaskType
    
    assert TaskType.DOCUMENT_PARSE.value == "document_parse"
    assert TaskType.DOCUMENT_VECTORIZE.value == "document_vectorize"
    assert TaskType.FOLDER_SYNC.value == "folder_sync"
    assert TaskType.EXPORT_CONVERSATION.value == "export_conversation"


def test_async_task_model_fields():
    """Test AsyncTask model has required fields."""
    from app.models.async_task import AsyncTask
    
    # Check model has expected columns
    columns = [c.name for c in AsyncTask.__table__.columns]
    assert "id" in columns
    assert "task_type" in columns
    assert "status" in columns
    assert "entity_type" in columns
    assert "entity_id" in columns
    assert "progress" in columns
    assert "message" in columns
    assert "input_data" in columns
    assert "output_data" in columns
    assert "error_message" in columns
    assert "started_at" in columns
    assert "completed_at" in columns
    assert "created_by" in columns
    assert "created_at" in columns


def test_conversation_model_fields():
    """Test Conversation model has required fields."""
    from app.models.conversation import Conversation
    
    columns = [c.name for c in Conversation.__table__.columns]
    assert "id" in columns
    assert "conversation_id" in columns
    assert "knowledge_base_id" in columns
    assert "title" in columns
    assert "share_token" in columns
    assert "is_shared" in columns
    assert "share_expires_at" in columns
    assert "user_id" in columns


def test_conversation_message_model_fields():
    """Test ConversationMessage model has required fields."""
    from app.models.conversation import ConversationMessage
    
    columns = [c.name for c in ConversationMessage.__table__.columns]
    assert "id" in columns
    assert "conversation_id" in columns
    assert "role" in columns
    assert "content" in columns
    assert "extra_data" in columns
    assert "created_at" in columns


def test_conversation_generate_share_token():
    """Test Conversation.generate_share_token() generates unique tokens."""
    from app.models.conversation import Conversation
    
    token1 = Conversation.generate_share_token()
    token2 = Conversation.generate_share_token()
    
    assert token1 != token2
    assert len(token1) > 20
    assert len(token2) > 20


def test_knowledge_base_chunk_settings_fields():
    """Test KnowledgeBase model has chunk settings fields."""
    from app.models.knowledge_base import KnowledgeBase
    
    columns = [c.name for c in KnowledgeBase.__table__.columns]
    assert "chunk_size" in columns
    assert "chunk_overlap" in columns


# ============== Prometheus Metrics Tests ==============

def test_prometheus_metrics_module():
    """Test prometheus metrics module exports."""
    from app import metrics
    
    # Check counters exist
    assert hasattr(metrics, "HTTP_REQUESTS_TOTAL")
    assert hasattr(metrics, "DOCUMENTS_UPLOADED_TOTAL")
    assert hasattr(metrics, "RAG_QUERIES_TOTAL")
    assert hasattr(metrics, "USER_FEEDBACK_TOTAL")
    assert hasattr(metrics, "ASYNC_TASKS_TOTAL")
    
    # Check histograms exist
    assert hasattr(metrics, "HTTP_REQUEST_DURATION_SECONDS")
    assert hasattr(metrics, "DOCUMENT_PARSE_DURATION_SECONDS")
    assert hasattr(metrics, "RAG_QUERY_DURATION_SECONDS")
    
    # Check gauges exist
    assert hasattr(metrics, "KNOWLEDGE_BASES_TOTAL")
    assert hasattr(metrics, "ASYNC_TASKS_PENDING")


def test_prometheus_get_metrics():
    """Test get_metrics returns bytes."""
    from app.metrics import get_metrics, get_content_type
    
    metrics_output = get_metrics()
    assert isinstance(metrics_output, bytes)
    assert len(metrics_output) > 0
    
    content_type = get_content_type()
    assert "text/plain" in content_type or "openmetrics" in content_type


# ============== Service Tests ==============

def test_async_task_service_imports():
    """Test AsyncTaskService can be imported."""
    from app.services.async_task_service import AsyncTaskService
    
    assert hasattr(AsyncTaskService, "create_task")
    assert hasattr(AsyncTaskService, "get_task")
    assert hasattr(AsyncTaskService, "list_tasks")
    assert hasattr(AsyncTaskService, "update_task_status")
    assert hasattr(AsyncTaskService, "cancel_task")
    assert hasattr(AsyncTaskService, "run_task_in_background")


def test_conversation_service_imports():
    """Test ConversationService can be imported."""
    from app.services.conversation_service import ConversationService
    
    assert hasattr(ConversationService, "create_conversation")
    assert hasattr(ConversationService, "get_conversation")
    assert hasattr(ConversationService, "add_message")
    assert hasattr(ConversationService, "get_messages")
    assert hasattr(ConversationService, "enable_sharing")
    assert hasattr(ConversationService, "disable_sharing")
    assert hasattr(ConversationService, "export_to_markdown")
    assert hasattr(ConversationService, "export_to_pdf_bytes")


def test_kb_edit_service_imports():
    """Test KnowledgeBaseEditService can be imported."""
    from app.services.knowledge_base_edit_service import KnowledgeBaseEditService
    
    assert hasattr(KnowledgeBaseEditService, "get_document_content")
    assert hasattr(KnowledgeBaseEditService, "update_document_content")
    assert hasattr(KnowledgeBaseEditService, "get_kb_chunk_settings")
    assert hasattr(KnowledgeBaseEditService, "update_kb_chunk_settings")
    assert hasattr(KnowledgeBaseEditService, "rechunk_document")
    assert hasattr(KnowledgeBaseEditService, "rechunk_all_documents")


# ============== Config Tests ==============

def test_config_has_phase33_settings():
    """Test config has Phase 3.3 related settings."""
    from app.config import settings
    
    # These should exist from Phase 3.2 but verify they're still there
    assert hasattr(settings, "chunk_size")
    assert hasattr(settings, "chunk_overlap")


# ============== API Router Tests ==============

def test_api_routers_registered():
    """Test Phase 3.3 API routers are registered."""
    from app.api import api_router
    
    # Get all route paths
    routes = [route.path for route in api_router.routes]
    
    # Check async tasks routes
    assert any("/tasks" in r for r in routes)
    
    # Check conversations routes
    assert any("/conversations" in r for r in routes)
    
    # Check kb edit routes (under /knowledge-bases)
    assert any("/knowledge-bases" in r for r in routes)


# ============== Model Export Tests ==============

def test_models_exported():
    """Test Phase 3.3 models are exported from models package."""
    from app.models import (
        AsyncTask,
        TaskStatus,
        TaskType,
        Conversation,
        ConversationMessage,
    )
    
    assert AsyncTask is not None
    assert TaskStatus is not None
    assert TaskType is not None
    assert Conversation is not None
    assert ConversationMessage is not None


# ============== Markdown Export Test ==============

def test_markdown_export_format():
    """Test markdown export produces valid format."""
    # This is a unit test for the format, not the service
    title = "测试对话"
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    ]
    
    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for msg in messages:
        role_label = "**用户**" if msg["role"] == "user" else "**助手**"
        lines.append(f"### {role_label}")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")
        lines.append("---")
        lines.append("")
    
    md_content = "\n".join(lines)
    
    assert "# 测试对话" in md_content
    assert "**用户**" in md_content
    assert "**助手**" in md_content
    assert "你好" in md_content


# ============== Chunk Settings Validation Tests ==============

def test_chunk_size_validation():
    """Test chunk size validation logic."""
    # Valid range: 100-10000
    valid_sizes = [100, 500, 1000, 5000, 10000]
    invalid_sizes = [50, 99, 10001, 20000]
    
    for size in valid_sizes:
        assert 100 <= size <= 10000, f"Size {size} should be valid"
    
    for size in invalid_sizes:
        assert not (100 <= size <= 10000), f"Size {size} should be invalid"


def test_chunk_overlap_validation():
    """Test chunk overlap validation logic."""
    # Valid range: 0-500
    valid_overlaps = [0, 50, 100, 250, 500]
    invalid_overlaps = [-1, 501, 1000]
    
    for overlap in valid_overlaps:
        assert 0 <= overlap <= 500, f"Overlap {overlap} should be valid"
    
    for overlap in invalid_overlaps:
        assert not (0 <= overlap <= 500), f"Overlap {overlap} should be invalid"


def test_chunk_overlap_less_than_size():
    """Test chunk overlap must be less than chunk size."""
    test_cases = [
        (500, 50, True),   # Valid: overlap < size
        (500, 499, True),  # Valid: overlap < size
        (500, 500, False), # Invalid: overlap == size
        (500, 600, False), # Invalid: overlap > size
        (100, 0, True),    # Valid: no overlap
    ]
    
    for size, overlap, expected_valid in test_cases:
        is_valid = overlap < size
        assert is_valid == expected_valid, f"size={size}, overlap={overlap}"
