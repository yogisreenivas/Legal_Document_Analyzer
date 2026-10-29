"""
workflow.py - LangGraph StateGraph assembly and execution.

Assembles the complete RAG workflow as a LangGraph StateGraph:

    classify_query → retrieve → generate → verify_grounding
                                                  ↓
                                        grounded? → YES → END
                                                  → NO  → rewrite_query → retrieve → generate → verify_grounding
                                                                                                      ↓
                                                                                            grounded? → YES → END
                                                                                                      → NO  → fallback → END

Conditional edges handle routing based on groundedness and retry count.
"""

from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langchain_community.vectorstores import FAISS

from app.graph.state import GraphState
from app.graph.nodes import (
    classify_query,
    retrieve,
    generate,
    verify_grounding,
    rewrite_query,
    fallback,
    set_vector_store,
)
from app.config import DISCLAIMER
from app.utils.logger import get_logger

logger = get_logger(__name__)


def build_graph() -> StateGraph:
    """Build and compile the LangGraph workflow.

    The graph has the following flow:
    1. classify_query: Determine the task type
    2. retrieve: Fetch relevant chunks from the vector store
    3. generate: Generate an answer using the LLM
    4. verify_grounding: Check if the answer is grounded
    5. If grounded → END
    6. If not grounded and retry_count < 1 → rewrite_query → retrieve (retry)
    7. If not grounded and retry_count >= 1 → fallback → END

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    logger.info("Building LangGraph workflow")

    # Create the graph with our typed state.
    workflow = StateGraph(GraphState)

    # ── Add Nodes ─────────────────────────────────────────────
    workflow.add_node("classify_query", classify_query)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.add_node("verify_grounding", verify_grounding)
    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("fallback", fallback)

    # ── Add Edges ─────────────────────────────────────────────

    # Start → classify_query
    workflow.set_entry_point("classify_query")

    # classify_query → retrieve (always)
    workflow.add_edge("classify_query", "retrieve")

    # retrieve → generate (always)
    workflow.add_edge("retrieve", "generate")

    # generate → verify_grounding (always)
    workflow.add_edge("generate", "verify_grounding")

    # verify_grounding → conditional routing based on groundedness
    workflow.add_conditional_edges(
        "verify_grounding",
        _route_after_grounding,
        {
            "end": END,            # Answer is grounded → done
            "retry": "rewrite_query",  # Not grounded, first attempt → retry
            "fallback": "fallback",    # Not grounded after retry → fallback
        },
    )

    # rewrite_query → retrieve (retry with rewritten query)
    workflow.add_edge("rewrite_query", "retrieve")

    # fallback → END
    workflow.add_edge("fallback", END)

    # Compile the graph.
    compiled = workflow.compile()
    logger.info("LangGraph workflow compiled successfully")

    return compiled


def _route_after_grounding(state: Dict[str, Any]) -> str:
    """Routing function for the conditional edge after verify_grounding.

    Decision logic:
    - If the answer is grounded → "end" (go to END)
    - If not grounded and retry_count < 1 → "retry" (rewrite and re-retrieve)
    - If not grounded and retry_count >= 1 → "fallback" (give up)

    Args:
        state: Current graph state.

    Returns:
        One of: "end", "retry", "fallback"
    """
    grounded = state.get("grounded", False)
    retry_count = state.get("retry_count", 0)

    if grounded:
        logger.info("Answer is grounded → ending workflow")
        return "end"
    elif retry_count < 1:
        logger.info(f"Answer not grounded (retry {retry_count}/1) → retrying")
        return "retry"
    else:
        logger.info(f"Answer not grounded after {retry_count} retries → fallback")
        return "fallback"


def run_workflow(
    query: str,
    vector_store: FAISS,
    task_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the complete RAG workflow for a given query.

    This is the main entry point for the RAG pipeline. It:
    1. Sets up the vector store for the retrieval node
    2. Builds and compiles the graph
    3. Invokes the graph with the initial state
    4. Returns the final state with the answer and metadata

    Args:
        query: The user's question or request.
        vector_store: FAISS vector store with indexed documents.
        task_type: Optional override for task classification.
                   If None, the classifier node determines it.

    Returns:
        Final graph state dictionary with answer, citations,
        groundedness info, and disclaimer.
    """
    logger.info(f"Running workflow for query: '{query[:80]}...'")

    # Set the vector store for the retrieval node.
    set_vector_store(vector_store)

    # Build the graph.
    graph = build_graph()

    # Prepare the initial state.
    initial_state: GraphState = {
        "query": query,
        "task_type": task_type or "",  # Empty = let classifier decide
        "retrieved_docs": None,
        "context": None,
        "answer": None,
        "citations": None,
        "grounded": None,
        "groundedness_explanation": None,
        "retry_count": 0,
        "rewritten_query": None,
        "error": None,
    }

    # If a task_type override is provided, skip the classifier.
    # We do this by setting it before the graph runs.
    # The classify_query node will still run but its result
    # won't change anything since we set it in initial state.

    try:
        # Run the graph.
        final_state = graph.invoke(initial_state)

        # Add disclaimer to the final state.
        if final_state.get("answer") and DISCLAIMER not in final_state["answer"]:
            final_state["answer"] += f"\n\n{DISCLAIMER}"

        logger.info("Workflow completed successfully")
        return final_state

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return {
            **initial_state,
            "answer": f"An error occurred during analysis: {str(e)}\n\n{DISCLAIMER}",
            "grounded": False,
            "error": str(e),
        }


def export_graph_mermaid() -> str:
    """Export the graph structure as a Mermaid diagram.

    Returns:
        Mermaid diagram string for documentation.
    """
    graph = build_graph()

    try:
        mermaid = graph.get_graph().draw_mermaid()
        return mermaid
    except Exception as e:
        logger.warning(f"Could not generate Mermaid diagram: {e}")
        # Return a manually created diagram as fallback.
        return """graph TD
    __start__ --> classify_query
    classify_query --> retrieve
    retrieve --> generate
    generate --> verify_grounding
    verify_grounding -->|grounded| __end__
    verify_grounding -->|not grounded, retry < 1| rewrite_query
    verify_grounding -->|not grounded, retry >= 1| fallback
    rewrite_query --> retrieve
    fallback --> __end__"""
