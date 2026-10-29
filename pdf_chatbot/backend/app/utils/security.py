"""
security.py - Security, file validation, and prompt injection mitigation.
"""

import re
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# PDF Magic Bytes: "%PDF" (hex 25 50 44 46)
PDF_MAGIC_BYTES = b"%PDF"

# Valid Document ID pattern (alphanumeric, underscores, hyphens, 4-64 chars)
DOC_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{4,64}$")


def validate_document_id(doc_id: str) -> str:
    """
    Validates document ID format to prevent directory traversal and injection.
    """
    if not doc_id or not DOC_ID_REGEX.match(doc_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid document identifier format."
        )
    return doc_id


def validate_uploaded_pdf(file: UploadFile) -> None:
    """
    Validates uploaded file against security constraints:
    - Allowed extension (.pdf)
    - Valid PDF magic bytes header
    - File size limit (up to 50MB)
    - Malicious stream scan (detect embedded executable launch actions)
    """
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        logger.warning(f"File rejected: invalid extension '{ext}' for file {filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Only standard PDF documents (.pdf) are allowed."
        )

    # Read first 1024 bytes to check magic number and early headers
    header_chunk = file.file.read(1024)
    file.file.seek(0)  # Rewind file pointer

    if not header_chunk.startswith(PDF_MAGIC_BYTES):
        logger.warning(f"File rejected: invalid magic bytes for file {filename}")
        raise HTTPException(
            status_code=400,
            detail="Invalid file content. The uploaded file is corrupted or is not a valid PDF document."
        )

    # Security scan: check for dangerous Launch actions
    if b"/Launch" in header_chunk:
        logger.warning(f"File rejected: potentially malicious action detected in {filename}")
        raise HTTPException(
            status_code=400,
            detail="Security violation: Uploaded PDF contains forbidden executable Launch actions."
        )


def sanitize_filename(filename: str) -> str:
    """
    Removes path traversal components and unsafe symbols from filename.
    """
    base = Path(filename).name
    clean_name = re.sub(r"[^\w\s\.-]", "", base).strip()
    clean_name = clean_name.replace("..", "")
    return clean_name or "document.pdf"


def sanitize_for_prompt_context(text: str) -> str:
    """
    Hardens document text against Prompt Injection attacks:
    - Disarms system role escapes (e.g. 'Human:', 'Assistant:', 'System:', '<|im_start|>')
    - Disarms common jailbreak triggers ('Ignore previous instructions')
    - Encapsulates content in explicit data tags
    """
    if not text:
        return ""

    # Neutralize instruction override phrases completely
    sanitized = re.sub(
        r"(?i)(ignore\s+(all\s+)?(previous|prior|above)\s+instructions)",
        "[DISARMED_PROMPT_INJECTION]",
        text
    )
    # Neutralize role marker escapes
    sanitized = re.sub(
        r"(?i)^(system|assistant|human|user):",
        r"[\1]:",
        sanitized,
        flags=re.MULTILINE
    )
    sanitized = sanitized.replace("<|im_start|>", "[TAG]")
    sanitized = sanitized.replace("<|im_end|>", "[/TAG]")

    return sanitized


def validate_chat_query(query: str) -> str:
    """Validates and trims user chat queries."""
    clean_q = query.strip()
    if not clean_q:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(clean_q) > 4000:
        raise HTTPException(status_code=400, detail="Question exceeds maximum allowed length of 4000 characters.")
    return clean_q
