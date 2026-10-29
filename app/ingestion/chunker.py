"""
chunker.py - Text chunking for RAG pipeline.

Splits preprocessed documents into smaller, overlapping chunks suitable
for embedding and retrieval. Uses LangChain's RecursiveCharacterTextSplitter,
which tries to split at natural boundaries (paragraphs > sentences > words).

Each chunk carries metadata: source filename, page number, and chunk_id.
"""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_chunks(
    documents: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Document]:
    """Split documents into overlapping chunks with metadata.

    Why overlapping chunks?
    - Overlap ensures that sentences at chunk boundaries aren't split
      in the middle, so the retriever can find relevant context even
      if the answer spans two chunks.

    Args:
        documents: List of preprocessed Document objects.
        chunk_size: Maximum characters per chunk (default from config).
        chunk_overlap: Number of overlapping characters between chunks
                       (default from config).

    Returns:
        List of Document objects, each representing a chunk with metadata
        containing: source, page, chunk_id.
    """
    # Use defaults from config if not provided.
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = CHUNK_OVERLAP

    logger.info(
        f"Chunking {len(documents)} document(s) with "
        f"chunk_size={chunk_size}, overlap={chunk_overlap}"
    )

    # RecursiveCharacterTextSplitter tries these separators in order:
    # "\n\n" (paragraph) > "\n" (line) > " " (word) > "" (character)
    # This preserves natural text boundaries as much as possible.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,  # Count characters (not tokens).
        separators=["\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False,
    )

    # Split all documents into chunks.
    chunks = text_splitter.split_documents(documents)

    # Add chunk_id to each chunk's metadata for citation tracking.
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = idx

    logger.info(
        f"Created {len(chunks)} chunks from {len(documents)} document section(s)"
    )

    # Log some statistics for debugging.
    if chunks:
        lengths = [len(c.page_content) for c in chunks]
        logger.debug(
            f"Chunk stats - min: {min(lengths)}, max: {max(lengths)}, "
            f"avg: {sum(lengths) / len(lengths):.0f} characters"
        )

    return chunks


def get_chunk_summary(chunks: List[Document]) -> dict:
    """Return summary statistics about the chunks.

    Useful for displaying in the UI and for evaluation.

    Args:
        chunks: List of chunked Document objects.

    Returns:
        Dictionary with chunk statistics.
    """
    if not chunks:
        return {"total_chunks": 0, "avg_length": 0, "min_length": 0, "max_length": 0}

    lengths = [len(c.page_content) for c in chunks]
    sources = set(c.metadata.get("source", "unknown") for c in chunks)

    return {
        "total_chunks": len(chunks),
        "avg_length": round(sum(lengths) / len(lengths), 1),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "sources": list(sources),
    }
