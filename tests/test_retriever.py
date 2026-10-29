"""
test_retriever.py - Unit tests for the retrieval module.

Tests cover:
- Retrieval returns correct number of results
- Retrieved documents have valid metadata
- Empty query handling
- Context formatting
- Score-based retrieval

Note: These tests create a small in-memory FAISS index for testing.
They do NOT require an API key or external services.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from langchain_core.documents import Document
from app.embeddings.embedder import get_embeddings
from app.retrieval.retriever import retrieve_documents, retrieve_with_scores, format_context

# We build a small FAISS index in a fixture so tests are self-contained.
from langchain_community.vectorstores import FAISS


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sample_vector_store():
    """Create a small FAISS vector store for testing.

    Uses the real embedding model (all-MiniLM-L6-v2) but with only
    a few documents, so it's fast.
    """
    docs = [
        Document(
            page_content="The termination clause allows either party to end the agreement with 30 days notice.",
            metadata={"source": "nda.txt", "page": 1, "chunk_id": 0},
        ),
        Document(
            page_content="Monthly rent is INR 35,000 payable by the 5th of each month via bank transfer.",
            metadata={"source": "rental.txt", "page": 1, "chunk_id": 1},
        ),
        Document(
            page_content="All confidential information must be kept secret for five years after termination.",
            metadata={"source": "nda.txt", "page": 2, "chunk_id": 2},
        ),
        Document(
            page_content="Disputes shall be resolved through arbitration in Bangalore under Indian law.",
            metadata={"source": "service.txt", "page": 3, "chunk_id": 3},
        ),
        Document(
            page_content="The security deposit of INR 1,75,000 shall be refunded within 30 days of vacating.",
            metadata={"source": "rental.txt", "page": 2, "chunk_id": 4},
        ),
    ]

    embeddings = get_embeddings()
    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store


# ── Tests ─────────────────────────────────────────────────────


class TestRetrieveDocuments:
    """Tests for the retrieve_documents function."""

    def test_returns_correct_number(self, sample_vector_store):
        """Should return exactly top_k documents."""
        results = retrieve_documents(sample_vector_store, "termination clause", top_k=3)
        assert len(results) == 3

    def test_returns_fewer_if_not_enough(self, sample_vector_store):
        """Should return all docs if top_k > total docs."""
        results = retrieve_documents(sample_vector_store, "test query", top_k=10)
        assert len(results) == 5  # Only 5 docs in our test store

    def test_results_have_metadata(self, sample_vector_store):
        """Each retrieved document should have source and chunk_id metadata."""
        results = retrieve_documents(sample_vector_store, "rent payment", top_k=2)

        for doc in results:
            assert "source" in doc.metadata
            assert "chunk_id" in doc.metadata

    def test_relevant_results_first(self, sample_vector_store):
        """The most relevant result should relate to the query topic."""
        results = retrieve_documents(sample_vector_store, "monthly rent payment amount", top_k=1)

        # The top result should be about rent (from rental.txt).
        assert "rent" in results[0].page_content.lower() or \
               "INR" in results[0].page_content

    def test_empty_query_returns_empty(self, sample_vector_store):
        """Empty query should return an empty list."""
        results = retrieve_documents(sample_vector_store, "", top_k=3)
        assert results == []

    def test_whitespace_query_returns_empty(self, sample_vector_store):
        """Whitespace-only query should return an empty list."""
        results = retrieve_documents(sample_vector_store, "   ", top_k=3)
        assert results == []


class TestRetrieveWithScores:
    """Tests for the retrieve_with_scores function."""

    def test_returns_tuples(self, sample_vector_store):
        """Should return (Document, float) tuples."""
        results = retrieve_with_scores(sample_vector_store, "arbitration", top_k=2)

        assert len(results) == 2
        for doc, score in results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)

    def test_scores_are_non_negative(self, sample_vector_store):
        """Similarity scores should be non-negative."""
        results = retrieve_with_scores(sample_vector_store, "confidentiality", top_k=3)

        for _, score in results:
            assert score >= 0


class TestFormatContext:
    """Tests for the format_context function."""

    def test_formats_with_headers(self, sample_vector_store):
        """Formatted context should include source and chunk headers."""
        docs = retrieve_documents(sample_vector_store, "rent", top_k=2)
        context = format_context(docs)

        assert "[Source:" in context
        assert "Chunk:" in context
        assert "---" in context  # Separator between chunks

    def test_empty_docs_message(self):
        """Empty docs should return a 'no context' message."""
        context = format_context([])
        assert "no relevant context" in context.lower()
