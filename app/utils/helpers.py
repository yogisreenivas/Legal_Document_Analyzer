"""
helpers.py - Miscellaneous utility functions.

Small, reusable functions that don't belong to any specific module.
"""

from pathlib import Path
from typing import List


def get_file_extension(file_path: str) -> str:
    """Return the lowercase file extension without the leading dot.

    Args:
        file_path: Path to the file.

    Returns:
        Extension string, e.g. 'pdf', 'docx', 'txt'.
    """
    return Path(file_path).suffix.lower().lstrip(".")


def validate_file_type(file_path: str, allowed: List[str] = None) -> bool:
    """Check whether a file has an allowed extension.

    Args:
        file_path: Path to the file.
        allowed: List of allowed extensions (default: pdf, docx, txt).

    Returns:
        True if the file extension is in the allowed list.
    """
    if allowed is None:
        allowed = ["pdf", "docx", "txt"]
    return get_file_extension(file_path) in allowed


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length, adding ellipsis if needed.

    Args:
        text: The input text.
        max_length: Maximum character count.

    Returns:
        Truncated text with '...' appended if it was shortened.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_citation(source: str, page: int = None, chunk_id: int = None) -> str:
    """Format a citation string from document metadata.

    Args:
        source: Source document filename.
        page: Page number (if available).
        chunk_id: Chunk identifier (if available).

    Returns:
        A formatted citation string like '[Source: nda.pdf, Page 2, Chunk 5]'.
    """
    parts = [f"Source: {source}"]
    if page is not None:
        parts.append(f"Page {page}")
    if chunk_id is not None:
        parts.append(f"Chunk {chunk_id}")
    return "[" + ", ".join(parts) + "]"
