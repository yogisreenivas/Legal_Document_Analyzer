"""
document_service.py - Orchestrates document ingestion, status tracking, analysis caching,
and persistent SQLite metadata storage.
"""

from typing import Dict, Optional, Tuple, List, Any
from pathlib import Path
import uuid
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.models.schemas import ProcessingStatus, AnalysisCardData, DocumentMetadata, DocumentQuality
from app.core.extractor import PDFExtractor
from app.core.table_detector import TableDetector
from app.core.chunker import PageAwareChunker
from app.core.vector_store import VectorStoreService
from app.core.llm import LLMService
from app.db.database import DatabaseManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory document status & analysis cache for sub-millisecond retrieval
_document_status_cache: Dict[str, ProcessingStatus] = {}
_document_analysis_cache: Dict[str, AnalysisCardData] = {}
_executor = ThreadPoolExecutor(max_workers=3)


class DocumentService:
    def __init__(self):
        self.extractor = PDFExtractor()
        self.chunker = PageAwareChunker()
        self.vector_store = VectorStoreService()
        self.llm = LLMService()

    def create_document_entry(self, doc_id: str, filename: str, file_path: Path) -> str:
        """Sets initial tracking status and saves to persistent database."""
        file_size_bytes = file_path.stat().st_size if file_path.exists() else 0
        size_mb = file_size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1.0 else f"{file_size_bytes / 1024:.0f} KB"

        init_status = ProcessingStatus(
            document_id=doc_id,
            status="uploading",
            progress_percentage=10,
            current_step_message="File received. Initializing pipeline..."
        )
        _document_status_cache[doc_id] = init_status

        # Persist to SQLite
        DatabaseManager.upsert_document(
            doc_id=doc_id,
            filename=filename,
            safe_name=file_path.name,
            file_size_bytes=file_size_bytes,
            file_size_human=size_str,
            status="uploading",
            progress=10,
            message="File received. Initializing pipeline..."
        )

        return doc_id

    def get_status(self, document_id: str) -> Optional[ProcessingStatus]:
        """Fetches status from memory or falls back to persistent DB."""
        if document_id in _document_status_cache:
            return _document_status_cache[document_id]

        # Fallback to SQLite
        doc = DatabaseManager.get_document(document_id)
        if doc:
            status = ProcessingStatus(
                document_id=doc["id"],
                status=doc["status"],
                progress_percentage=doc["progress_percentage"],
                current_step_message=doc["current_step_message"] or "",
                error=doc["error_message"]
            )
            # Rehydrate memory cache
            _document_status_cache[document_id] = status
            return status

        return None

    def get_analysis(self, document_id: str) -> Optional[AnalysisCardData]:
        """Fetches analysis card from memory, DB, or disk cache."""
        if document_id in _document_analysis_cache:
            return _document_analysis_cache[document_id]

        # Check SQLite DB
        db_analysis = DatabaseManager.get_analysis(document_id)
        if db_analysis:
            card = AnalysisCardData(**db_analysis)
            _document_analysis_cache[document_id] = card
            return card

        # Check disk cache
        cache_file = settings.STORAGE_DIR / f"{document_id}_analysis.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    card = AnalysisCardData(**data)
                    _document_analysis_cache[document_id] = card
                    DatabaseManager.save_analysis(document_id, data)
                    return card
            except Exception as e:
                logger.warning(f"Failed to read disk cache for {document_id}: {e}")

        return None

    def list_recent_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns list of analyzed documents from persistent DB."""
        return DatabaseManager.list_documents(limit=limit)

    def get_page_path(self, document_id: str, page_number: int) -> Optional[Path]:
        page_file = settings.PAGES_DIR / document_id / f"page_{page_number}.png"
        if page_file.exists():
            return page_file
        return None

    def get_pdf_path(self, document_id: str) -> Optional[Path]:
        for file in settings.UPLOAD_DIR.glob(f"{document_id}_*.pdf"):
            if file.exists():
                return file
        return None

    async def process_document_async(self, document_id: str, file_path: Path, filename: str):
        """Asynchronously runs the full ingestion pipeline in thread pool."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, self._process_pipeline_sync, document_id, file_path, filename)

    def _process_pipeline_sync(self, document_id: str, file_path: Path, filename: str):
        """Synchronous ingestion pipeline execution."""
        try:
            # Step 1: Extracting text & coordinates
            self._update_status(document_id, "extracting", 25, "Extracting text and page coordinates...")
            pages, audit = self.extractor.extract_document(file_path, document_id)

            if not pages:
                raise ValueError("Could not extract any content from the uploaded PDF.")

            # Step 2: OCR if scanned
            if audit.get("ocr_applied", False):
                self._update_status(document_id, "running_ocr", 40, "Running OCR enhancement on scanned pages...")
            else:
                self._update_status(document_id, "extracting", 45, "Text and block coordinates extracted.")

            # Step 3: Table detection
            self._update_status(document_id, "extracting", 55, "Detecting tabular data and structures...")
            tables = TableDetector.extract_tables(file_path)

            # Step 4: Chunking and Indexing
            self._update_status(document_id, "indexing", 70, "Creating page-aware semantic chunks & embeddings...")
            chunks = self.chunker.chunk_document(pages, document_id)
            self.vector_store.add_chunks(document_id, chunks)

            # Step 5: Stage 1 Analysis generation
            self._update_status(document_id, "analyzing", 85, "Generating Stage 1 visual analysis card...")

            file_size_bytes = file_path.stat().st_size
            size_mb = file_size_bytes / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB" if size_mb >= 1.0 else f"{file_size_bytes / 1024:.0f} KB"

            metadata = DocumentMetadata(
                document_id=document_id,
                filename=filename,
                file_size_bytes=file_size_bytes,
                file_size_human=size_str,
                page_count=len(pages),
                language="English",
                document_title=filename.replace(".pdf", ""),
                document_type="PDF Document"
            )

            quality = DocumentQuality(
                is_scanned=audit.get("is_scanned", False),
                ocr_applied=audit.get("ocr_applied", False),
                confidence_score=audit.get("confidence_score", 0.95),
                quality_notes=audit.get("quality_notes", [])
            )

            # Sample text from first few pages for overview
            sample_text = "\n\n".join(p.text for p in pages[:5])

            # Run LLM analysis in thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis_card = loop.run_until_complete(
                self.llm.generate_document_analysis(metadata, sample_text, tables, quality)
            )
            loop.close()

            # Cache in memory
            _document_analysis_cache[document_id] = analysis_card

            # Persist to disk and SQLite
            cache_file = settings.STORAGE_DIR / f"{document_id}_analysis.json"
            analysis_dict = analysis_card.model_dump()
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(analysis_dict, f, indent=2)

            DatabaseManager.save_analysis(document_id, analysis_dict)
            DatabaseManager.finalize_document_metadata(
                doc_id=document_id,
                page_count=len(pages),
                title=analysis_card.metadata.document_title,
                doc_type=analysis_card.metadata.document_type,
                is_scanned=quality.is_scanned,
                ocr_applied=quality.ocr_applied,
                confidence_score=quality.confidence_score
            )

            # Mark ready
            self._update_status(document_id, "ready", 100, "Document ready for analysis and chat.", analysis=analysis_card)
            logger.info(f"Pipeline finished successfully for {document_id}")

        except Exception as e:
            logger.error(f"Pipeline failed for document {document_id}: {e}", exc_info=True)
            self._update_status(document_id, "failed", 0, f"Error: {e}", error=str(e))

    def _update_status(
        self,
        doc_id: str,
        status: str,
        progress: int,
        message: str,
        analysis: Optional[AnalysisCardData] = None,
        error: Optional[str] = None
    ):
        if doc_id in _document_status_cache:
            _document_status_cache[doc_id].status = status
            _document_status_cache[doc_id].progress_percentage = progress
            _document_status_cache[doc_id].current_step_message = message
            _document_status_cache[doc_id].error = error
            if analysis:
                _document_status_cache[doc_id].analysis = analysis

        # Persist status to SQLite
        try:
            DatabaseManager.update_document_progress(doc_id, status, progress, message, error)
        except Exception as err:
            logger.warning(f"Failed to update progress in DB: {err}")

    def save_chat_turn(
        self,
        doc_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        follow_ups: Optional[List[str]] = None
    ):
        """Persists chat message into SQLite."""
        DatabaseManager.save_chat_message(doc_id, role, content, citations, follow_ups)

    def get_chat_history(self, doc_id: str) -> List[Dict[str, Any]]:
        """Retrieves conversational history for document."""
        return DatabaseManager.get_chat_history(doc_id)
