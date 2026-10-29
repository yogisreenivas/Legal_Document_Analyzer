"""
embedder.py - Embedding generation using sentence-transformers.

Wraps the HuggingFace sentence-transformers model (all-MiniLM-L6-v2)
via LangChain's HuggingFaceEmbeddings. This model:
- Produces 384-dimensional vectors
- Is only ~80 MB in size
- Runs on CPU (no GPU needed)
- Is well-suited for semantic similarity tasks
"""

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import EMBEDDING_MODEL
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level cache to avoid re-loading the model on every call.
_embeddings_instance = None


def get_embeddings(model_name: str = None) -> HuggingFaceEmbeddings:
    """Get the embedding model instance (singleton pattern).

    The model is loaded once and cached for subsequent calls.
    This avoids the overhead of downloading/loading the model
    every time embeddings are needed.

    Args:
        model_name: Name of the sentence-transformers model.
                    Default: all-MiniLM-L6-v2 (from config).

    Returns:
        A HuggingFaceEmbeddings instance ready to embed text.
    """
    global _embeddings_instance

    if model_name is None:
        model_name = EMBEDDING_MODEL

    if _embeddings_instance is None:
        logger.info(f"Loading embedding model: {model_name}")
        logger.info("(First load may take a moment to download the model)")

        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=model_name,
            # model_kwargs: passed to the SentenceTransformer constructor.
            model_kwargs={"device": "cpu"},
            # encode_kwargs: passed to model.encode() when generating embeddings.
            encode_kwargs={
                "normalize_embeddings": True,  # L2 normalize for cosine similarity
            },
        )

        logger.info(f"Embedding model '{model_name}' loaded successfully")
    else:
        logger.debug("Using cached embedding model instance")

    return _embeddings_instance
