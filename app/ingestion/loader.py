"""
loader.py - Document loading module.

Loads PDF, DOCX, and TXT files using LangChain's document loaders.
Each loader returns a list of LangChain Document objects with content
and metadata (source filename, page number where applicable).
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)

from app.utils.logger import get_logger
from app.utils.helpers import get_file_extension, validate_file_type

logger = get_logger(__name__)


def load_document(file_path: str) -> List[Document]:
    """Load a single document and return LangChain Document objects.

    Supported formats: PDF, DOCX, TXT.
    Each Document contains the extracted text (page_content) and metadata
    including the source filename and page number (for PDFs).

    Args:
        file_path: Absolute or relative path to the document file.

    Returns:
        A list of Document objects (one per page for PDFs, one for TXT/DOCX).

    Raises:
        ValueError: If the file type is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file type is supported
    if not validate_file_type(file_path):
        raise ValueError(
            f"Unsupported file type: '{get_file_extension(file_path)}'. "
            f"Supported types: pdf, docx, txt"
        )

    extension = get_file_extension(file_path)
    logger.info(f"Loading {extension.upper()} file: {path.name}")

    try:
        if extension == "pdf":
            docs = _load_pdf(str(path))
        elif extension == "docx":
            docs = _load_docx(str(path))
        elif extension == "txt":
            docs = _load_txt(str(path))
        else:
            raise ValueError(f"Unsupported file type: {extension}")

        # Add the source filename to metadata for all documents.
        for doc in docs:
            doc.metadata["source"] = path.name

        # Warn if no text was extracted (e.g., scanned PDF without OCR).
        total_text = sum(len(doc.page_content.strip()) for doc in docs)
        if total_text == 0:
            logger.warning(
                f"No text extracted from {path.name}. "
                f"The file may be a scanned image or empty."
            )

        logger.info(f"Loaded {len(docs)} document section(s) from {path.name}")
        return docs

    except Exception as e:
        logger.error(f"Failed to load {path.name}: {e}")
        raise


def _load_pdf(file_path: str) -> List[Document]:
    """Load a PDF file using PyPDFLoader.

    Returns one Document per page with page numbers in metadata.
    """
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # PyPDFLoader adds 'page' to metadata (0-indexed). Convert to 1-indexed.
    for doc in docs:
        if "page" in doc.metadata:
            doc.metadata["page"] = doc.metadata["page"] + 1

    return docs


def _load_docx(file_path: str) -> List[Document]:
    """Load a DOCX file using python-docx directly.

    We use python-docx instead of a LangChain loader for better control.
    Returns a single Document with all text content.
    """
    try:
        import docx
    except ImportError:
        raise ImportError(
            "python-docx is required for DOCX files. "
            "Install it with: pip install python-docx"
        )

    doc = docx.Document(file_path)
    # Extract text from all paragraphs, preserving paragraph breaks.
    full_text = "\n".join(
        paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()
    )

    return [
        Document(
            page_content=full_text,
            metadata={"page": 1},  # DOCX doesn't have page numbers
        )
    ]


def _load_txt(file_path: str) -> List[Document]:
    """Load a plain text file using LangChain's TextLoader.

    Returns a single Document with all text content.
    """
    loader = TextLoader(file_path, encoding="utf-8")
    docs = loader.load()

    # Add page metadata (TXT files are treated as a single page).
    for doc in docs:
        doc.metadata["page"] = 1

    return docs


def load_multiple_documents(file_paths: List[str]) -> List[Document]:
    """Load multiple documents and combine them into a single list.

    Args:
        file_paths: List of file paths to load.

    Returns:
        Combined list of Document objects from all files.
    """
    all_docs: List[Document] = []
    for file_path in file_paths:
        try:
            docs = load_document(file_path)
            all_docs.extend(docs)
        except Exception as e:
            # Log the error but continue loading other files.
            logger.error(f"Skipping {file_path}: {e}")

    logger.info(f"Total documents loaded: {len(all_docs)} from {len(file_paths)} file(s)")
    return all_docs
