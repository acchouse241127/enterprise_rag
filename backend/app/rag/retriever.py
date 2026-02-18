"""Vector retriever for RAG."""

from app.rag.embedding import BgeM3EmbeddingService
from app.rag.vector_store import ChromaVectorStore


class VectorRetriever:
    """Retrieve top-k chunks from vector store."""

    def __init__(
        self,
        embedding_service: BgeM3EmbeddingService,
        vector_store: ChromaVectorStore,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        knowledge_base_id: int,
        query: str,
        top_k: int = 5,
    ) -> tuple[list[dict], str | None]:
        """Retrieve relevant chunks for a user query."""
        cleaned = query.strip()
        if not cleaned:
            return [], "query 不能为空"

        query_embedding = self.embedding_service.embed([cleaned])[0]
        rows, err = self.vector_store.query_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )
        if err is not None:
            return [], err
        return rows, None
