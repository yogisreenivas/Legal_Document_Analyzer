"""
test_chunker.py - Unit tests for PageAwareChunker.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.core.extractor import ExtractedPage
from app.core.chunker import PageAwareChunker


def test_chunker_preserves_page_numbers():
    chunker = PageAwareChunker(chunk_size=200, chunk_overlap=30)
    pages = [
        ExtractedPage(
            page_number=1,
            text="This is page 1 content. " * 15,
            blocks=[{"bbox": [10, 10, 500, 700], "text": "This is page 1 content."}],
            width=595,
            height=842
        ),
        ExtractedPage(
            page_number=2,
            text="This is page 2 content. " * 12,
            blocks=[{"bbox": [10, 10, 500, 700], "text": "This is page 2 content."}],
            width=595,
            height=842
        ),
    ]

    chunks = chunker.chunk_document(pages, "test_doc_123")
    assert len(chunks) > 2

    # Verify that each chunk has correct page number
    p1_chunks = [c for c in chunks if c.page_number == 1]
    p2_chunks = [c for c in chunks if c.page_number == 2]

    assert len(p1_chunks) > 0
    assert len(p2_chunks) > 0

    for c in chunks:
        assert c.document_id == "test_doc_123"
        assert c.bounding_box is not None
        assert "x0" in c.bounding_box
        assert "y0" in c.bounding_box


def test_chunker_empty_page_handling():
    chunker = PageAwareChunker(chunk_size=300, chunk_overlap=50)
    pages = [
        ExtractedPage(page_number=1, text="", blocks=[], width=595, height=842),
        ExtractedPage(page_number=2, text="Actual text on page 2.", blocks=[], width=595, height=842)
    ]
    chunks = chunker.chunk_document(pages, "doc_empty_test")
    assert len(chunks) == 1
    assert chunks[0].page_number == 2
    assert "Actual text on page 2" in chunks[0].text
