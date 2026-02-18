"""Text chunking utilities."""

import re
from typing import Literal

ChunkMode = Literal["char", "sentence"]


class TextChunker:
    """Split long text into overlapped chunks. Supports char window or sentence boundary."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, mode: ChunkMode = "char") -> list[str]:
        """Chunk text. mode: 'char' = sliding window; 'sentence' = by sentence/paragraph then merge to ~chunk_size."""
        normalized = text.strip()
        if not normalized:
            return []
        if mode == "sentence":
            return self._chunk_by_sentence(normalized)
        return self._chunk_by_char(normalized)

    def _chunk_by_char(self, text: str) -> list[str]:
        """Sliding window by character."""
        chunks: list[str] = []
        start = 0
        text_len = len(text)
        step = self.chunk_size - self.chunk_overlap
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            piece = text[start:end].strip()
            if piece:
                chunks.append(piece)
            if end == text_len:
                break
            start += step
        return chunks

    def _chunk_by_sentence(self, text: str) -> list[str]:
        """Split by sentence/paragraph boundaries, then merge segments to ~chunk_size."""
        # 按句/段切：中英文句号、换行、问号、感叹号
        parts = re.split(r"(?<=[。！？!?\n])\s*", text)
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            return self._chunk_by_char(text)
        chunks = []
        current = []
        current_len = 0
        for p in parts:
            p_len = len(p) + 1
            if current_len + p_len > self.chunk_size and current:
                chunks.append(" ".join(current))
                overlap_parts = []
                overlap_len = 0
                for x in reversed(current):
                    if overlap_len + len(x) + 1 <= self.chunk_overlap:
                        overlap_parts.append(x)
                        overlap_len += len(x) + 1
                    else:
                        break
                current = list(reversed(overlap_parts)) + [p]
                current_len = sum(len(x) for x in current) + len(current) - 1
            else:
                current.append(p)
                current_len += p_len
        if current:
            chunks.append(" ".join(current))
        return chunks

