# Repository 模式重构方案

## 问题总结

根据 `common-patterns.md` 规则检查，发现以下架构问题：

| 问题 | 位置 | 严重性 | 影响 |
|------|------|--------|------|
| QaService 直接实例化依赖 | `qa_service.py:43-51` | 高 | 难以测试、难以替换组件 |
| 直接调用 SessionLocal | `qa_service.py:275` | 高 | 绕过依赖注入，事务管理混乱 |
| 循环导入 | `knowledge_base_service.py:109` | 中 | 潜在运行时错误 |
| 内存状态管理 | `qa_service.py:52` | 高 | 多实例部署时状态不共享 |
| Service 使用静态方法 | 多个 Service 文件 | 中 | 限制依赖注入和测试 |

## 修复方案

### 1. QaService 依赖注入重构

**目标**：将静态实例化改为构造函数注入

**修改文件**：
- `backend/app/services/qa_service.py` - 重构为实例类
- `backend/app/api/deps.py` - 添加 get_qa_service 依赖
- `backend/app/api/qa.py` - 使用依赖注入

**修改前**：
```python
class QaService:
    _embedding_service = BgeM3EmbeddingService(...)
    _vector_store = ChromaVectorStore(...)
    _retriever = VectorRetriever(...)
    
    @staticmethod
    def ask(...):
        ...
```

**修改后**：
```python
class QaService:
    def __init__(
        self,
        retriever: VectorRetriever,
        embedding_service: BgeM3EmbeddingService,
        vector_store: ChromaVectorStore,
        reranker: BgeRerankerService,
        pipeline: RagPipeline,
        keyword_retriever: KeywordRetriever,
        conversation_store: ConversationStore,
    ):
        self._retriever = retriever
        self._embedding_service = embedding_service
        ...
    
    def ask(self, ...):
        ...
```

### 2. 会话历史状态管理重构

**目标**：将内存字典改为可插拔的存储接口

**新增文件**：`backend/app/services/conversation_store.py`

```python
from abc import ABC, abstractmethod
from typing import Protocol

class ConversationStore(Protocol):
    """会话历史存储接口"""
    
    def get_messages(self, key: str) -> list[ChatMessage]:
        """获取会话历史"""
        ...
    
    def append_message(self, key: str, message: ChatMessage) -> None:
        """追加消息"""
        ...
```

**实现**：
- `InMemoryConversationStore` - 默认实现，用于单实例部署
- `RedisConversationStore` - 可选实现，用于多实例部署

### 3. 循环导入修复

**目标**：使用延迟导入和依赖注入消除循环导入

**修改 `knowledge_base_service.py`**：

```python
# 修改前
from app.services.document_service import DocumentService

# 修改后
def delete(db: Session, kb: KnowledgeBase, vector_store: ChromaVectorStore) -> tuple[bool, str | None]:
    # 使用传入的 vector_store 而不是导入 DocumentService
    ...
```

### 4. 统一 Service 实例方法模式

**目标**：所有 Service 改为实例类，支持依赖注入

**步骤**：
1. 将 `@staticmethod` 改为实例方法
2. 添加构造函数接收依赖
3. 在 `deps.py` 中添加工厂函数
4. 更新 API 层使用依赖注入

## 实施顺序

1. ✅ 创建 `ConversationStore` 接口和实现
2. ⬜ 重构 `QaService` 为实例类
3. ⬜ 更新 `deps.py` 添加工厂函数
4. ⬜ 更新 API 层使用依赖注入
5. ⬜ 修复循环导入问题
6. ⬜ 添加单元测试验证重构

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 破坏现有功能 | 高 | 保持 API 签名不变，渐进式重构 |
| 性能影响 | 低 | 使用单例模式，避免重复创建 |
| 测试覆盖不足 | 中 | 重构前先补充测试 |

## 回滚方案

保留原始静态方法作为备份，通过环境变量切换新旧实现：

```python
USE_LEGACY_QA_SERVICE = os.getenv("USE_LEGACY_QA_SERVICE", "false").lower() == "true"

if USE_LEGACY_QA_SERVICE:
    QaService = LegacyQaService
```
