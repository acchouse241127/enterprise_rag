#!/usr/bin/env python
"""Auto-annotate evaluation QA set by running retrieval and suggesting chunk IDs.

This script:
1. Loads the eval QA set
2. Runs retrieval for each question
3. Updates expected_chunk_ids with retrieved results (for manual review)
4. Saves the annotated set back

Usage:
    python scripts/auto_annotate_eval_set.py [--kb-id 1] [--top-k 5] [--output tests/fixtures/eval_qa_set_annotated.yaml]

The output should be manually reviewed before use.
"""

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def load_qa_set(qa_set_path: Path) -> list[dict[str, Any]]:
    """Load evaluation QA set from YAML file."""
    with open(qa_set_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def save_qa_set(qa_set_path: Path, qa_items: list[dict[str, Any]]) -> None:
    """Save evaluation QA set to YAML file."""
    with open(qa_set_path, "w", encoding="utf-8") as f:
        yaml.dump(qa_items, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def get_chunks_for_kb(kb_id: int) -> list[dict]:
    """Get all chunks for a knowledge base from database."""
    from sqlalchemy import text
    from app.core.database import SessionLocal

    sql = text("""
        SELECT id, document_id, chunk_index, content, section_title
        FROM chunks
        WHERE knowledge_base_id = :kb_id
        ORDER BY document_id, chunk_index
    """)

    with SessionLocal() as db:
        result = db.execute(sql, {"kb_id": kb_id})
        return [
            {
                "id": str(row[0]),
                "document_id": row[1],
                "chunk_index": row[2],
                "content": row[3],
                "section_title": row[4],
            }
            for row in result.all()
        ]


def find_relevant_chunks(question: str, chunks: list[dict], top_k: int = 5) -> list[str]:
    """Find relevant chunks using simple keyword matching (no embedding needed)."""
    # Simple TF-IDF like scoring
    from collections import Counter
    import re

    # Tokenize question
    q_words = set(re.findall(r"\w+", question.lower()))
    if not q_words:
        return []

    # Score each chunk
    scored = []
    for chunk in chunks:
        content = (chunk.get("content") or "").lower()
        # Count word occurrences
        content_words = re.findall(r"\w+", content)
        word_counts = Counter(content_words)

        # Calculate simple score: sum of question word frequencies
        score = sum(word_counts.get(w, 0) for w in q_words)

        # Bonus for section title match
        title = (chunk.get("section_title") or "").lower()
        if any(w in title for w in q_words):
            score += 5

        scored.append((score, chunk["id"]))

    # Sort by score and return top_k
    scored.sort(key=lambda x: -x[0])
    return [chunk_id for score, chunk_id in scored[:top_k] if score > 0]


def annotate_with_retrieval(qa_items: list[dict[str, Any]], kb_id: int, top_k: int = 5) -> list[dict[str, Any]]:
    """Annotate QA items with suggested chunk IDs using retrieval."""
    from app.rag.bm25_retriever import BM25Retriever
    from app.rag.retriever import VectorRetriever
    from app.rag.embedding import BgeM3EmbeddingService
    from app.rag.vector_store import ChromaVectorStore
    from app.config import settings

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

    annotated = []
    for item in qa_items:
        question = item.get("question", "")
        item_kb_id = item.get("knowledge_base_id", kb_id)

        # Try vector retrieval first
        vector_chunks, _ = vector_retriever.retrieve(item_kb_id, question, top_k=top_k)
        suggested_ids = [c.get("id") or c.get("chunk_id", "") for c in vector_chunks]

        # Update item
        new_item = {**item}
        new_item["expected_chunk_ids"] = suggested_ids
        new_item["annotation_status"] = "auto"  # Mark as auto-annotated
        new_item["annotation_note"] = "Requires manual review"
        annotated.append(new_item)

        print(f"  [{item.get('id')}] {question[:50]}... -> {len(suggested_ids)} chunks")

    return annotated


def main():
    parser = argparse.ArgumentParser(description="Auto-annotate evaluation QA set")
    parser.add_argument(
        "--qa-set",
        type=str,
        default="tests/fixtures/eval_qa_set.yaml",
        help="Path to input QA set (default: tests/fixtures/eval_qa_set.yaml)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="tests/fixtures/eval_qa_set_annotated.yaml",
        help="Path to output annotated QA set",
    )
    parser.add_argument(
        "--kb-id",
        type=int,
        default=1,
        help="Knowledge base ID to query (default: 1)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to suggest per question (default: 5)",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["retrieval", "keyword"],
        default="retrieval",
        help="Annotation method: retrieval (use actual retriever) or keyword (simple matching)",
    )

    args = parser.parse_args()

    qa_set_path = Path(args.qa_set)
    if not qa_set_path.exists():
        print(f"[ERROR] QA set not found: {qa_set_path}")
        return 1

    print(f"[INFO] Loading QA set from: {qa_set_path}")
    qa_items = load_qa_set(qa_set_path)
    print(f"[INFO] Loaded {len(qa_items)} questions")

    print(f"[INFO] Annotating using {args.method} method...")
    if args.method == "retrieval":
        annotated = annotate_with_retrieval(qa_items, args.kb_id, args.top_k)
    else:
        # Simple keyword matching
        chunks = get_chunks_for_kb(args.kb_id)
        print(f"[INFO] Found {len(chunks)} chunks in KB {args.kb_id}")

        annotated = []
        for item in qa_items:
            question = item.get("question", "")
            suggested_ids = find_relevant_chunks(question, chunks, args.top_k)

            new_item = {**item}
            new_item["expected_chunk_ids"] = suggested_ids
            new_item["annotation_status"] = "auto_keyword"
            annotated.append(new_item)
            print(f"  [{item.get('id')}] {question[:50]}... -> {len(suggested_ids)} chunks")

    # Save annotated set
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_qa_set(output_path, annotated)
    print(f"\n[SUCCESS] Annotated QA set saved to: {output_path}")
    print("[WARNING] Please review and correct the suggested chunk IDs before using for evaluation!")

    return 0


if __name__ == "__main__":
    import sys

    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    sys.exit(main())
