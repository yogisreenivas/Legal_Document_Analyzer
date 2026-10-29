"""
test_chunker.py - Unit tests for the text chunking module.

Tests cover:
- Chunk creation with default settings
- Chunk size constraints
- Metadata (chunk_id, source, page) preservation
- Edge cases: empty input, single-sentence input
- Custom chunk size/overlap
"""

import sys
from pathlib import Path

# Add project root to path for imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from langchain_core.documents import Document
from app.ingestion.chunker import create_chunks, get_chunk_summary


# ── Test Data ─────────────────────────────────────────────────

SAMPLE_TEXT = """
1. TERMINATION CLAUSE

This Agreement may be terminated by either party upon providing thirty (30) days
written notice to the other party. In the event of a material breach, the
non-breaching party may terminate immediately upon written notice.

2. PAYMENT TERMS

The Tenant shall pay a monthly rent of INR 35,000 on or before the 5th of each
month. Late payments shall attract a penalty of INR 200 per day of delay,
up to a maximum of INR 3,000 per month.

3. CONFIDENTIALITY

Both parties agree to maintain the confidentiality of all proprietary information
disclosed during the term of this Agreement. This obligation shall survive
termination for a period of five (5) years.

4. DISPUTE RESOLUTION

Any dispute arising out of this Agreement shall first be resolved through
mediation. If mediation fails, the dispute shall be referred to arbitration
in accordance with the Arbitration and Conciliation Act, 1996.
"""


def _create_test_documents() -> list:
    """Helper to create test Document objects."""
    return [
        Document(
            page_content=SAMPLE_TEXT,
            metadata={"source": "test_doc.txt", "page": 1},
        )
    ]


# ── Tests ─────────────────────────────────────────────────────


class TestCreateChunks:
    """Tests for the create_chunks function."""

    def test_creates_chunks_from_documents(self):
        """Chunks should be created from input documents."""
        docs = _create_test_documents()
        chunks = create_chunks(docs, chunk_size=200, chunk_overlap=50)

        assert len(chunks) > 0, "Should create at least one chunk"
        assert len(chunks) > 1, "Should create multiple chunks from a long document"

    def test_chunk_size_respected(self):
        """Each chunk should not exceed the specified chunk_size."""
        docs = _create_test_documents()
        chunk_size = 300
        chunks = create_chunks(docs, chunk_size=chunk_size, chunk_overlap=50)

        for chunk in chunks:
            # Allow some tolerance because the splitter doesn't hard-cut.
            assert len(chunk.page_content) <= chunk_size + 100, (
                f"Chunk too long: {len(chunk.page_content)} > {chunk_size + 100}"
            )

    def test_chunk_metadata_has_chunk_id(self):
        """Each chunk should have a unique chunk_id in metadata."""
        docs = _create_test_documents()
        chunks = create_chunks(docs, chunk_size=200, chunk_overlap=50)

        chunk_ids = [c.metadata.get("chunk_id") for c in chunks]
        assert all(cid is not None for cid in chunk_ids), "All chunks need chunk_id"
        assert len(set(chunk_ids)) == len(chunk_ids), "chunk_ids should be unique"

    def test_source_metadata_preserved(self):
        """Source metadata from the original document should be preserved."""
        docs = _create_test_documents()
        chunks = create_chunks(docs, chunk_size=200, chunk_overlap=50)

        for chunk in chunks:
            assert "source" in chunk.metadata, "Chunk should have 'source' metadata"
            assert chunk.metadata["source"] == "test_doc.txt"

    def test_page_metadata_preserved(self):
        """Page metadata from the original document should be preserved."""
        docs = _create_test_documents()
        chunks = create_chunks(docs, chunk_size=200, chunk_overlap=50)

        for chunk in chunks:
            assert "page" in chunk.metadata, "Chunk should have 'page' metadata"

    def test_empty_input(self):
        """Empty input should return empty output."""
        chunks = create_chunks([], chunk_size=200, chunk_overlap=50)
        assert chunks == [], "Empty input should produce empty output"

    def test_single_short_document(self):
        """A very short document should produce a single chunk."""
        docs = [
            Document(
                page_content="This is a short sentence.",
                metadata={"source": "short.txt", "page": 1},
            )
        ]
        chunks = create_chunks(docs, chunk_size=1000, chunk_overlap=100)

        assert len(chunks) == 1, "Short doc should produce exactly one chunk"
        assert chunks[0].page_content == "This is a short sentence."

    def test_custom_chunk_size(self):
        """Different chunk sizes should produce different numbers of chunks."""
        docs = _create_test_documents()

        chunks_small = create_chunks(docs, chunk_size=150, chunk_overlap=30)
        chunks_large = create_chunks(docs, chunk_size=500, chunk_overlap=50)

        assert len(chunks_small) > len(chunks_large), (
            "Smaller chunk size should produce more chunks"
        )

    def test_overlap_creates_shared_content(self):
        """Overlapping chunks should share some content at boundaries."""
        continuous_text = (
            "The quick brown fox jumps over the lazy dog repeatedly in order to "
            "generate sufficient textual length for verifying the chunk overlap mechanism. "
        ) * 5
        docs = [
            Document(
                page_content=continuous_text,
                metadata={"source": "test_overlap.txt", "page": 1},
            )
        ]
        chunks = create_chunks(docs, chunk_size=120, chunk_overlap=40)

        assert len(chunks) >= 2, "Expected multiple chunks"

        # Check that the end of chunk N overlaps with the start of chunk N+1.
        chunk_0_end = chunks[0].page_content[-30:]
        chunk_1_start = chunks[1].page_content[:40]

        # At least some words should be shared.
        end_words = set(chunk_0_end.lower().split())
        start_words = set(chunk_1_start.lower().split())
        shared = end_words & start_words

        assert len(shared) > 0, "Overlapping chunks should share some words"


class TestGetChunkSummary:
    """Tests for the get_chunk_summary function."""

    def test_summary_with_chunks(self):
        """Summary should contain correct statistics."""
        docs = _create_test_documents()
        chunks = create_chunks(docs, chunk_size=200, chunk_overlap=50)
        summary = get_chunk_summary(chunks)

        assert summary["total_chunks"] == len(chunks)
        assert summary["avg_length"] > 0
        assert summary["min_length"] > 0
        assert summary["max_length"] >= summary["min_length"]
        assert "test_doc.txt" in summary["sources"]

    def test_summary_empty_input(self):
        """Summary of empty input should have zero values."""
        summary = get_chunk_summary([])

        assert summary["total_chunks"] == 0
        assert summary["avg_length"] == 0
