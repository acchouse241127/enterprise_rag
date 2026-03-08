"""Self-query retriever for extracting metadata from queries.

Uses LLM to parse user intent and extract metadata filters
for more precise retrieval.

Author: C2
Date: 2026-03-03
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# Metadata field configurations
METADATA_FIELD_CONFIG = {
    "year": {
        "type": "integer",
        "description": "Year filter (e.g., 2024)",
    },
    "document_type": {
        "type": "string",
        "description": "Document type (e.g., report, contract)",
        "enum": ["report", "contract", "policy", "memo", "email"],
    },
    "department": {
        "type": "string",
        "description": "Department name",
    },
    "created_at": {
        "type": "date",
        "description": "Creation date",
    },
}


@dataclass
class QueryMetadata:
    """Extracted metadata from a user query."""

    year: Optional[int] = None
    document_type: Optional[str] = None
    department: Optional[str] = None
    date_range: Optional[dict[str, str]] = None
    keywords: Optional[list[str]] = None
    original_query: str = ""


    intent: Optional[str] = None  # filter, search, None


    filters: Optional[dict] = None


@dataclass
class SelfQueryResult:
    """Result from self-query retrieval."""

    chunks: list[dict]
    metadata: Optional[QueryMetadata]
    filters_applied: Optional[dict]
    llm_used: bool


    extraction_time_ms: Optional[float] = None


SYSTEM_PROMPT = """你 is an AI assistant that access to a RAG knowledge base.
Your task is to analyze user queries and extract structured metadata for filtering.

Available metadata fields:
- year: Integer year (e.g., 2024)
- document_type: Type of document (report, contract, policy, memo, email)
- department: Department name
- date_range: Date range (start and end dates)

