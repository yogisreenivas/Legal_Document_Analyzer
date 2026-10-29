"""
nodes.py - LangGraph node functions.

Each function is a "node" in the LangGraph StateGraph. Nodes take the
current state as input, perform an operation, and return updated state
fields. The workflow orchestrator (workflow.py) connects these nodes
with edges and conditional routing.

Nodes:
- classify_query: Determine the task type from the user's query.
- retrieve: Fetch relevant document chunks from the vector store.
- generate: Generate an answer using the LLM with task-specific prompts.
- verify_grounding: Check if the answer is supported by the context.
- rewrite_query: Rewrite the query for a retry attempt.
- fallback: Return a "not found" response when grounding fails.
"""

from typing import Any, Dict

from langchain_community.vectorstores import FAISS

from app.retrieval.retriever import retrieve_documents, format_context
from app.llm.llm_factory import get_llm
from app.llm.prompts import (
    get_prompt_for_task,
    GROUNDING_CHECK_TEMPLATE,
    QUERY_REWRITE_TEMPLATE,
)
from app.config import DISCLAIMER
from app.utils.logger import get_logger

logger = get_logger(__name__)

# The vector store is set at runtime before running the graph.
# This module-level variable is set by workflow.py's run function.
_vector_store: FAISS = None


def set_vector_store(vs: FAISS) -> None:
    """Set the FAISS vector store for the retrieval node.

    Called by the workflow runner before invoking the graph.

    Args:
        vs: A FAISS vector store instance with indexed documents.
    """
    global _vector_store
    _vector_store = vs


def classify_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Classify the user's query into a task type.

    Uses keyword matching for reliability. An LLM-based classifier
    could be more flexible but is slower and less predictable.

    Task types:
    - summarize: User wants a summary of the document
    - key_clauses: User wants to identify key clauses
    - extract_obligations: User wants structured extraction
    - qa: Default for all other questions

    Args:
        state: Current graph state with 'query'.

    Returns:
        Updated state with 'task_type' set.
    """
    query = state["query"].lower().strip()
    logger.info(f"Classifying query: '{query[:80]}...'")

    # Keyword-based classification for predictability.
    if any(kw in query for kw in ["summarize", "summary", "summarise", "overview", "brief"]):
        task_type = "summarize"
    elif any(kw in query for kw in [
        "key clause", "key clauses", "important clause", "important clauses",
        "identify clause", "list clause", "find clause",
        "termination", "confidentiality", "liability", "indemnity",
        "governing law", "dispute resolution", "renewal", "intellectual property"
    ]):
        task_type = "key_clauses"
    elif any(kw in query for kw in [
        "extract", "obligation", "obligations", "condition", "conditions",
        "deadline", "deadlines", "penalty", "penalties", "parties",
        "structured", "json"
    ]):
        task_type = "extract_obligations"
    else:
        # Default: treat as a question-answering task.
        task_type = "qa"

    logger.info(f"Query classified as: {task_type}")
    return {"task_type": task_type}


def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve relevant document chunks from the vector store.

    Uses the query (or rewritten query on retry) to perform
    semantic similarity search.

    Args:
        state: Current graph state with 'query' and optionally 'rewritten_query'.

    Returns:
        Updated state with 'retrieved_docs' and 'context'.
    """
    # On retry, use the rewritten query instead of the original.
    search_query = state.get("rewritten_query") or state["query"]
    logger.info(f"Retrieving documents for: '{search_query[:80]}...'")

    if _vector_store is None:
        logger.error("Vector store not initialized!")
        return {
            "retrieved_docs": [],
            "context": "No documents indexed. Please upload a document first.",
            "error": "Vector store not initialized",
        }

    try:
        docs = retrieve_documents(_vector_store, search_query)
        context = format_context(docs)

        logger.info(f"Retrieved {len(docs)} chunks")
        return {
            "retrieved_docs": docs,
            "context": context,
        }
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return {
            "retrieved_docs": [],
            "context": "Retrieval failed.",
            "error": str(e),
        }


