from typing import Any, Dict, List


class TextChunker:
    """
    Sliding window text chunker for industrial SOPs, technical manuals, and inspection reports.
    Preserves document source, page number, and chunk offsets.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self,
        text: str,
        document_name: str,
        page: int = 1,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split raw text into overlapping chunks with metadata.
        """
        if not text or not text.strip():
            return []

        chunks: List[Dict[str, Any]] = []
        start = 0
        text_len = len(text)
        chunk_idx = 0

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # If not at the end of the text, try to break at paragraph / sentence / space
            if end < text_len:
                break_point = max(
                    text.rfind("\n\n", start, end),
                    text.rfind(". ", start, end),
                    text.rfind(" ", start, end)
                )
                if break_point > start + (self.chunk_size // 2):
                    end = break_point + 1

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunk_meta = dict(metadata or {})
                chunk_meta.update({
                    "document": document_name,
                    "page": page,
                    "chunk_index": chunk_idx,
                    "start_offset": start,
                    "end_offset": end,
                    "char_count": len(chunk_content)
                })

                chunks.append({
                    "id": f"{document_name}_p{page}_c{chunk_idx}",
                    "content": chunk_content,
                    "metadata": chunk_meta
                })
                chunk_idx += 1

            if end >= text_len:
                break

            start = max(start + 1, end - self.chunk_overlap)

        return chunks


chunker = TextChunker()
