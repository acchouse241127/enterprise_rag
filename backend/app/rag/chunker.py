"""Text chunking utilities.

Author: C2
Date: 2026-02-27
"""

import re
from typing import Literal

import tiktoken

ChunkMode = Literal["char", "sentence", "chinese_recursive", "token"]


class TextChunker:
    """Split long text into overlapped chunks.

    Supports:
    - 'char' = character sliding window (V1 compatibility)
    - 'sentence' = sentence/paragraph boundary
    - 'chinese_recursive' = recursive splitting by semantic boundaries (recommended)
    - 'token' = token-based splitting using tiktoken
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, mode: ChunkMode = "char") -> list[str]:
        """Chunk text.

        Args:
            text: input text
            mode: chunking mode ('char', 'sentence', 'chinese_recursive', 'token')

        Returns:
            list of chunks
        """
        normalized = text.strip()
        if not normalized:
            return []
        if mode == "sentence":
            return self._chunk_by_sentence(normalized)
        if mode == "chinese_recursive":
            return self._chunk_chinese_recursive(normalized)
        if mode == "token":
            return self._chunk_by_token(normalized)
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

    def _chunk_chinese_recursive(self, text: str) -> list[str]:
        """中文递归分块：按语义边界递归切分（推荐模式）。

        分隔符优先级（高到低）：
        1. 段落边界
        2. 换行符
        3. 句号
        4. 分号
        5. 逗号
        """
        separators = ["\n\n", "\n", "。", "；", "，"]
        return self._recursive_split(text, separators)

    def _recursive_split(self, text: str, separators: list[str], depth: int = 0) -> list[str]:
        """递归分块算法。"""
        if depth >= len(separators) or len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        sep = separators[depth]
        parts = text.split(sep)
        chunks = []
        current = []
        current_len = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if current_len + len(part) + 1 <= self.chunk_size:
                current.append(part)
                current_len += len(part) + 1
            else:
                if current:
                    chunks.append(sep.join(current))
                if len(part) > self.chunk_size:
                    # 单个部分仍超过限制，递归使用下一级分隔符
                    sub_chunks = self._recursive_split(part, separators, depth + 1)
                    chunks.extend(sub_chunks)
                    current = []
                    current_len = 0
                else:
                    current = [part]
                    current_len = len(part) + 1

        if current:
            chunks.append(sep.join(current))
        return chunks

    def _chunk_by_token(self, text: str) -> list[str]:
        """Token级分块：使用 tiktoken 控制大小。"""
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        chunks = []
        start = 0
        step = max(1, int(self.chunk_size * 0.75)) - int(self.chunk_overlap * 0.75)

        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = enc.decode(chunk_tokens)
            if chunk_text:
                chunks.append(chunk_text)
            if end == len(tokens):
                break
            start += step
        return chunks

