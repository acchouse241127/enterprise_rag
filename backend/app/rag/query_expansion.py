"""Query expansion for retrieval: rule-based and LLM-based approaches."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.llm import BaseChatProvider

logger = logging.getLogger(__name__)

ExpansionMode = Literal["rule", "llm", "hybrid"]

# 常见中文停用词
CHINESE_STOPWORDS = {
    "的", "了", "和", "是", "就", "都", "而", "及", "与", "着",
    "或", "一个", "没有", "我们", "你们", "他们", "它们", "这个",
    "那个", "哪些", "什么", "怎么", "如何", "为什么", "哪", "哪有",
    "请", "请问", "能", "能否", "可以", "可否", "我想", "我要",
    "帮我", "帮忙", "告诉", "知道", "了解", "查一下", "看一下",
}

# 常见英文停用词
ENGLISH_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "what", "which", "who", "whom",
    "how", "when", "where", "why", "please", "tell", "show", "give",
}

# 常见同义词映射（可根据业务扩展）
SYNONYMS = {
    # 中文同义词
    "如何": ["怎么", "怎样", "方法"],
    "怎么": ["如何", "怎样", "方法"],
    "为什么": ["原因", "为何", "因何"],
    "区别": ["差异", "不同", "差别"],
    "优点": ["优势", "好处", "长处"],
    "缺点": ["劣势", "不足", "短处"],
    "方法": ["方式", "办法", "做法"],
    "设置": ["配置", "设定", "配置"],
    "删除": ["移除", "清除", "去掉"],
    "添加": ["增加", "新增", "加入"],
    "修改": ["更改", "变更", "编辑"],
    "查询": ["搜索", "查找", "检索"],
    "问题": ["疑问", "困惑", "难题"],
    "解决": ["处理", "解决", "应对"],
    "实现": ["完成", "达成", "实现"],
    # 英文同义词
    "how": ["way", "method", "approach"],
    "what": ["which", "thing"],
    "why": ["reason", "cause"],
    "create": ["make", "build", "generate"],
    "delete": ["remove", "clear", "erase"],
    "update": ["modify", "change", "edit"],
    "get": ["fetch", "retrieve", "obtain"],
    "find": ["search", "locate", "look"],
    "fix": ["solve", "resolve", "repair"],
}


def _tokenize(text: str) -> list[str]:
    """Simple tokenization: split by whitespace and punctuation."""
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    return tokens


def _remove_stopwords(tokens: list[str]) -> list[str]:
    """Remove stopwords from token list."""
    all_stopwords = CHINESE_STOPWORDS | ENGLISH_STOPWORDS
    return [t for t in tokens if t not in all_stopwords]


def _expand_with_synonyms(tokens: list[str]) -> list[str]:
    """Expand tokens with synonyms, return original + synonyms."""
    expanded = list(tokens)
    for token in tokens:
        if token in SYNONYMS:
            expanded.extend(SYNONYMS[token][:2])  # 每个词最多加2个同义词
    return expanded


def expand_query_rule(query: str, max_extra: int = 2) -> list[str]:
    """
    Rule-based query expansion using synonyms and stopwords removal.

    Args:
        query: Original user query
        max_extra: Maximum number of expanded queries to return

    Returns:
        List of expanded queries (original + variations)
    """
    q = (query or "").strip()
    if not q:
        return []

    # Original query is always included
    queries = [q]

    # Tokenize and process
    tokens = _tokenize(q)
    tokens_no_stop = _remove_stopwords(tokens)

    # Strategy 1: Query without stopwords
    if tokens_no_stop and " ".join(tokens_no_stop) != q.lower():
        cleaned = " ".join(tokens_no_stop)
        queries.append(cleaned)

    # Strategy 2: Query with synonyms
    tokens_with_syn = _expand_with_synonyms(tokens_no_stop)
    if len(tokens_with_syn) > len(tokens_no_stop):
        expanded = " ".join(tokens_with_syn[:len(tokens_no_stop) + 3])  # 限制长度
        if expanded != q.lower() and expanded not in queries:
            queries.append(expanded)

    return queries[:max_extra + 1]


def expand_query_llm(query: str, llm_provider: "BaseChatProvider | None", max_extra: int = 2) -> list[str]:
    """
    LLM-based query expansion.

    Args:
        query: Original user query
        llm_provider: LLM provider instance
        max_extra: Maximum number of expanded queries to return

    Returns:
        List of expanded queries (original + LLM-generated)
    """
    q = (query or "").strip()
    if not q:
        return []

    # Original query is always included
    queries = [q]

    if llm_provider is None:
        logger.warning("LLM provider not available for query expansion, using original only")
        return queries

    prompt = f"""请将以下用户问题改写成{max_extra}个语义相同但表达不同的搜索查询，用于文档检索。