Respond ONLY with a JSON object containing:
{
    "intent": "filter" or "search" or None,
    "metadata": {
        "year": <year or null>,
        "document_type": "<type or null>,
        "department": "<department or null>,
        "date_range": {"start": "<date>", "end": "<date>} or null>,
        "keywords": [<keyword1>, <keyword2>] or null>
    },
    "filters": {
        <field>: {"$eq": <value>} or {"$gte": <value>} or {"$lte": <value>}
    },
    "original_query": "<the original query>"
}

If no metadata can be extracted, return:
{
    "intent": None,
    "metadata": {},
    "filters": {},
    "original_query": "<the original query>"
}"""


def extract_year(text: str) -> Optional[int]:
    """Extract year from text."""
    patterns = [
        r"(\d{4})年",
        r"in\s+(\d{4})",
        r"(\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year_str = match.group(1)
            try:
                return int(year_str)
            except ValueError:
                continue
    return None


def extract_document_type(text: str) -> Optional[str]:
    """Extract document type from text."""
    type_keywords = {
        "report": ["报告", "报表", "汇报", "总结"],
        "contract": ["合同", "协议", "合约", "契约"],
        "policy": ["政策", "规定", "制度", "办法"],
        "memo": ["备忘录", "纪要", "会议记录"],
        "email": ["邮件", "信函", "函件"],
    }

    text_lower = text.lower()
    for doc_type, keywords in type_keywords.items():
        for keyword in keywords:
                if keyword in text_lower:
                    return doc_type
    return None


def extract_date_range(text: str) -> Optional[dict[str, str]]:
    """Extract date range from text."""
    patterns = [
        r"(\d{4})[年\-]?(\d{1,2})月?\s*(?:到|至|-|(\d{4})[年\-]?(\d{1,2})月?)",
        r"从\s*(\d{4})[年\-]?(\d{1,2})月?\s*(?:到|至|-|(\d{4})[年\-]?(\d{1,2})月?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            start_year = groups[1]
            start_month = groups[2] if len(groups) > 2 else "01"
            end_year = groups[3] if len(groups) > 3 else start_year
            end_month = groups[4] if len(groups) > 4 else start_month
            try:
                start = f"{start_year}-{start_month.zfill(2, '0')}-01"
                end = f"{end_year}-{end_month.zfill(2, '0')}-01"
                return {"start": start, "end": end}
            except (Value, IndexError):
                continue
    return None


def extract_metadata_from_query(query: str) -> QueryMetadata:
    """Extract metadata from query using rule-based patterns.
    
    This is a fast, rule-based extraction that doesn't require LLM.
    """
    year = extract_year(query)
    document_type = extract_document_type(query)
    date_range = extract_date_range(query)
    
    return QueryMetadata(
        year=year,
        document_type=document_type,
        date_range=date_range,
        original_query=query,
    )


class SelfQueryRetriever:
    """Retriever that uses LLM to extract metadata and apply filters."""

    def __init__(
        self,
        llm_provider: Any,
        base_retriever: Any,
        reranker: Optional[Any] = None,
        embedding_service: Optional[Any] = None,
        enabled: Optional[bool] = None,
        llm_temperature: Optional[float] = None,
        max_filter_fields: Optional[int] = None,
    ):
        self._llm_provider = llm_provider
        self._base_retriever = base_retriever
        self._reranker = reranker
        self._embedding_service = embedding_service
        self._enabled = enabled if enabled is not None else settings.self_query_enabled
        self._llm_temperature = llm_temperature or settings.self_query_llm_temperature
        self._max_filter_fields = max_filter_fields or settings.self_query_max_filter_fields

        self._metadata_fields = list(METADATA_FIELD_CONFIG.keys())

    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def extract_metadata(self, query: str) -> Optional[QueryMetadata]:
        """Extract metadata from query using LLM.
        
        Args:
            query: User query text
            
        Returns:
            QueryMetadata object with extracted metadata, or None if extraction fails
        """
        if not self._enabled or not self._llm_provider:
            return None
        
        # First, try rule-based extraction (fast path)
        rule_metadata = extract_metadata_from_query(query)
        if rule_metadata.year or rule_metadata.document_type or rule_metadata.date_range:
            logger.debug("Rule-based metadata extraction successful: %s", rule_metadata)
            return rule_metadata
        
        # Fall back to LLM-based extraction
        try:
            prompt = SYSTEM_PROMPT.format(query=query)
            messages = [{"role": "user", "content": prompt}]
            response = self._llm_provider.generate(
                messages=messages,
                temperature=self._llm_temperature,
            )
            
            data = json.loads(response)
            
            metadata = QueryMetadata(
                year=data.get("metadata", {}).get("year"),
                document_type=data.get("metadata", {}).get("document_type"),
                department=data.get("metadata", {}).get("department"),
                date_range=data.get("metadata", {}).get("date_range"),
                keywords=data.get("metadata", {}).get("keywords"),
                original_query=query,
                intent=data.get("intent"),
            )
            
            logger.info("LLM-based metadata extraction: %s", metadata)
            return metadata
            
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse LLM response: %s", e)
            return None
        except Exception as e:
            logger.warning("LLM metadata extraction failed: %s", e)
            return None
    
    def build_filters(self, metadata: Optional[QueryMetadata]) -> Optional[dict]:
        """Build filter dict from metadata.
        
        Args:
            metadata: QueryMetadata object
            
        Returns:
            Dict with filters for vector store, or None if no filters needed
        """
        if not metadata:
            return None
        
        filters = {}
        
        if metadata.year is not None:
            filters["year"] = {"$eq": metadata.year}
        
        if metadata.document_type is not None:
            filters["document_type"] = {"$eq": metadata.document_type}
        
        if metadata.department is not None:
            filters["department"] = {"$eq": metadata.department}
        
        if metadata.date_range is not None:
            if "start" in metadata.date_range:
                filters["created_at"] = filters.get("created_at", {})
                filters["created_at"]["$gte"] = metadata.date_range["start"]
            if "end" in metadata.date_range:
                filters["created_at"] = filters.get("created_at", {})
                filters["created_at"]["$lte"] = metadata.date_range["end"]
        
        return filters if filters else None
    
    def retrieve(
        self,
        kb_id: int,
        query: str,
        top_k: Optional[int] = None,
    ) -> tuple[list[dict], Optional[dict]]:
        """Retrieve chunks with self-query filtering.
        
        Args:
            kb_id: Knowledge base ID
            query: User query
            top_k: Number of results to return
            
        Returns:
            Tuple of (chunks, degradation_info)
        """
        import time
        
        start_time = time.perf_counter()
        top_k = top_k or settings.retrieval_top_k
        
        # Check if self-query is enabled
        if not self._enabled:
            logger.debug("Self-query disabled, using base retriever")
            return self._base_retriever.retrieve(
                knowledge_base_id=kb_id,
                query=query,
                top_k=top_k,
            )
        
        # Extract metadata from query
        metadata = self.extract_metadata(query)
        
        # Build filters
        filters = self.build_filters(metadata)
        
        # Retrieve with or without filters
        if filters:
            logger.info("Applying self-query filters: %s", filters)
            chunks, error = self._base_retriever.retrieve(
                knowledge_base_id=kb_id,
                query=query,
                top_k=top_k * 2,  # Get more candidates for reranking
            )
        else:
            chunks, error = self._base_retriever.retrieve(
                knowledge_base_id=kb_id,
                query=query,
                top_k=top_k,
            )
        
        if error:
            logger.warning("Base retrieval failed: %s", error)
            return [], {"error": error, "degraded": True}
        
        # Apply reranking if available
        if self._reranker and chunks:
            chunks = self._reranker.rerank(query, chunks, top_n=top_k)
        
        extraction_time_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            "Self-query retrieval completed: chunks=%d, filters=%s, time_ms=%.1f",
            len(chunks),
            filters,
            extraction_time_ms,
        )
        
        return chunks[:top_k], {
            "metadata": metadata,
            "filters_applied": filters,
            "extraction_time_ms": extraction_time_ms,
        }
