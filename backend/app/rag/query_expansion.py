"""Query expansion for retrieval: return original query plus optional rewrites (stub for now)."""


def expand_query(query: str, max_extra: int = 2) -> list[str]:
    """
    Return [query] or [query, rewrite1, ...] for multi-query retrieval.
    Currently returns [query] only; can be extended with rules or LLM.
    """
    q = (query or "").strip()
    if not q:
        return []
    return [q]
