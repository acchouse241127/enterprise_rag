"""Retrieval service for Phase 1.3."""

from app.config import settings
from app.rag import BgeM3EmbeddingService, ChromaVectorStore, VectorRetriever


class RetrievalService:
    """Domain service to retrieve relevant chunks from knowledge base."""

    _embedding_service = BgeM3EmbeddingService(
        model_name=settings.embedding_model_name,
        fallback_dim=settings.embedding_fallback_dim,
    )
    _vector_store = ChromaVectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_prefix=settings.chroma_collection_prefix,
    )
    _retriever = VectorRetriever(
        embedding_service=_embedding_service,
        vector_store=_vector_store,
    )

    @staticmethod
    def retrieve(
        knowledge_base_id: int,
        query: str,
        top_k: int | None = None,
    ) -> tuple[list[dict], str | None]:
        final_top_k = top_k if top_k is not None else settings.retrieval_top_k
        return RetrievalService._retriever.retrieve(
            knowledge_base_id=knowledge_base_id,
            query=query,
            top_k=final_top_k,
        )
