"""Retrieval evaluation framework for RAG system.

This script evaluates retrieval quality using metrics like Recall@K and MRR.
"""
import argparse
import json
from pathlib import Path
from typing import Any

from app.rag.bm25_retriever import BM25Retriever
from app.rag.retriever import VectorRetriever
from app.rag.embedding import BgeM3EmbeddingService
from app.rag.vector_store import ChromaVectorStore
from app.rag.rrf_fusion import RRFFusion
from app.config import settings


def calculate_recall_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> float:
    """Calculate Recall@K.

    Args:
        retrieved_ids: List of retrieved chunk/document IDs
        expected_ids: List of expected (relevant) IDs
        k: Number of top results to consider

    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not expected_ids:
        return 1.0

    top_k = retrieved_ids[:k]
    relevant_retrieved = len(set(top_k) & set(expected_ids))

    return relevant_retrieved / len(expected_ids)


def calculate_mrr(retrieved_ids: list[str], expected_ids: list[str]) -> float:
    """Calculate Mean Reciprocal Rank.

    Args:
        retrieved_ids: List of retrieved chunk/document IDs
        expected_ids: List of expected (relevant) IDs

    Returns:
        MRR score (0.0 to 1.0)
    """
    if not expected_ids:
        return 1.0

    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in expected_ids:
            return 1.0 / i

    return 0.0


def load_qa_set(qa_set_path: Path) -> list[dict[str, Any]]:
    """Load evaluation QA set from YAML/JSON file.

    Args:
        qa_set_path: Path to evaluation dataset file

    Returns:
        List of QA items with question and expected results
    """
    with open(qa_set_path, 'r', encoding='utf-8') as f:
        if qa_set_path.suffix in ['.yaml', '.yml']:
            import yaml
            return yaml.safe_load(f)
        else:
            return json.load(f)


def evaluate_retrieval(
    qa_items: list[dict[str, Any]],
    retriever_type: str = "vector",
    top_k: int = 10,
) -> dict[str, Any]:
    """Evaluate retrieval quality on QA set.

    Args:
        qa_items: List of QA items with 'question' and 'expected_chunk_ids'
        retriever_type: Type of retriever ('vector', 'bm25', or 'hybrid')
        top_k: Number of results to retrieve

    Returns:
        Evaluation results with per-item and aggregated metrics
    """
    # Initialize retrievers
    embedding_service = BgeM3EmbeddingService(
        model_name=settings.embedding_model_name,
        fallback_dim=settings.embedding_fallback_dim,
    )
    vector_store = ChromaVectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_prefix=settings.chroma_collection_prefix,
    )

    vector_retriever = VectorRetriever(embedding_service, vector_store)
    bm25_retriever = BM25Retriever()

    results = []

    for item in qa_items:
        question = item.get('question', '')
        expected_ids = item.get('expected_chunk_ids', [])
        knowledge_base_id = item.get('knowledge_base_id', 1)

        # Perform retrieval
        retrieved = []
        if retriever_type == "vector":
            chunks, _ = vector_retriever.retrieve(knowledge_base_id, question, top_k=top_k)
            retrieved = [c.get('id', c.get('chunk_id', '')) for c in chunks]
        elif retriever_type == "bm25":
            bm25_results, _ = bm25_retriever.search(question, knowledge_base_id, top_k=top_k)
            retrieved = [r.id for r in bm25_results]
        elif retriever_type == "hybrid":
            # Combine vector and BM25 results using RRF fusion
            vector_chunks, _ = vector_retriever.retrieve(knowledge_base_id, question, top_k=top_k * 2)
            bm25_results, _ = bm25_retriever.search(question, knowledge_base_id, top_k=top_k * 2)

            # 使用 RRF 融合（与主路径保持一致）
            rrf_fusion = RRFFusion(k=60)
            vector_dicts = [
                {
                    "id": c.get('id', c.get('chunk_id', '')),
                    "document_id": c.get('document_id'),
                    "knowledge_base_id": c.get('knowledge_base_id'),
                    "chunk_index": c.get('chunk_index'),
                    "content": c.get('content', ''),
                    "score": c.get('distance', 0),
                }
                for c in vector_chunks
            ]
            bm25_dicts = [
                {
                    "id": r.id,
                    "document_id": r.document_id,
                    "knowledge_base_id": r.knowledge_base_id,
                    "chunk_index": r.chunk_index,
                    "content": r.content,
                    "score": r.bm25_score,
                }
                for r in bm25_results
            ]

            rrf_results = rrf_fusion.fuse([bm25_dicts, vector_dicts], ["bm25", "vector"], top_k=top_k)
            retrieved = [r.id for r in rrf_results]
        else:
            raise ValueError(f"Unknown retriever type: {retriever_type}")

        # Calculate metrics
        recall_5 = calculate_recall_at_k(retrieved, expected_ids, 5)
        recall_10 = calculate_recall_at_k(retrieved, expected_ids, 10)
        mrr = calculate_mrr(retrieved, expected_ids)

        results.append({
            'question': question,
            'expected_count': len(expected_ids),
            'retrieved_count': len(retrieved),
            'recall_at_5': recall_5,
            'recall_at_10': recall_10,
            'mrr': mrr,
            'retrieved_ids': retrieved[:10],  # Top 10
            'expected_ids': expected_ids,
        })

    # Aggregate metrics
    avg_recall_5 = sum(r['recall_at_5'] for r in results) / len(results)
    avg_recall_10 = sum(r['recall_at_10'] for r in results) / len(results)
    avg_mrr = sum(r['mrr'] for r in results) / len(results)

    return {
        'retriever_type': retriever_type,
        'total_questions': len(results),
        'metrics': {
            'avg_recall_at_5': avg_recall_5,
            'avg_recall_at_10': avg_recall_10,
            'avg_mrr': avg_mrr,
        },
        'per_question_results': results,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Evaluate retrieval quality')
    parser.add_argument(
        '--qa-set',
        type=str,
        default='tests/fixtures/eval_qa_set.yaml',
        help='Path to evaluation QA set (default: tests/fixtures/eval_qa_set.yaml)'
    )
    parser.add_argument(
        '--retriever',
        type=str,
        choices=['vector', 'bm25', 'hybrid'],
        default='vector',
        help='Retriever type to evaluate (default: vector)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=10,
        help='Number of results to retrieve (default: 10)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='evaluation_results.json',
        help='Output file path (default: evaluation_results.json)'
    )

    args = parser.parse_args()

    # Load QA set
    qa_set_path = Path(args.qa_set)
    if not qa_set_path.exists():
        print(f"[ERROR] QA set not found: {qa_set_path}")
        return 1

    print(f"[INFO] Loading QA set from: {qa_set_path}")
    qa_items = load_qa_set(qa_set_path)
    print(f"[INFO] Loaded {len(qa_items)} questions")

    # Evaluate
    print(f"[INFO] Evaluating {args.retriever} retriever...")
    results = evaluate_retrieval(
        qa_items=qa_items,
        retriever_type=args.retriever,
        top_k=args.top_k,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Retriever Type: {results['retriever_type']}")
    print(f"Total Questions: {results['total_questions']}")
    print("\nMetrics:")
    print(f"  Average Recall@5:  {results['metrics']['avg_recall_at_5']:.4f}")
    print(f"  Average Recall@10: {results['metrics']['avg_recall_at_10']:.4f}")
    print(f"  Average MRR:        {results['metrics']['avg_mrr']:.4f}")
    print("=" * 60 + "\n")

    # Save detailed results
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Detailed results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
