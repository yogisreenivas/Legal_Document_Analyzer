"""
state.py - LangGraph workflow state definition.

Defines the typed state that flows through the LangGraph StateGraph.
Every node reads from and writes to this shared state object.
Using TypedDict gives us type safety and clear documentation of
what data is available at each step.
"""

from typing import List, Optional
from typing_extensions import TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict):
    """State that flows through the LangGraph workflow.

    Attributes:
        query: The user's original question or request.
        task_type: Classified task type (summarize, qa, key_clauses, extract_obligations).
        retrieved_docs: List of Document chunks retrieved from the vector store.
        context: Formatted context string for the LLM prompt.
        answer: The LLM's generated response.
        citations: List of citation strings referencing source chunks.
        grounded: Whether the answer is verified as grounded in the context.
        groundedness_explanation: Explanation from the grounding check.
        retry_count: Number of retrieval retries attempted (max 1).
        rewritten_query: Rewritten query for retry attempts.
        error: Error message if something went wrong.
    """

    query: str
    task_type: str
    retrieved_docs: Optional[List[Document]]
    context: Optional[str]
    answer: Optional[str]
    citations: Optional[List[str]]
    grounded: Optional[bool]
    groundedness_explanation: Optional[str]
    retry_count: int
    rewritten_query: Optional[str]
    error: Optional[str]
