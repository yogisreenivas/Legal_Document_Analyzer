"""
vector_store.py - FAISS vector store management.

FAISS (Facebook AI Similarity Search) stores document chunk embeddings
and enables fast approximate nearest-neighbor search. This module handles:
- Creating a new FAISS index from document chunks
- Saving the index to disk for persistence
- Loading an existing index from disk
- Adding new documents to an existing index
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.config import VECTOR_STORE_PATH
from app.embeddings.embedder import get_embeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_vector_store(
    documents: List[Document],
    save_path: Optional[str] = None,
) -> FAISS:
    """Create a new FAISS vector store from document chunks.

    This embeds all chunks and builds a FAISS index for similarity search.
    The index is optionally saved to disk for later reuse.

    Args:
        documents: List of chunked Document objects to embed and index.
        save_path: Optional path to save the index. Default from config.

    Returns:
        A FAISS vector store instance ready for similarity search.

    Raises:
        ValueError: If the documents list is empty.
    """
    if not documents:
        raise ValueError("Cannot create vector store from empty document list")

    logger.info(f"Creating FAISS vector store from {len(documents)} chunks")

    # Get the embedding model (singleton, loaded once).
    embeddings = get_embeddings()

    # FAISS.from_documents handles:
    # 1. Generating embeddings for all documents
    # 2. Building the FAISS index
    # 3. Storing document content and metadata alongside vectors
    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings,
    )

    logger.info(f"FAISS vector store created with {len(documents)} vectors")

    # Save to disk if a path is provided.
    if save_path is None:
        save_path = str(VECTOR_STORE_PATH)

    save_vector_store(vector_store, save_path)

    return vector_store


def save_vector_store(vector_store: FAISS, save_path: str = None) -> None:
    """Save the FAISS vector store to disk.

    FAISS stores two files: the index (.faiss) and the docstore (.pkl).

    Args:
        vector_store: The FAISS vector store instance.
        save_path: Directory path to save the index files.
    """
    if save_path is None:
        save_path = str(VECTOR_STORE_PATH)

    # Create the directory if it doesn't exist.
    Path(save_path).mkdir(parents=True, exist_ok=True)

    vector_store.save_local(save_path)
    logger.info(f"Vector store saved to: {save_path}")


def load_vector_store(load_path: str = None) -> Optional[FAISS]:
    """Load a previously saved FAISS vector store from disk.

    Args:
        load_path: Directory path containing the saved index files.

    Returns:
        The loaded FAISS vector store, or None if files don't exist.
    """
    if load_path is None:
        load_path = str(VECTOR_STORE_PATH)

    path = Path(load_path)

    # Check if the index files exist.
    if not path.exists() or not (path / "index.faiss").exists():
        logger.warning(f"No vector store found at: {load_path}")
        return None

    logger.info(f"Loading vector store from: {load_path}")
    embeddings = get_embeddings()

    vector_store = FAISS.load_local(
        load_path,
        embeddings,
        allow_dangerous_deserialization=True,  # Required for pickle-based docstore.
    )

    logger.info("Vector store loaded successfully")
    return vector_store


def add_documents_to_store(
    vector_store: FAISS,
    documents: List[Document],
    save_path: str = None,
) -> FAISS:
    """Add new documents to an existing FAISS vector store.

    This is useful when the user uploads additional documents to an
    existing session without rebuilding the entire index.

    Args:
        vector_store: Existing FAISS vector store.
        documents: New chunked documents to add.
        save_path: Path to save the updated index.

    Returns:
        The updated FAISS vector store.
    """
    if not documents:
        logger.warning("No documents to add")
        return vector_store

    logger.info(f"Adding {len(documents)} new chunks to existing vector store")
    vector_store.add_documents(documents)

    # Save the updated index.
    save_vector_store(vector_store, save_path)

    logger.info("Vector store updated and saved")
    return vector_store
