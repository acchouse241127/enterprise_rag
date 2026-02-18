"""Question answering service."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)
from app.llm import ChatMessage, LlmProviderError, get_provider_for_task
from app.services.conversation_service import ConversationService
from app.rag import BgeM3EmbeddingService, BgeRerankerService, ChromaVectorStore, RagPipeline, VectorRetriever, deduplicate_chunks
from app.rag.query_expansion import expand_query
from app.rag.keyword_retriever import KeywordRetriever


class QaService:
    """Service for ask and stream ask."""

    # Chroma 使用 cosine 时返回的是距离（越小越相似），超过此距离视为无关，直接返回无答案
    # 现在由 settings.dynamic_threshold_fallback 控制，此处保留兼容
    _max_distance_accept: float = settings.dynamic_threshold_fallback

    _embedding_service = BgeM3EmbeddingService(
        model_name=settings.embedding_model_name,
        fallback_dim=settings.embedding_fallback_dim,
    )
    _vector_store = ChromaVectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_prefix=settings.chroma_collection_prefix,
    )
    _retriever = VectorRetriever(_embedding_service, _vector_store)
    _keyword_retriever = KeywordRetriever(_embedding_service, _vector_store)
    _reranker = BgeRerankerService(model_name=settings.reranker_model_name)
    _pipeline = RagPipeline(_retriever, _embedding_service)
    _conversation_history: dict[str, list[ChatMessage]] = {}

    @staticmethod
    def _filter_by_similarity(chunks: list[dict]) -> list[dict]:
        """过滤掉相似度过低的片段（Chroma cosine 距离过大即无关）。"""
        if not chunks:
            return []
        out = []
        for c in chunks:
            d = c.get("distance")
            if d is None:
                out.append(c)
                continue
            if d <= QaService._max_distance_accept:
                out.append(c)
        return out

    @staticmethod
    def _build_history_key(knowledge_base_id: int, conversation_id: str | None) -> str | None:
        if not conversation_id:
            return None
        return f"kb:{knowledge_base_id}:conv:{conversation_id.strip()}"

    @staticmethod
    def _get_history_messages(
        knowledge_base_id: int,
        conversation_id: str | None,
        history_turns: int | None,
    ) -> list[ChatMessage]:
        key = QaService._build_history_key(knowledge_base_id, conversation_id)
        if key is None:
            return []
        all_msgs = QaService._conversation_history.get(key, [])
        if not all_msgs:
            return []
        turns = history_turns if history_turns is not None else settings.qa_history_max_turns
        # 1 turn = user + assistant, each turn is 2 messages.
        keep_count = max(1, turns) * 2
        return all_msgs[-keep_count:]

    @staticmethod
    def _append_history(
        knowledge_base_id: int,
        conversation_id: str | None,
        question: str,
        answer: str,
    ) -> None:
        key = QaService._build_history_key(knowledge_base_id, conversation_id)
        if key is None:
            return
        existing = QaService._conversation_history.get(key, [])
        existing.append(ChatMessage(role="user", content=question))
        existing.append(ChatMessage(role="assistant", content=answer))
        max_keep = max(1, settings.qa_history_max_turns) * 2
        QaService._conversation_history[key] = existing[-max_keep:]

    @staticmethod
    def _apply_dedup(chunks: list[dict]) -> list[dict]:
        """应用 SimHash 去重，移除近似重复的检索片段。"""
        if not chunks:
            return []
        if not settings.dedup_enabled:
            return chunks
        return deduplicate_chunks(
            chunks,
            threshold=settings.dedup_simhash_threshold,
            content_key="content",
        )

    @staticmethod
    def _apply_reranker(question: str, chunks: list[dict], final_top_k: int) -> list[dict]:
        if not chunks:
            return []
        if not settings.reranker_enabled:
            return chunks[:final_top_k]
        reranked = QaService._reranker.rerank(question, chunks, top_n=final_top_k)
        # 动态阈值：过滤 Reranker 分数过低的结果
        if settings.dynamic_threshold_enabled:
            reranked = [
                c for c in reranked
                if c.get("rerank_score", 1.0) >= settings.dynamic_threshold_min
            ]
        return reranked

    @staticmethod
    def _log_retrieval(
        knowledge_base_id: int,
        user_id: int | None,
        query: str,
        chunks_retrieved: int,
        chunks_after_filter: int,
        chunks_after_dedup: int,
        chunks_after_rerank: int,
        final_chunks: list[dict],
        retrieval_time_ms: int | None = None,
        rerank_time_ms: int | None = None,
        total_time_ms: int | None = None,
        llm_time_ms: int | None = None,
        answer_generated: bool = True,
        answer_length: int | None = None,
        error_message: str | None = None,
    ) -> int | None:
        """Log retrieval to database (Phase 3.2). Returns log_id if successful."""
        if not settings.retrieval_log_enabled:
            return None
        try:
            from app.core.database import SessionLocal
            from app.services.retrieval_log_service import RetrievalLogService

            # Calculate score stats
            scores = [c.get("rerank_score") or c.get("distance") for c in final_chunks if c]
            scores = [s for s in scores if s is not None]
            top_score = max(scores) if scores else None
            avg_score = sum(scores) / len(scores) if scores else None
            min_score = min(scores) if scores else None

            # Build chunk details for logging
            chunk_details = [
                {
                    "chunk_id": c.get("id"),
                    "document_id": c.get("document_id"),
                    "content_preview": (c.get("content") or "")[:200],
                    "score": c.get("rerank_score") or c.get("distance"),
                }
                for c in final_chunks[:settings.retrieval_log_max_chunks]
            ]

            db = SessionLocal()
            try:
                log = RetrievalLogService.create_log(
                    db=db,
                    knowledge_base_id=knowledge_base_id,
                    user_id=user_id,
                    query=query,
                    chunks_retrieved=chunks_retrieved,
                    chunks_after_filter=chunks_after_filter,
                    chunks_after_dedup=chunks_after_dedup,
                    chunks_after_rerank=chunks_after_rerank,
                    top_chunk_score=top_score,
                    avg_chunk_score=avg_score,
                    min_chunk_score=min_score,
                    chunk_details=chunk_details,
                    retrieval_time_ms=retrieval_time_ms,
                    rerank_time_ms=rerank_time_ms,
                    total_time_ms=total_time_ms,
                    llm_time_ms=llm_time_ms,
                    answer_generated=answer_generated,
                    answer_length=answer_length,
                    error_message=error_message,
                )
                logger.info("retrieval_log created id=%s kb_id=%s", log.id, knowledge_base_id)
                return log.id
            finally:
                db.close()
        except Exception as e:
            logger.warning("retrieval_log create failed (qa): %s", e, exc_info=True)
            return None

    @staticmethod
    def ask(
        knowledge_base_id: int,
        question: str,
        top_k: int | None = None,
        conversation_id: str | None = None,
        history_turns: int | None = None,
        user_id: int | None = None,  # Phase 3.2: for retrieval logging
        system_prompt_version: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        start_time = time.perf_counter()
        final_top_k = top_k if top_k is not None else settings.retrieval_top_k
        retrieve_top_k = max(final_top_k, settings.reranker_candidate_k) if settings.reranker_enabled else final_top_k

        retrieval_start = time.perf_counter()
        queries = [question]
        if getattr(settings, "retrieval_query_expansion_enabled", False):
            queries = expand_query(question, max_extra=2) or [question]
        seen_ids = set()
        chunks = []
        for q in queries:
            vec_chunks, err = QaService._retriever.retrieve(
                knowledge_base_id=knowledge_base_id,
                query=q,
                top_k=retrieve_top_k,
            )
            if err is not None:
                return None, err
            for c in vec_chunks:
                cid = c.get("chunk_id")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    chunks.append(c)
        if getattr(settings, "retrieval_use_keyword", False):
            kw_chunks, _ = QaService._keyword_retriever.retrieve(
                knowledge_base_id=knowledge_base_id,
                query=question,
                top_k=retrieve_top_k,
            )
            for c in kw_chunks:
                cid = c.get("chunk_id")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    chunks.append(c)
        retrieval_time_ms = int((time.perf_counter() - retrieval_start) * 1000)

        chunks_retrieved = len(chunks)

        # 检索为空或全部低分时直接返回「未找到」，不调用 LLM
        chunks = QaService._filter_by_similarity(chunks)
        chunks_after_filter = len(chunks)

        chunks = QaService._apply_dedup(chunks)  # Phase 2.3: 去重
        chunks_after_dedup = len(chunks)

        rerank_start = time.perf_counter()
        chunks = QaService._apply_reranker(question, chunks, final_top_k=final_top_k)
        rerank_time_ms = int((time.perf_counter() - rerank_start) * 1000)
        chunks_after_rerank = len(chunks)
        logger.info(
            "qa_timing retrieval_ms=%s rerank_ms=%s chunks=%s",
            retrieval_time_ms,
            rerank_time_ms,
            chunks_after_rerank,
        )

        if not chunks:
            total_time_ms = int((time.perf_counter() - start_time) * 1000)
            # Log empty retrieval
            log_id = QaService._log_retrieval(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                query=question,
                chunks_retrieved=chunks_retrieved,
                chunks_after_filter=chunks_after_filter,
                chunks_after_dedup=chunks_after_dedup,
                chunks_after_rerank=chunks_after_rerank,
                final_chunks=[],
                retrieval_time_ms=retrieval_time_ms,
                rerank_time_ms=rerank_time_ms,
                total_time_ms=total_time_ms,
                answer_generated=True,
                answer_length=len(QaService._pipeline.no_answer_text),
            )
            return {
                "answer": QaService._pipeline.no_answer_text,
                "citations": [],
                "retrieved_count": 0,
                "conversation_id": conversation_id,
                "retrieval_log_id": log_id,  # Phase 3.2
            }, None

        provider = get_provider_for_task("qa")
        history_messages = QaService._get_history_messages(knowledge_base_id, conversation_id, history_turns)
        messages = QaService._pipeline.build_prompt_messages(
            question=question,
            chunks=chunks,
            history_messages=history_messages,
            system_prompt_version=system_prompt_version,
        )

        llm_start = time.perf_counter()
        try:
            raw_answer = provider.generate(messages=messages, temperature=settings.llm_temperature)
            llm_time_ms = int((time.perf_counter() - llm_start) * 1000)
            total_time_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                "qa_timing llm_ms=%s total_ms=%s (retrieval=%s rerank=%s)",
                llm_time_ms,
                total_time_ms,
                retrieval_time_ms,
                rerank_time_ms,
            )
        except LlmProviderError as exc:
            llm_time_ms = int((time.perf_counter() - llm_start) * 1000)
            total_time_ms = int((time.perf_counter() - start_time) * 1000)
            # Log failed LLM call
            log_id = QaService._log_retrieval(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                query=question,
                chunks_retrieved=chunks_retrieved,
                chunks_after_filter=chunks_after_filter,
                chunks_after_dedup=chunks_after_dedup,
                chunks_after_rerank=chunks_after_rerank,
                final_chunks=chunks,
                retrieval_time_ms=retrieval_time_ms,
                rerank_time_ms=rerank_time_ms,
                llm_time_ms=llm_time_ms,
                total_time_ms=total_time_ms,
                answer_generated=False,
                error_message=str(exc.detail),
            )
            return {
                "answer": None,
                "citations": [],
                "retrieved_count": len(chunks),
                "llm_failed": True,
                "error_message": str(exc.detail),
                "chunks": chunks,
                "conversation_id": conversation_id,
                "retrieval_log_id": log_id,  # Phase 3.2
            }, None

        llm_time_ms = int((time.perf_counter() - llm_start) * 1000)
        total_time_ms = int((time.perf_counter() - start_time) * 1000)

        answer, citations = QaService._pipeline.insert_citations(raw_answer, chunks)
        QaService._append_history(knowledge_base_id, conversation_id, question, answer)

        # Log successful retrieval
        log_id = QaService._log_retrieval(
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            query=question,
            chunks_retrieved=chunks_retrieved,
            chunks_after_filter=chunks_after_filter,
            chunks_after_dedup=chunks_after_dedup,
            chunks_after_rerank=chunks_after_rerank,
            final_chunks=chunks,
            retrieval_time_ms=retrieval_time_ms,
            rerank_time_ms=rerank_time_ms,
            llm_time_ms=llm_time_ms,
            total_time_ms=total_time_ms,
            answer_generated=True,
            answer_length=len(answer),
        )

        return {
            "answer": answer,
            "citations": citations,
            "retrieved_count": len(chunks),
            "conversation_id": conversation_id,
            "retrieval_log_id": log_id,  # Phase 3.2
        }, None

    @staticmethod
    def stream_ask(
        knowledge_base_id: int,
        question: str,
        top_k: int | None = None,
        conversation_id: str | None = None,
        history_turns: int | None = None,
        user_id: int | None = None,  # Phase 3.2: for retrieval logging
        system_prompt_version: str | None = None,
    ) -> Iterator[str]:
        start_time = time.perf_counter()
        final_top_k = top_k if top_k is not None else settings.retrieval_top_k
        retrieve_top_k = max(final_top_k, settings.reranker_candidate_k) if settings.reranker_enabled else final_top_k

        retrieval_start = time.perf_counter()
        queries = [question]
        if getattr(settings, "retrieval_query_expansion_enabled", False):
            queries = expand_query(question, max_extra=2) or [question]
        seen_ids = set()
        chunks = []
        for q in queries:
            vec_chunks, err = QaService._retriever.retrieve(
                knowledge_base_id=knowledge_base_id,
                query=q,
                top_k=retrieve_top_k,
            )
            if err is not None:
                yield f"data: {json.dumps({'type': 'error', 'message': err}, ensure_ascii=False)}\n\n"
                return
            for c in vec_chunks:
                cid = c.get("chunk_id")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    chunks.append(c)
        if getattr(settings, "retrieval_use_keyword", False):
            kw_chunks, _ = QaService._keyword_retriever.retrieve(
                knowledge_base_id=knowledge_base_id,
                query=question,
                top_k=retrieve_top_k,
            )
            for c in kw_chunks:
                cid = c.get("chunk_id")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    chunks.append(c)
        retrieval_time_ms = int((time.perf_counter() - retrieval_start) * 1000)

        chunks_retrieved = len(chunks)
        chunks = QaService._filter_by_similarity(chunks)
        chunks_after_filter = len(chunks)
        chunks = QaService._apply_dedup(chunks)  # Phase 2.3: 去重
        chunks_after_dedup = len(chunks)

        rerank_start = time.perf_counter()
        chunks = QaService._apply_reranker(question, chunks, final_top_k=final_top_k)
        rerank_time_ms = int((time.perf_counter() - rerank_start) * 1000)
        chunks_after_rerank = len(chunks)
        logger.info(
            "qa_timing stream retrieval_ms=%s rerank_ms=%s chunks=%s",
            retrieval_time_ms,
            rerank_time_ms,
            chunks_after_rerank,
        )

        if not chunks:
            total_time_ms = int((time.perf_counter() - start_time) * 1000)
            log_id = QaService._log_retrieval(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                query=question,
                chunks_retrieved=chunks_retrieved,
                chunks_after_filter=chunks_after_filter,
                chunks_after_dedup=chunks_after_dedup,
                chunks_after_rerank=chunks_after_rerank,
                final_chunks=[],
                retrieval_time_ms=retrieval_time_ms,
                rerank_time_ms=rerank_time_ms,
                total_time_ms=total_time_ms,
                answer_generated=True,
                answer_length=len(QaService._pipeline.no_answer_text),
            )
            yield f"data: {json.dumps({'type': 'answer', 'delta': QaService._pipeline.no_answer_text}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'retrieval_log_id', 'data': log_id}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return

        provider = get_provider_for_task("qa")
        history_messages = QaService._get_history_messages(knowledge_base_id, conversation_id, history_turns)
        messages = QaService._pipeline.build_prompt_messages(
            question=question,
            chunks=chunks,
            history_messages=history_messages,
            system_prompt_version=system_prompt_version,
        )
        answer_parts: list[str] = []
        llm_start = time.perf_counter()
        try:
            for piece in provider.stream(messages=messages, temperature=settings.llm_temperature):
                answer_parts.append(piece)
                yield f"data: {json.dumps({'type': 'answer', 'delta': piece}, ensure_ascii=False)}\n\n"
        except LlmProviderError as exc:
            llm_time_ms = int((time.perf_counter() - llm_start) * 1000)
            total_time_ms = int((time.perf_counter() - start_time) * 1000)
            log_id = QaService._log_retrieval(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                query=question,
                chunks_retrieved=chunks_retrieved,
                chunks_after_filter=chunks_after_filter,
                chunks_after_dedup=chunks_after_dedup,
                chunks_after_rerank=chunks_after_rerank,
                final_chunks=chunks,
                retrieval_time_ms=retrieval_time_ms,
                rerank_time_ms=rerank_time_ms,
                llm_time_ms=llm_time_ms,
                total_time_ms=total_time_ms,
                answer_generated=False,
                error_message=str(exc.detail),
            )
            yield f"data: {json.dumps({'type': 'error', 'message': f'LLM 调用失败: {exc.detail}'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'retrieval_log_id', 'data': log_id}, ensure_ascii=False)}\n\n"
            return

        llm_time_ms = int((time.perf_counter() - llm_start) * 1000)
        total_time_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "qa_timing stream llm_ms=%s total_ms=%s (retrieval=%s rerank=%s)",
            llm_time_ms,
            total_time_ms,
            retrieval_time_ms,
            rerank_time_ms,
        )

        merged = "".join(answer_parts).strip()
        if merged:
            QaService._append_history(knowledge_base_id, conversation_id, question, merged)
        # OPT-024: stream 结束后持久化到对话管理（独立 session）
        if merged and conversation_id and conversation_id.strip():
            try:
                ConversationService.persist_qa_turn_standalone(
                    conversation_id_str=conversation_id.strip(),
                    knowledge_base_id=knowledge_base_id,
                    user_id=user_id,
                    question=question,
                    answer=merged,
                )
            except Exception:
                pass  # 持久化失败不影响流式响应
        _, citations = QaService._pipeline.insert_citations(merged, chunks)

        # Log successful retrieval
        log_id = QaService._log_retrieval(
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            query=question,
            chunks_retrieved=chunks_retrieved,
            chunks_after_filter=chunks_after_filter,
            chunks_after_dedup=chunks_after_dedup,
            chunks_after_rerank=chunks_after_rerank,
            final_chunks=chunks,
            retrieval_time_ms=retrieval_time_ms,
            rerank_time_ms=rerank_time_ms,
            llm_time_ms=llm_time_ms,
            total_time_ms=total_time_ms,
            answer_generated=True,
            answer_length=len(merged),
        )

        yield f"data: {json.dumps({'type': 'citations', 'data': citations}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'retrieval_log_id', 'data': log_id}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
