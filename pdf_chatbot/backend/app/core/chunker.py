"""
chunker.py - Page-aware text chunking with coordinate preservation.
Ensures every chunk is strictly mapped to its origin page number and bounding box.
"""

from typing import List, Dict, Any
from app.config import settings
from app.core.extractor import ExtractedPage
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Chunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        page_number: int,
        text: str,
        bounding_box: Dict[str, float] = None,
        char_start: int = 0,
        char_end: int = 0
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.page_number = page_number
        self.text = text
        self.bounding_box = bounding_box or {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 0.0}
        self.char_start = char_start
        self.char_end = char_end

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "text": self.text,
            "bounding_box": self.bounding_box,
            "char_start": self.char_start,
            "char_end": self.char_end
        }


class PageAwareChunker:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_document(self, pages: List[ExtractedPage], document_id: str) -> List[Chunk]:
        """
        Splits extracted pages into overlapping chunks while preserving:
        1. Exact page number
        2. Bounding box coordinates from text block analysis
        """
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0

        for page in pages:
            page_text = page.text
            if not page_text:
                continue

            # Split within page boundaries so chunks never cross pages without label
            page_chunks = self._chunk_page_text(page_text, self.chunk_size, self.chunk_overlap)

            for local_idx, (chunk_text, start_char, end_char) in enumerate(page_chunks):
                # Calculate approximate bounding box from page blocks
                bbox = self._find_approximate_bbox(chunk_text, page.blocks, page.width, page.height)

                chunk = Chunk(
                    chunk_id=f"{document_id}_p{page.page_number}_c{local_idx}",
                    document_id=document_id,
                    page_number=page.page_number,
                    text=chunk_text,
                    bounding_box=bbox,
                    char_start=start_char,
                    char_end=end_char
                )
                all_chunks.append(chunk)
                global_chunk_idx += 1

        logger.info(f"PageAwareChunker created {len(all_chunks)} chunks across {len(pages)} pages.")
        return all_chunks

    def _chunk_page_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[tuple]:
        """Sliding window chunking by character count with natural sentence/paragraph breaks."""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)

            # If not at the end of text, try to find a natural boundary (paragraph or sentence)
            if end < text_len:
                # Look backwards for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break != -1 and para_break > start + (chunk_size // 2):
                    end = para_break + 2
                else:
                    # Look backwards for period + space or newline
                    sent_break = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
                    if sent_break != -1 and sent_break > start + (chunk_size // 2):
                        end = sent_break + 1

            chunk_slice = text[start:end].strip()
            if chunk_slice:
                chunks.append((chunk_slice, start, end))

            # Step forward by chunk_size - overlap
            step = max(chunk_size - chunk_overlap, 100)
            if start + step >= text_len or end == text_len:
                break
            start += step

        return chunks

    def _find_approximate_bbox(self, chunk_text: str, blocks: List[Dict[str, Any]], page_w: float, page_h: float) -> Dict[str, float]:
        """Finds the bounding rectangle enclosing the words in this chunk."""
        if not blocks or page_w == 0 or page_h == 0:
            return {"x0": 0.05, "y0": 0.1, "x1": 0.95, "y1": 0.9}

        # Normalize coordinates relative to page dimensions (0.0 to 1.0)
        matching_boxes = []
        sample_words = [w.lower() for w in chunk_text.split()[:10] if len(w) > 3]

        for b in blocks:
            b_text = b.get("text", "").lower()
            if any(w in b_text for w in sample_words):
                matching_boxes.append(b.get("bbox", [0, 0, 0, 0]))

        if matching_boxes:
            min_x0 = min(box[0] for box in matching_boxes) / page_w
            min_y0 = min(box[1] for box in matching_boxes) / page_h
            max_x1 = max(box[2] for box in matching_boxes) / page_w
            max_y1 = max(box[3] for box in matching_boxes) / page_h

            return {
                "x0": max(0.0, min(1.0, round(min_x0, 3))),
                "y0": max(0.0, min(1.0, round(min_y0, 3))),
                "x1": max(0.0, min(1.0, round(max_x1, 3))),
                "y1": max(0.0, min(1.0, round(max_y1, 3))),
            }

        return {"x0": 0.05, "y0": 0.1, "x1": 0.95, "y1": 0.3}
