"""
test_graph_routing.py - Unit tests for LangGraph query classification and routing.

Tests cover:
- Query classification into correct task types
- Routing logic after grounding verification
- Edge cases: ambiguous queries, mixed keywords
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.graph.nodes import classify_query
from app.graph.workflow import _route_after_grounding


# ── Tests for Query Classification ────────────────────────────


class TestClassifyQuery:
    """Tests for the classify_query node function."""

    def test_summarize_classification(self):
        """Queries asking for summaries should be classified as 'summarize'."""
        test_cases = [
            "Summarize this document",
            "Give me a summary of the agreement",
            "Provide an overview of the contract",
            "Give a brief of this document",
        ]
        for query in test_cases:
            state = {"query": query}
            result = classify_query(state)
            assert result["task_type"] == "summarize", (
                f"Query '{query}' should be 'summarize', got '{result['task_type']}'"
            )

    def test_key_clauses_classification(self):
        """Queries about key clauses should be classified as 'key_clauses'."""
        test_cases = [
            "Identify the key clauses in this document",
            "What are the important clauses?",
            "Find the termination clause",
            "What does the confidentiality section say?",
            "What is the liability cap?",
            "Explain the dispute resolution mechanism",
        ]
        for query in test_cases:
            state = {"query": query}
            result = classify_query(state)
            assert result["task_type"] == "key_clauses", (
                f"Query '{query}' should be 'key_clauses', got '{result['task_type']}'"
            )

    def test_extract_obligations_classification(self):
        """Queries about extraction should be classified as 'extract_obligations'."""
        test_cases = [
            "Extract all obligations from this document",
            "What are the conditions in this agreement?",
            "List all deadlines",
            "What penalties are mentioned?",
            "Who are the parties in this agreement?",
            "Give me the structured data as JSON",
        ]
        for query in test_cases:
            state = {"query": query}
            result = classify_query(state)
            assert result["task_type"] == "extract_obligations", (
                f"Query '{query}' should be 'extract_obligations', got '{result['task_type']}'"
            )

    def test_qa_default_classification(self):
        """General questions should default to 'qa'."""
        test_cases = [
            "How much is the monthly rent?",
            "When does this agreement expire?",
            "Can the tenant sublet the property?",
            "What is the address of the property?",
        ]
        for query in test_cases:
            state = {"query": query}
            result = classify_query(state)
            assert result["task_type"] == "qa", (
                f"Query '{query}' should be 'qa', got '{result['task_type']}'"
            )

    def test_case_insensitive(self):
        """Classification should be case-insensitive."""
        state = {"query": "SUMMARIZE THIS DOCUMENT"}
        result = classify_query(state)
        assert result["task_type"] == "summarize"


# ── Tests for Routing Logic ───────────────────────────────────


class TestRouteAfterGrounding:
    """Tests for the _route_after_grounding routing function."""

    def test_grounded_goes_to_end(self):
        """Grounded answer should route to 'end'."""
        state = {"grounded": True, "retry_count": 0}
        assert _route_after_grounding(state) == "end"

    def test_not_grounded_first_attempt_goes_to_retry(self):
        """First non-grounded attempt should route to 'retry'."""
        state = {"grounded": False, "retry_count": 0}
        assert _route_after_grounding(state) == "retry"

    def test_not_grounded_after_retry_goes_to_fallback(self):
        """Non-grounded after retry should route to 'fallback'."""
        state = {"grounded": False, "retry_count": 1}
        assert _route_after_grounding(state) == "fallback"

    def test_not_grounded_multiple_retries_goes_to_fallback(self):
        """Multiple retries should always go to fallback."""
        state = {"grounded": False, "retry_count": 5}
        assert _route_after_grounding(state) == "fallback"

    def test_grounded_after_retry_goes_to_end(self):
        """Grounded on retry should still route to 'end'."""
        state = {"grounded": True, "retry_count": 1}
        assert _route_after_grounding(state) == "end"
