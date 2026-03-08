"""Question answering service."""

from __future__ import annotations

import json
import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse
import time
from collections.abc import Iterator
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)
from app.llm import ChatMessage, LlmProviderError, build_chat_provider, get_provider_for_task
from app.services.conversation_service import ConversationService
from app.rag import BgeM3EmbeddingService, BgeRerankerService, ChromaVectorStore, RagPipeline, VectorRetriever, deduplicate_chunks
from app.rag.query_expansion import expand_query, ExpansionMode
from app.rag.keyword_retriever import KeywordRetriever

# V2.0 质量保障模块导入
from app.verify.nli_detector import NLIHallucinationDetector
from app.verify.confidence_scorer import ConfidenceScorer
from app.verify.citation_verifier import CitationVerifier
from app.verify.verify_pipeline import VerifyPipeline, VerificationAction
from app.verify.refusal import RefusalHandler

# V2.0 质量保障配置
_verification_enabled = getattr(settings, "verification_enabled", False)
_confidence_threshold = getattr(settings, "verification_confidence_threshold", 0.5)
_citation_threshold = getattr(settings, "verification_citation_threshold", 0.5)
_refusal_threshold = getattr(settings, "verification_refusal_threshold", 0.3)


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
    _expansion_timeout_max: int = 30
    _expansion_max_retries_max: int = 2
    _expansion_retry_delay_max: float = 5.0

    # V2.0 质量保障 Pipeline（延迟初始化）
    _verify_pipeline: VerifyPipeline | None = None

    @classmethod
    def _get_verify_pipeline(cls) -> VerifyPipeline | None:
        """获取验证 Pipeline（延迟初始化以避免启动时加载模型）。"""
        if not _verification_enabled:
            return None
        if cls._verify_pipeline is None:
            try:
                nli_detector = NLIHallucinationDetector()
                cls._verify_pipeline = VerifyPipeline(
                    nli_detector=nli_detector,
                    confidence_threshold=_confidence_threshold,
                    citation_threshold=_citation_threshold,
                    refusal_threshold=_refusal_threshold,
                )
                logger.info("VerifyPipeline initialized with thresholds: confidence=%.2f, citation=%.2f, refusal=%.2f",
                           _confidence_threshold, _citation_threshold, _refusal_threshold)
            except Exception as e:
                logger.warning("Failed to initialize VerifyPipeline: %s", e)
                return None
        return cls._verify_pipeline

    # V2.1 Phase 4: 增强检索服务（延迟初始化）
    _enhanced_retrieval: EnhancedRetrievalService | None = None

    @classmethod
    def _get_enhanced_retrieval(cls) -> EnhancedRetrievalService | None:
        """获取增强检索服务（延迟初始化）。"""
        if cls._enhanced_retrieval is None:
            try:
                cls._enhanced_retrieval = EnhancedRetrievalService()
                logger.info("EnhancedRetrievalService initialized")
            except Exception as e:
                logger.warning("Failed to initialize EnhancedRetrievalService: %s", e)
                return None
        return cls._enhanced_retrieval

    @staticmethod
    def _retrieve_with_enhanced(
        knowledge_base_id: int,
        question: str,
        top_k: int,
    ) -> tuple[list[dict], dict]:
        """使用增强检索服务进行多模态感知检索。

        Args:
            knowledge_base_id: 知识库ID
            question: 查询问题
            top_k: 返回结果数量

        Returns:
            (检索结果列表, 元数据字典)
        """
        service = QaService._get_enhanced_retrieval()
        if service is None:
            logger.warning("EnhancedRetrievalService not available, using vector retrieval")
            # Fallback to basic retrieval
            chunks, err = QaService._retriever.retrieve(
                knowledge_base_id=knowledge_base_id,
                query=question,
                top_k=top_k,
            )
            if err is not None:
                return [], {"error": str(err)}
            return chunks, {}

        try:
            # 使用增强检索服务进行多模态感知检索
            enhanced_chunks, metadata = service.retrieve_with_modality_aware(
                query=question,
                knowledge_base_id=knowledge_base_id,
                top_k=top_k,
            )

            logger.info(
                "Enhanced retrieval retrieved %d chunks with modality boost (needs_chart=%s, needs_table=%s, needs_image=%s)",
                len(enhanced_chunks),
                metadata.get("needs_chart", False),
                metadata.get("needs_table", False),
                metadata.get("needs_image", False),
            )

            return enhanced_chunks, metadata

        except Exception as e:
            logger.error("Enhanced retrieval failed: %s", e)
            # Fallback to basic retrieval
            chunks, err = QaService._retriever.retrieve(
                knowledge_base_id=knowledge_base_id,
                query=question,
                top_k=top_k,
            )
            if err is not None:
                return [], {"error": str(err)}
            return chunks, {}

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
    def _parse_cited_ids(answer: str) -> list[int]:
        """Parse [ID:x] citations from answer text."""
        if not answer:
            return []
        matches = re.findall(r"\[ID:(\d+)\]", answer)
        return [int(m) for m in matches]

    @staticmethod
    def _is_safe_public_base_url(base_url: str) -> bool:
        """Allow only public http(s) endpoints to reduce SSRF risk."""
        parsed = urlparse((base_url or "").strip())
        if parsed.scheme not in {"http", "https"}:
            return False
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False
        if hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".local"):
            return False
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        except ValueError:
            # Domain name: resolve and reject if any resolved address is non-public.
            try:
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
                infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
                for info in infos:
                    resolved = info[4][0]
                    ip = ipaddress.ip_address(resolved)
                    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                        return False
            except Exception:
                return False
        return True

    @staticmethod
    def _resolve_query_expansion_config(
        query_expansion_mode: ExpansionMode | None = None,
        query_expansion_target: str | None = None,
        query_expansion_llm: dict[str, Any] | None = None,
    ) -> tuple[ExpansionMode, Any]:
        """Resolve request-level query expansion mode and provider with fallback chain."""
        mode = (query_expansion_mode or getattr(settings, "retrieval_query_expansion_mode", "rule"))
        target = (query_expansion_target or "default").lower()
        provider = None

        if mode in ("llm", "hybrid"):
            try:
                # Request-level explicit provider config has highest priority.
                if query_expansion_llm:
                    base_url = query_expansion_llm.get("base_url")
                    if base_url and not QaService._is_safe_public_base_url(str(base_url)):
                        raise ValueError("Unsafe query expansion base_url")

                    timeout_seconds = query_expansion_llm.get("timeout_seconds")
                    if timeout_seconds is not None:
                        timeout_seconds = min(int(timeout_seconds), QaService._expansion_timeout_max)
                    max_retries = query_expansion_llm.get("max_retries")
                    if max_retries is not None:
                        max_retries = min(int(max_retries), QaService._expansion_max_retries_max)
                    retry_base_delay = query_expansion_llm.get("retry_base_delay")
                    if retry_base_delay is not None:
                        retry_base_delay = min(float(retry_base_delay), QaService._expansion_retry_delay_max)

                    provider = build_chat_provider(
                        provider=query_expansion_llm.get("provider"),
                        api_key=query_expansion_llm.get("api_key"),
                        model_name=query_expansion_llm.get("model_name"),
                        base_url=base_url,
                        timeout_seconds=timeout_seconds,
                        max_retries=max_retries,
                        retry_base_delay=retry_base_delay,
                    )
                else:
                    if target == "local":
                        # Local target is reserved for future rollout; fallback to default chain now.
                        logger.info("query_expansion_target=local but local provider is unavailable, fallback to default")
                    provider = get_provider_for_task("query_expansion")
            except Exception as e:
                logger.warning("LLM provider not available for query expansion: %s", e)
                try:
                    provider = get_provider_for_task("query_expansion")
                except Exception:
                    provider = None

        return mode, provider

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
        answer: str | None = None,  # B4.6: for parsing cited_chunk_ids
        # V2.0 质量保障字段
        confidence_score: float | None = None,
        faithfulness_score: float | None = None,
        has_hallucination: bool | None = None,
        retrieval_mode: str | None = None,
        refusal_reason: str | None = None,
        citation_accuracy: float | None = None,
        latency_breakdown: dict | None = None,
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

            # B4.6: Parse cited chunk IDs from answer
            cited_chunk_ids = QaService._parse_cited_ids(answer) if answer else None

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
                    cited_chunk_ids=cited_chunk_ids,
                    retrieval_time_ms=retrieval_time_ms,
                    rerank_time_ms=rerank_time_ms,
                    total_time_ms=total_time_ms,
                    llm_time_ms=llm_time_ms,
                    answer_generated=answer_generated,
                    answer_length=answer_length,
                    error_message=error_message,
                    # V2.0 质量保障字段
                    confidence_score=confidence_score,
                    faithfulness_score=faithfulness_score,
                    has_hallucination=has_hallucination,
                    retrieval_mode=retrieval_mode,
                    refusal_reason=refusal_reason,
                    citation_accuracy=citation_accuracy,
                    latency_breakdown=latency_breakdown,
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
        strategy: str | None = None,  # B4.4: retrieval strategy
        query_expansion_mode: ExpansionMode | None = None,
        query_expansion_target: str | None = None,
        query_expansion_llm: dict[str, Any] | None = None,
        retrieval_mode: str | None = None,  # P0: Override strategy retrieval_mode
    ) -> tuple[dict[str, Any] | None, str | None]:
        start_time = time.perf_counter()

        # B4.3/B4.4: 应用检索策略
        from app.rag.retrieval_strategy import get_strategy
        strat = get_strategy(strategy or settings.retrieval_strategy)

        final_top_k = top_k if top_k is not None else strat.top_k
        retrieve_top_k = max(final_top_k, strat.reranker_candidate_k) if settings.reranker_enabled else final_top_k
        use_expansion = strat.expansion_enabled and settings.retrieval_query_expansion_enabled
        use_keyword = strat.keyword_enabled and settings.retrieval_use_keyword

        # V2.1 Phase 4: Enhanced strategy uses modality-aware retrieval
        enhancement_metadata = {}
        if strategy == "enhanced":
            chunks, enhancement_metadata = QaService._retrieve_with_enhanced(
                knowledge_base_id=knowledge_base_id,
                question=question,
                top_k=final_top_k,
            )
            retrieval_time_ms = enhancement_metadata.get("retrieval_time_ms", 0)
        else:
            retrieval_start = time.perf_counter()
            queries = [question]
            if use_expansion:
                expansion_mode, expansion_llm = QaService._resolve_query_expansion_config(
                    query_expansion_mode=query_expansion_mode,
                    query_expansion_target=query_expansion_target,
                    query_expansion_llm=query_expansion_llm,
                )
                queries = expand_query(
                    question,
                    mode=expansion_mode,
                    llm_provider=expansion_llm,
                    max_extra=2
                ) or [question]
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
            if use_keyword:
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

        answer, citations = QaService._pipeline.insert_citations(raw_answer, chunks, query=question)
        
        # V2.0: 质量保障验证
        verification_result = None
        confidence_score = None
        faithfulness_score = None
        has_hallucination = None
        citation_accuracy = None
        refusal_reason = None
        
        verify_pipeline = QaService._get_verify_pipeline()
        if verify_pipeline:
            try:
                contexts = [c.get("content", "") for c in chunks if c.get("content")]
                avg_score = sum(c.get("rerank_score", 0) for c in chunks) / len(chunks) if chunks else 0
                verification_result = verify_pipeline.verify(answer, contexts, avg_score)
                
                # 提取验证指标
                if verification_result.confidence_score:
                    confidence_score = verification_result.confidence_score.score
                if verification_result.confidence_score and hasattr(verification_result.confidence_score, 'faithfulness'):
                    faithfulness_score = verification_result.confidence_score.faithfulness
                if verification_result.action == VerificationAction.REFUSE:
                    refusal_reason = verification_result.reason
                if verification_result.citation_result:
                    citation_accuracy = verification_result.citation_result.citation_accuracy
                
                logger.info("V2.0 verification: action=%s confidence=%.2f reason=%s",
                           verification_result.action.value, confidence_score or 0, verification_result.reason)
            except Exception as e:
                logger.warning("V2.0 verification failed: %s", e)
        
        QaService._append_history(knowledge_base_id, conversation_id, question, answer)

        # Log successful retrieval with V2.0 metrics
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
            answer=answer,  # B4.6: for cited_chunk_ids
            # V2.0 质量保障字段
            confidence_score=confidence_score,
            faithfulness_score=faithfulness_score,
            has_hallucination=has_hallucination,
            retrieval_mode="hybrid",
            refusal_reason=refusal_reason,
            citation_accuracy=citation_accuracy,
            latency_breakdown={
                "retrieval_ms": retrieval_time_ms,
                "rerank_ms": rerank_time_ms,
                "llm_ms": llm_time_ms,
                "total_ms": total_time_ms,
            },
        )

        return {
            "answer": answer,
            "citations": citations,
            "retrieved_count": len(chunks),
            "conversation_id": conversation_id,
            "retrieval_log_id": log_id,  # Phase 3.2
            # V2.0 质量保障返回字段
            "verification": {
                "action": verification_result.action.value if verification_result else None,
                "confidence_score": confidence_score,
                "citation_accuracy": citation_accuracy,
            } if verification_result else None,
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
        strategy: str | None = None,  # B4.4: retrieval strategy
        query_expansion_mode: ExpansionMode | None = None,
        query_expansion_target: str | None = None,
        query_expansion_llm: dict[str, Any] | None = None,
        retrieval_mode: str | None = None,  # P0: Override strategy retrieval_mode
    ) -> Iterator[str]:
        start_time = time.perf_counter()

        # B4.3/B4.4: 应用检索策略
        from app.rag.retrieval_strategy import get_strategy
        strat = get_strategy(strategy or settings.retrieval_strategy)

        final_top_k = top_k if top_k is not None else strat.top_k
        retrieve_top_k = max(final_top_k, strat.reranker_candidate_k) if settings.reranker_enabled else final_top_k
        use_expansion = strat.expansion_enabled and settings.retrieval_query_expansion_enabled
        use_keyword = strat.keyword_enabled and settings.retrieval_use_keyword

        # V2.1 Phase 4: Enhanced strategy uses modality-aware retrieval
        enhancement_metadata = {}
        if strategy == "enhanced":
            chunks, enhancement_metadata = QaService._retrieve_with_enhanced(
                knowledge_base_id=knowledge_base_id,
                question=question,
                top_k=final_top_k,
            )
            retrieval_time_ms = enhancement_metadata.get("retrieval_time_ms", 0)
        else:
                    retrieval_start = time.perf_counter()
                    queries = [question]
                    if use_expansion:
                        expansion_mode, expansion_llm = QaService._resolve_query_expansion_config(
                            query_expansion_mode=query_expansion_mode,
                            query_expansion_target=query_expansion_target,
                            query_expansion_llm=query_expansion_llm,
                        )
                        queries = expand_query(
                            question,
                            mode=expansion_mode,
                            llm_provider=expansion_llm,
                            max_extra=2
                        ) or [question]
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
                    if use_keyword:
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
        _, citations = QaService._pipeline.insert_citations(merged, chunks, query=question)

        # V2.0: 质量保障验证
        verification_result = None
        confidence_score = None
        faithfulness_score = None
        has_hallucination = None
        citation_accuracy = None
        refusal_reason = None
        
        verify_pipeline = QaService._get_verify_pipeline()
        if verify_pipeline and merged:
            try:
                contexts = [c.get("content", "") for c in chunks if c.get("content")]
                avg_score = sum(c.get("rerank_score", 0) for c in chunks) / len(chunks) if chunks else 0
                verification_result = verify_pipeline.verify(merged, contexts, avg_score)
                
                if verification_result.confidence_score:
                    confidence_score = verification_result.confidence_score.score
                if verification_result.action == VerificationAction.REFUSE:
                    refusal_reason = verification_result.reason
                if verification_result.citation_result:
                    citation_accuracy = verification_result.citation_result.citation_accuracy
                
                logger.info("V2.0 stream verification: action=%s confidence=%.2f",
                           verification_result.action.value, confidence_score or 0)
            except Exception as e:
                logger.warning("V2.0 stream verification failed: %s", e)

        # Log successful retrieval with V2.0 metrics
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
            answer=merged,  # B4.6: for cited_chunk_ids
            # V2.0 质量保障字段
            confidence_score=confidence_score,
            faithfulness_score=faithfulness_score,
            has_hallucination=has_hallucination,
            retrieval_mode="hybrid",
            refusal_reason=refusal_reason,
            citation_accuracy=citation_accuracy,
            latency_breakdown={
                "retrieval_ms": retrieval_time_ms,
                "rerank_ms": rerank_time_ms,
                "llm_ms": llm_time_ms,
                "total_ms": total_time_ms,
            },
        )

        yield f"data: {json.dumps({'type': 'citations', 'data': citations}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'retrieval_log_id', 'data': log_id}, ensure_ascii=False)}\n\n"
        # V2.0: 发送验证结果
        if verification_result:
            yield f"data: {json.dumps({'type': 'verification', 'data': {'action': verification_result.action.value, 'confidence_score': confidence_score, 'citation_accuracy': citation_accuracy}}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