def generate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an answer using the LLM with task-specific prompts.

    Selects the appropriate prompt template based on task_type,
    fills it with the context (and query for QA), and calls the LLM.

    Args:
        state: Current graph state with 'task_type', 'context', and 'query'.

    Returns:
        Updated state with 'answer' and 'citations'.
    """
    task_type = state["task_type"]
    context = state.get("context", "No context available.")
    query = state["query"]

    logger.info(f"Generating response for task: {task_type}")

    try:
        llm = get_llm()
        prompt = get_prompt_for_task(task_type)

        # Build the prompt input variables.
        prompt_inputs = {"context": context}
        if task_type == "qa":
            prompt_inputs["query"] = query

        # Create the chain: prompt → LLM → string output.
        chain = prompt | llm

        # Invoke the chain.
        response = chain.invoke(prompt_inputs)

        # Extract the text content from the response.
        answer = response.content if hasattr(response, "content") else str(response)

        # Extract citations from retrieved docs metadata.
        citations = _extract_citations(state.get("retrieved_docs", []))

        logger.info(f"Generated response ({len(answer)} chars)")
        return {
            "answer": answer,
            "citations": citations,
        }

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return {
            "answer": f"Error generating response: {str(e)}",
            "citations": [],
            "error": str(e),
        }


def verify_grounding(state: Dict[str, Any]) -> Dict[str, Any]:
    """Verify that the generated answer is grounded in the context.

    Uses two approaches:
    1. Quick overlap check: Does the answer contain keywords from the context?
    2. LLM-as-judge: Ask the LLM to verify groundedness (more reliable).

    Args:
        state: Current graph state with 'answer' and 'context'.

    Returns:
        Updated state with 'grounded' (bool) and 'groundedness_explanation'.
    """
    answer = state.get("answer", "")
    context = state.get("context", "")

    logger.info("Verifying answer groundedness")

    # Check for explicit "not found" responses (already grounded by definition).
    if "not found in the document" in answer.lower():
        return {
            "grounded": True,
            "groundedness_explanation": "Answer explicitly states information was not found.",
        }

    # Quick overlap check: see if key terms from the answer appear in context.
    # This is a fast heuristic before calling the LLM.
    overlap_score = _compute_overlap(answer, context)
    logger.debug(f"Overlap score: {overlap_score:.2f}")

    if overlap_score < 0.1:
        # Very low overlap → likely not grounded, skip LLM check.
        return {
            "grounded": False,
            "groundedness_explanation": f"Low text overlap ({overlap_score:.2f}). Answer may not be supported by context.",
        }

    # LLM-as-judge: ask the LLM to verify groundedness.
    try:
        llm = get_llm()
        chain = GROUNDING_CHECK_TEMPLATE | llm
        result = chain.invoke({"context": context, "answer": answer})
        verdict = result.content if hasattr(result, "content") else str(result)

        grounded = "GROUNDED" in verdict.upper() and "NOT_GROUNDED" not in verdict.upper()

        logger.info(f"Groundedness check: {'GROUNDED' if grounded else 'NOT GROUNDED'}")
        return {
            "grounded": grounded,
            "groundedness_explanation": verdict.strip(),
        }

    except Exception as e:
        # If the LLM check fails, fall back to the overlap heuristic.
        logger.warning(f"LLM grounding check failed: {e}. Using overlap heuristic.")
        grounded = overlap_score > 0.2
        return {
            "grounded": grounded,
            "groundedness_explanation": f"Fallback check (overlap: {overlap_score:.2f}). LLM check failed: {e}",
        }


def rewrite_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Rewrite the query for a retry attempt.

    When the first answer isn't grounded, we try to improve retrieval
    by rewriting the query to be more specific or use different terms.

    Args:
        state: Current graph state with 'query'.

    Returns:
        Updated state with 'rewritten_query' and incremented 'retry_count'.
    """
    query = state["query"]
    retry_count = state.get("retry_count", 0)

    logger.info(f"Rewriting query (retry #{retry_count + 1}): '{query[:80]}...'")

    try:
        llm = get_llm()
        chain = QUERY_REWRITE_TEMPLATE | llm
        result = chain.invoke({"query": query})
        rewritten = result.content if hasattr(result, "content") else str(result)
        rewritten = rewritten.strip()

        logger.info(f"Rewritten query: '{rewritten[:80]}...'")
        return {
            "rewritten_query": rewritten,
            "retry_count": retry_count + 1,
        }

    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}. Using original query.")
        return {
            "rewritten_query": query,
            "retry_count": retry_count + 1,
        }


def fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return a fallback response when the answer is not grounded.

    This node is reached when the grounding check fails even after
    a retry attempt.

    Args:
        state: Current graph state.

    Returns:
        Updated state with a safe fallback answer.
    """
    logger.info("Returning fallback response (answer not grounded)")

    return {
        "answer": (
            "Not found in the document. The information requested could not "
            "be reliably located in the uploaded document(s). Please try "
            "rephrasing your question or ensure the relevant document has "
            "been uploaded.\n\n"
            f"{DISCLAIMER}"
        ),
        "grounded": False,
        "groundedness_explanation": "Answer could not be grounded after retry.",
    }


# ── Helper Functions ──────────────────────────────────────────

def _extract_citations(docs: list) -> list:
    """Extract citation strings from retrieved document metadata.

    Args:
        docs: List of retrieved Document objects.

    Returns:
        List of formatted citation strings.
    """
    citations = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "N/A")
        chunk_id = doc.metadata.get("chunk_id", "N/A")
        citations.append(f"[Source: {source}, Page: {page}, Chunk: {chunk_id}]")
    return citations


def _compute_overlap(answer: str, context: str) -> float:
    """Compute a simple word-level overlap score between answer and context.

    This is a quick heuristic to detect obviously ungrounded answers
    before calling the more expensive LLM-as-judge.

    Args:
        answer: The generated answer text.
        context: The retrieved context text.

    Returns:
        Float between 0 and 1 (fraction of answer words found in context).
    """
    if not answer or not context:
        return 0.0

    # Lowercase and split into words.
    answer_words = set(answer.lower().split())
    context_words = set(context.lower().split())

    # Remove common stop words to focus on meaningful terms.
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "can", "could", "of", "in", "to", "for",
        "with", "on", "at", "from", "by", "as", "or", "and", "not", "no",
        "it", "its", "this", "that", "these", "those", "their", "they",
    }

    answer_meaningful = answer_words - stop_words
    if not answer_meaningful:
        return 1.0  # No meaningful words → trivially grounded.

    overlap = answer_meaningful & context_words
    return len(overlap) / len(answer_meaningful)
