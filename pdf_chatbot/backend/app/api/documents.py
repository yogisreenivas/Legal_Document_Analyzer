"""
documents.py - Document endpoints for upload, status tracking, analysis JSON, page rendering,
document library listing, and persistent conversation history.
"""

from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.models.schemas import ProcessingStatus, AnalysisCardData
from app.services.document_service import DocumentService
from app.db.database import DatabaseManager
from app.utils.security import validate_uploaded_pdf, sanitize_filename, validate_document_id
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])
document_service = DocumentService()


class ChatHistoryEntry(BaseModel):
    role: str
    content: str
    citations: List[Dict[str, Any]] = []
    follow_up_suggestions: List[str] = []


@router.get("", response_model=List[Dict[str, Any]])
async def list_recent_documents(limit: int = Query(default=30, ge=1, le=100)):
    """
    Returns list of recently uploaded and analyzed documents for the document library switcher.
    """
    return document_service.list_recent_documents(limit=limit)


@router.post("/upload", response_model=ProcessingStatus)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Accepts PDF upload, validates magic bytes and size, saves to disk,
    registers database entry, and enqueues background processing.
    """
    logger.info(f"Received upload request: {file.filename}")
    validate_uploaded_pdf(file)

    safe_name = sanitize_filename(file.filename or "document.pdf")

    # Save to upload directory with unique prefix
    import uuid
    doc_id = f"{uuid.uuid4().hex[:8]}"
    saved_path = settings.UPLOAD_DIR / f"{doc_id}_{safe_name}"

    try:
        content = await file.read()
        # Enforce size limit (50MB)
        if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB."
            )
        with open(saved_path, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to write uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to persist uploaded document.")

    # Register initial tracking status in DB and cache
    document_service.create_document_entry(doc_id, safe_name, saved_path)

    # Launch background processing
    background_tasks.add_task(
        document_service.process_document_async,
        doc_id,
        saved_path,
        safe_name
    )

    status = document_service.get_status(doc_id)
    return status


@router.get("/{document_id}/status", response_model=ProcessingStatus)
async def get_document_status(document_id: str):
    """Poll processing timeline progress."""
    validate_document_id(document_id)
    status = document_service.get_status(document_id)
    if not status:
        raise HTTPException(status_code=404, detail="Document ID not found.")
    return status


@router.get("/{document_id}/analysis", response_model=AnalysisCardData)
async def get_document_analysis(document_id: str):
    """Fetch validated Stage 1 structured analysis JSON."""
    validate_document_id(document_id)
    analysis = document_service.get_analysis(document_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not ready or document not found.")
    return analysis


@router.get("/{document_id}/file")
async def get_original_pdf(document_id: str):
    """Returns the original PDF file for PDF canvas viewer."""
    validate_document_id(document_id)
    pdf_path = document_service.get_pdf_path(document_id)
    if not pdf_path or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name
    )


@router.get("/{document_id}/pages/{page_number}")
async def get_page_raster(document_id: str, page_number: int):
    """Returns rendered PNG page raster for thumbnail carousel and high-speed previews."""
    validate_document_id(document_id)
    if page_number < 1 or page_number > 2000:
        raise HTTPException(status_code=400, detail="Invalid page number.")
    page_img = document_service.get_page_path(document_id, page_number)
    if not page_img or not page_img.exists():
        raise HTTPException(status_code=404, detail=f"Page {page_number} image not found.")
    return FileResponse(page_img, media_type="image/png")


@router.get("/{document_id}/chat-history")
async def get_chat_history(document_id: str):
    """Returns persistent chat conversation history for the document."""
    validate_document_id(document_id)
    history = document_service.get_chat_history(document_id)
    return {"document_id": document_id, "messages": history}


@router.post("/{document_id}/chat-history")
async def append_chat_message(document_id: str, entry: ChatHistoryEntry):
    """Persists a chat message turn to SQLite."""
    validate_document_id(document_id)
    document_service.save_chat_turn(
        doc_id=document_id,
        role=entry.role,
        content=entry.content,
        citations=entry.citations,
        follow_ups=entry.follow_up_suggestions
    )
    return {"status": "saved"}


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Deletes document files, page rasters, database records, and Chroma vector index."""
    validate_document_id(document_id)
    pdf_path = document_service.get_pdf_path(document_id)
    if pdf_path and pdf_path.exists():
        pdf_path.unlink()

    # Delete page rasters
    pages_dir = settings.PAGES_DIR / document_id
    if pages_dir.exists():
        import shutil
        shutil.rmtree(pages_dir)

    # Delete disk analysis cache
    cache_file = settings.STORAGE_DIR / f"{document_id}_analysis.json"
    if cache_file.exists():
        cache_file.unlink()

    # Delete from SQLite
    DatabaseManager.delete_document(document_id)

    # Delete vector store
    document_service.vector_store.delete_document_index(document_id)

    return {"status": "deleted", "document_id": document_id}
