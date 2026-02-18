"""
Chunk deduplication using SimHash.

Author: C2
Date: 2026-02-13
Task: C2-2.3.1
"""

from __future__ import annotations

import re
from typing import Sequence


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer: split by non-word characters, lowercase."""
    return [t.lower() for t in re.split(r"\W+", text) if t]


def _hash64(s: str) -> int:
    """Simple 64-bit hash using Python's built-in hash (for demonstration).
    
    In production, consider using a more robust hash like xxhash or mmh3.
    """
    h = hash(s)
    # Ensure positive 64-bit value
    return h & 0xFFFFFFFFFFFFFFFF


def simhash(text: str) -> int:
    """Compute SimHash fingerprint for a text string.
    
    Returns a 64-bit integer fingerprint.
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0

    # Initialize 64 counters
    v = [0] * 64

    for token in tokens:
        h = _hash64(token)
        for i in range(64):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    # Build fingerprint
    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(fp1: int, fp2: int) -> int:
    """Compute Hamming distance between two SimHash fingerprints."""
    xor = fp1 ^ fp2
    return bin(xor).count("1")


def deduplicate_chunks(
    chunks: Sequence[dict],
    threshold: int = 3,
    content_key: str = "content",
) -> list[dict]:
    """Remove near-duplicate chunks using SimHash.
    
    Args:
        chunks: List of chunk dictionaries.
        threshold: Hamming distance threshold. Chunks with distance <= threshold
                   are considered duplicates.
        content_key: Key to access text content in chunk dict.
    
    Returns:
        Deduplicated list of chunks (preserves order, keeps first occurrence).
    """
    if not chunks:
        return []

    seen_fingerprints: list[int] = []
    result: list[dict] = []

    for chunk in chunks:
        content = chunk.get(content_key, "")
        if not content:
            # Keep chunks without content (edge case)
            result.append(chunk)
            continue

        fp = simhash(content)

        # Check against all seen fingerprints
        is_duplicate = False
        for seen_fp in seen_fingerprints:
            if hamming_distance(fp, seen_fp) <= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_fingerprints.append(fp)
            result.append(chunk)

    return result