原始问题：{q}

要求：
1. 保持原意，但使用不同的词汇和句式
2. 每行一个改写后的查询
3. 不要添加解释或编号
4. 如果原问题很短，可以适当扩展关键概念

改写后的查询："""

    try:
        from app.llm import ChatMessage
        messages = [ChatMessage(role="user", content=prompt)]
        response = llm_provider.generate(messages=messages, temperature=0.3)

        # Parse response: each line is a query
        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            # Remove common prefixes like "1.", "1)", "-", etc.
            line = re.sub(r"^[\d]+[.、)\]]\s*", "", line)
            line = re.sub(r"^[-*]\s*", "", line)
            if line and line != q and len(line) > 2:
                queries.append(line)
                if len(queries) > max_extra + 1:
                    break

        logger.info("LLM query expansion: '%s' -> %s", q, queries)
    except Exception as e:
        logger.warning("LLM query expansion failed: %s", e)

    return queries[:max_extra + 1]


def _normalize_query_text(query: str) -> str:
    """Normalize query text for deduplication."""
    return re.sub(r"\s+", " ", (query or "").strip()).lower()


def _merge_and_limit_queries(
    base_query: str,
    query_groups: list[list[str]],
    max_extra: int,
) -> list[str]:
    """Merge multiple query groups with stable deduplication and truncation."""
    merged: list[str] = [base_query]
    seen = {_normalize_query_text(base_query)}

    for group in query_groups:
        for item in group:
            text = (item or "").strip()
            if not text:
                continue
            key = _normalize_query_text(text)
            if key in seen:
                continue
            seen.add(key)
            merged.append(text)
            if len(merged) >= max_extra + 1:
                return merged
    return merged[:max_extra + 1]


def expand_query(
    query: str,
    mode: ExpansionMode = "rule",
    llm_provider: "BaseChatProvider | None" = None,
    max_extra: int = 2,
) -> list[str]:
    """
    Expand query using specified mode.

    Args:
        query: Original user query
        mode: Expansion mode - "rule", "llm", or "hybrid"
        llm_provider: LLM provider instance (required for "llm" mode)
        max_extra: Maximum number of expanded queries to return

    Returns:
        List of expanded queries
    """
    q = (query or "").strip()
    if not q:
        return []

    if mode == "rule":
        return expand_query_rule(q, max_extra)
    elif mode == "llm":
        return expand_query_llm(q, llm_provider, max_extra)
    elif mode == "hybrid":
        # Hybrid = rule + llm: merge both sources, keep original highest priority.
        rule_queries = expand_query_rule(q, max_extra=max_extra)
        llm_queries = expand_query_llm(q, llm_provider, max_extra=max_extra)
        return _merge_and_limit_queries(
            q,
            [
                rule_queries[1:],  # skip original query
                llm_queries[1:],   # skip original query
            ],
            max_extra=max_extra,
        )
    else:
        logger.warning("Unknown expansion mode '%s', using original query only", mode)
        return [q]
