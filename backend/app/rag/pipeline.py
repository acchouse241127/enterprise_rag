"""RAG pipeline with citation tracing."""

from __future__ import annotations

import math
import re
from typing import Any

from app.llm import ChatMessage
from app.rag.embedding import BgeM3EmbeddingService
from app.rag.prompts import get_system_prompt
from app.rag.retriever import VectorRetriever


class RagPipeline:
    """Retrieve context, generate answer, and inject citations."""

    def __init__(
        self,
        retriever: VectorRetriever,
        embedding_service: BgeM3EmbeddingService,
        no_answer_text: str = "未检索到足够知识，无法给出可靠答案。当前知识库可能无有效文档，或文档解析/向量化未完成，请检查文档上传页面的解析状态。",
    ) -> None:
        self.retriever = retriever
        self.embedding_service = embedding_service
        self.no_answer_text = no_answer_text

    def _build_context(self, chunks: list[dict]) -> str:
        lines: list[str] = []
        for idx, chunk in enumerate(chunks):
            md = chunk.get("metadata") or {}
            lines.append(
                "\n".join(
                    [
                        f"ID: {idx}",
                        f"document_id: {md.get('document_id', '')}",
                        f"chunk_index: {md.get('chunk_index', '')}",
                        "content:",
                        str(chunk.get("content", "")),
                    ]
                )
            )
        return "\n\n".join(lines)

    def _split_sentences(self, text: str) -> list[str]:
        # Keep punctuation with sentence so citation can be inserted before it.
        parts = re.split(r"(?<=[。！？!?\.])\s*", text.strip())
        return [p for p in parts if p]

    def _cosine(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def insert_citations(
        self,
        answer: str,
        chunks: list[dict],
        similarity_threshold: float = 0.58,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Insert inline [ID:x] citations based on sentence-chunk similarity."""
        if not answer.strip() or not chunks:
            return answer, []

        chunk_texts = [str(c.get("content", "")) for c in chunks]
        chunk_vectors = self.embedding_service.embed(chunk_texts)
        sentences = self._split_sentences(answer)
        sentence_vectors = self.embedding_service.embed(sentences)

        used_ids: set[int] = set()
        cited_sentences: list[str] = []
        for sentence, vec in zip(sentences, sentence_vectors):
            scores = [self._cosine(vec, ck_vec) for ck_vec in chunk_vectors]
            if not scores:
                cited_sentences.append(sentence)
                continue
            best_id = max(range(len(scores)), key=lambda i: scores[i])
            best_score = scores[best_id]
            if best_score < similarity_threshold:
                cited_sentences.append(sentence)
                continue
            used_ids.add(best_id)
            if re.search(r"[。！？!?\.]$", sentence):
                cited = re.sub(r"([。！？!?\.])$", f" [ID:{best_id}]\\1", sentence)
            else:
                cited = sentence + f" [ID:{best_id}]"
            cited_sentences.append(cited)

        citations: list[dict[str, Any]] = []
        for idx in sorted(used_ids):
            chunk = chunks[idx]
            md = chunk.get("metadata") or {}
            citations.append(
                {
                    "id": idx,
                    "chunk_id": chunk.get("chunk_id"),
                    "document_id": md.get("document_id"),
                    "chunk_index": md.get("chunk_index"),
                    "content_preview": str(chunk.get("content", ""))[:200],
                }
            )
        return " ".join(cited_sentences).strip(), citations

    def build_prompt_messages(
        self,
        question: str,
        chunks: list[dict],
        history_messages: list[ChatMessage] | None = None,
        system_prompt_version: str | None = None,
    ) -> list[ChatMessage]:
        context = self._build_context(chunks)
        system = get_system_prompt(system_prompt_version)
        user = (
            f"【用户问题】\n{question}\n\n"
            f"【检索到的上下文】\n{context}\n\n"
            "请根据上述上下文回答用户问题。若上下文不足，请明确说明。"
        )
        messages = [ChatMessage(role="system", content=system)]
        if history_messages:
            messages.extend(history_messages)
        messages.append(ChatMessage(role="user", content=user))
        return messages
