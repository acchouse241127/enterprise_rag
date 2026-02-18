"""Text chunking utilities."""


class TextChunker:
    """Split long text into overlapped chunks."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        """Chunk text by character window with overlap."""
        normalized = text.strip()
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        text_len = len(normalized)
        step = self.chunk_size - self.chunk_overlap
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            piece = normalized[start:end].strip()
            if piece:
                chunks.append(piece)
            if end == text_len:
                break
            start += step
        return chunks

