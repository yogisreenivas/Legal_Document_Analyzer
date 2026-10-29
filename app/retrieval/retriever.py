"""
retriever.py - Semantic retrieval from the FAISS vector store.

Takes a user query, embeds it, and retrieves the top-k most similar
document chunks from the FAISS index. The retrieved chunks serve as
context for the LLM to generate grounded answers.
"""

from typing import List, Tuple

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.config import RETRIEVAL_TOP_K
from app.utils.logger import get_logger

logger = get_logger(__name__)


def retrieve_documents(
    vector_store: FAISS,
    query: str,
    top_k: int = None,
) -> List[Document]:
    """Retrieve the most relevant document chunks for a query.

    Uses FAISS similarity search to find chunks whose embeddings
    are closest to the query embedding (cosine similarity).

    Args:
        vector_store: The FAISS vector store containing indexed chunks.
        query: The user's question or search query.
        top_k: Number of chunks to retrieve. Default from config.

    Returns:
        List of Document objects sorted by relevance (most relevant first).
    """
    if top_k is None:
        top_k = RETRIEVAL_TOP_K

    if not query or not query.strip():
        logger.warning("Empty query provided to retriever")
        return []

    logger.info(f"Retrieving top-{top_k} chunks for query: '{query[:80]}...'")

    # similarity_search returns documents sorted by similarity (best first).
    results = vector_store.similarity_search(
        query=query,
        k=top_k,
    )

    logger.info(f"Retrieved {len(results)} chunks")

    # Log the sources of retrieved chunks for debugging.
    sources = [doc.metadata.get("source", "unknown") for doc in results]
    logger.debug(f"Retrieved from sources: {sources}")

    return results


def retrieve_with_scores(
    vector_store: FAISS,
    query: str,
    top_k: int = None,
) -> List[Tuple[Document, float]]:
    """Retrieve document chunks with their similarity scores.

    Similar to retrieve_documents but also returns the distance score.
    Lower scores = more similar (FAISS uses L2 distance by default,
    but with normalized embeddings this approximates cosine distance).

    Args:
        vector_store: The FAISS vector store.
        query: The user's query.
        top_k: Number of chunks to retrieve.

    Returns:
        List of (Document, score) tuples sorted by relevance.
    """
    if top_k is None:
        top_k = RETRIEVAL_TOP_K

    if not query or not query.strip():
        logger.warning("Empty query provided to retriever")
        return []

    logger.info(f"Retrieving top-{top_k} chunks with scores for: '{query[:80]}...'")

    results = [
        (doc, float(score))
        for doc, score in vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
        )
    ]

    logger.info(f"Retrieved {len(results)} chunks with scores")

    # Log scores for debugging.
    for doc, score in results:
        logger.debug(
            f"  Score: {score:.4f} | "
            f"Source: {doc.metadata.get('source', 'unknown')} | "
            f"Chunk: {doc.metadata.get('chunk_id', 'N/A')}"
        )

    return results


def format_context(documents: List[Document]) -> str:
    """Format retrieved documents into a single context string for the LLM.

    Each chunk is labeled with its source and chunk_id so the LLM
    can reference specific chunks in its citations.

    Args:
        documents: List of retrieved Document objects.

    Returns:
        A formatted string containing all chunks with labels.
    """
    if not documents:
        return "No relevant context found."

    context_parts = []
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "N/A")
        page = doc.metadata.get("page", "N/A")

        header = f"[Source: {source} | Page: {page} | Chunk: {chunk_id}]"
        context_parts.append(f"{header}\n{doc.page_content}")

    return "\n\n---\n\n".join(context_parts)
