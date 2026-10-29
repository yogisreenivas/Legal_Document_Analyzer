"""
preprocessor.py - Text preprocessing for legal documents.

Cleans extracted text by normalizing whitespace, removing artifacts,
and standardizing formatting. Keeps the text readable and consistent
for better chunking and embedding quality.
"""

import re
from typing import List

from langchain_core.documents import Document

from app.utils.logger import get_logger

logger = get_logger(__name__)


def preprocess_text(text: str) -> str:
    """Clean and normalize a single text string.

    Steps:
    1. Replace multiple whitespace characters with a single space.
    2. Normalize line breaks (collapse multiple blank lines into one).
    3. Remove common PDF extraction artifacts.
    4. Strip leading/trailing whitespace.

    Args:
        text: Raw extracted text from a document.

    Returns:
        Cleaned text string.
    """
    if not text or not text.strip():
        return ""

    # Replace tabs and multiple spaces with a single space (within lines).
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize line breaks: collapse 3+ newlines into 2 (preserving paragraphs).
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove common PDF artifacts like page numbers standalone on a line.
    # Pattern: a line that contains only a number (likely a page number).
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # Remove excessive dashes/underscores used as separators.
    text = re.sub(r"[-_]{5,}", "---", text)

    # Strip leading/trailing whitespace from each line.
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Final strip.
    text = text.strip()

    return text


def preprocess_documents(documents: List[Document]) -> List[Document]:
    """Apply preprocessing to a list of LangChain Document objects.

    This modifies the page_content of each Document in-place and returns
    the same list (filtering out any documents that become empty after
    preprocessing).

    Args:
        documents: List of Document objects from the loader.

    Returns:
        List of Document objects with cleaned text. Empty documents
        are removed.
    """
    logger.info(f"Preprocessing {len(documents)} document section(s)")

    cleaned_docs: List[Document] = []
    removed_count = 0

    for doc in documents:
        cleaned_text = preprocess_text(doc.page_content)

        if cleaned_text:
            # Create a new Document with cleaned text (preserving metadata).
            cleaned_doc = Document(
                page_content=cleaned_text,
                metadata=doc.metadata.copy(),
            )
            cleaned_docs.append(cleaned_doc)
        else:
            # Document became empty after cleaning (e.g., was only page numbers).
            removed_count += 1
            logger.debug(
                f"Removed empty document section from "
                f"{doc.metadata.get('source', 'unknown')}"
            )

    if removed_count > 0:
        logger.info(f"Removed {removed_count} empty section(s) after preprocessing")

    logger.info(f"Preprocessing complete: {len(cleaned_docs)} section(s) remaining")
    return cleaned_docs
