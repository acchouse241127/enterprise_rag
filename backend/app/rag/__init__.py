"""RAG pipeline package."""

from .chunker import TextChunker
from .dedup import deduplicate_chunks, hamming_distance, simhash
from .embedding import BgeM3EmbeddingService
from .modality_aware_retrieval import ModalityAwareRetrieval
from .pipeline import RagPipeline
from .query_analyzer import QueryAnalyzer
from .reranker import BgeRerankerService
from .retriever import VectorRetriever
from .vector_store import ChromaVectorStore

__all__ = [
    "TextChunker",
    "BgeM3EmbeddingService",
    "ChromaVectorStore",
    "VectorRetriever",
    "RagPipeline",
    "BgeRerankerService",
    "deduplicate_chunks",
    "simhash",
    "hamming_distance",
    # V2.1 新增模块
    "QueryAnalyzer",
    "ModalityAwareRetrieval",
]

