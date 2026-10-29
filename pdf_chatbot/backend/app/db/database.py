"""
database.py - Thread-safe SQLite persistence layer for DocIntel AI.
Stores document metadata, processing lifecycle, analysis cache, and conversational history.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = settings.STORAGE_DIR / "docintel.db"


def init_db():
    """Initializes database schema with WAL mode enabled for high concurrency."""
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")

        # 1. Documents Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                safe_name TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                file_size_human TEXT,
                page_count INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                progress_percentage INTEGER DEFAULT 0,
                current_step_message TEXT,
                error_message TEXT,
                document_title TEXT,
                document_type TEXT,
                is_scanned BOOLEAN DEFAULT 0,
                ocr_applied BOOLEAN DEFAULT 0,
                confidence_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Stage 1 Analysis Cache Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                document_id TEXT PRIMARY KEY,
                executive_summary TEXT,
                analysis_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
        """)

        # 3. Chat History Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                citations_json TEXT,
                follow_ups_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
        """)

        # Indices for high-speed queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_updated ON documents(updated_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_doc ON chat_history(document_id, created_at ASC);")

        conn.commit()
        logger.info(f"Database initialized successfully at {DB_PATH}")


@contextmanager
def get_db():
    """Context manager for thread-safe SQLite connections."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class DatabaseManager:
    """High-level DAO for document metadata, analysis, and chat history."""

    @staticmethod
    def upsert_document(
        doc_id: str,
        filename: str,
        safe_name: str,
        file_size_bytes: int,
        file_size_human: str,
        status: str = "uploading",
        progress: int = 10,
        message: str = "Initializing pipeline..."
    ):
        with get_db() as conn:
            conn.execute("""
                INSERT INTO documents (
                    id, filename, safe_name, file_size_bytes, file_size_human,
                    status, progress_percentage, current_step_message, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    progress_percentage=excluded.progress_percentage,
                    current_step_message=excluded.current_step_message,
                    updated_at=CURRENT_TIMESTAMP;
            """, (doc_id, filename, safe_name, file_size_bytes, file_size_human, status, progress, message))
            conn.commit()

    @staticmethod
    def update_document_progress(
        doc_id: str,
        status: str,
        progress: int,
        message: str,
        error: Optional[str] = None
    ):
        with get_db() as conn:
            conn.execute("""
                UPDATE documents
                SET status = ?,
                    progress_percentage = ?,
                    current_step_message = ?,
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (status, progress, message, error, doc_id))
            conn.commit()

    @staticmethod
    def finalize_document_metadata(
        doc_id: str,
        page_count: int,
        title: str,
        doc_type: str,
        is_scanned: bool = False,
        ocr_applied: bool = False,
        confidence_score: float = 1.0
    ):
        with get_db() as conn:
            conn.execute("""
                UPDATE documents
                SET page_count = ?,
                    document_title = ?,
                    document_type = ?,
                    is_scanned = ?,
                    ocr_applied = ?,
                    confidence_score = ?,
                    status = 'ready',
                    progress_percentage = 100,
                    current_step_message = 'Document ready for analysis and chat.',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (page_count, title, doc_type, is_scanned, ocr_applied, confidence_score, doc_id))
            conn.commit()

    @staticmethod
    def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?;", (doc_id,)).fetchone()
            if row:
                return dict(row)
            return None

    @staticmethod
    def list_documents(limit: int = 50) -> List[Dict[str, Any]]:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, filename, file_size_human, page_count, status,
                       document_title, document_type, created_at, updated_at
                FROM documents
                ORDER BY updated_at DESC
                LIMIT ?;
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def save_analysis(doc_id: str, analysis_dict: Dict[str, Any]):
        summary = analysis_dict.get("executive_summary", "")
        analysis_json = json.dumps(analysis_dict)
        with get_db() as conn:
            conn.execute("""
                INSERT INTO analysis_cache (document_id, executive_summary, analysis_json, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(document_id) DO UPDATE SET
                    executive_summary = excluded.executive_summary,
                    analysis_json = excluded.analysis_json,
                    created_at = CURRENT_TIMESTAMP;
            """, (doc_id, summary, analysis_json))
            conn.commit()

    @staticmethod
    def get_analysis(doc_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            row = conn.execute("SELECT analysis_json FROM analysis_cache WHERE document_id = ?;", (doc_id,)).fetchone()
            if row:
                return json.loads(row["analysis_json"])
            return None

    @staticmethod
    def save_chat_message(
        doc_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        follow_ups: Optional[List[str]] = None
    ):
        with get_db() as conn:
            conn.execute("""
                INSERT INTO chat_history (document_id, role, content, citations_json, follow_ups_json, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                doc_id,
                role,
                content,
                json.dumps(citations) if citations else None,
                json.dumps(follow_ups) if follow_ups else None
            ))
            conn.commit()

    @staticmethod
    def get_chat_history(doc_id: str) -> List[Dict[str, Any]]:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, role, content, citations_json, follow_ups_json, created_at
                FROM chat_history
                WHERE document_id = ?
                ORDER BY created_at ASC;
            """, (doc_id,)).fetchall()

            messages = []
            for r in rows:
                citations = json.loads(r["citations_json"]) if r["citations_json"] else []
                follow_ups = json.loads(r["follow_ups_json"]) if r["follow_ups_json"] else []
                messages.append({
                    "id": str(r["id"]),
                    "role": r["role"],
                    "content": r["content"],
                    "citations": citations,
                    "follow_up_suggestions": follow_ups,
                    "created_at": r["created_at"]
                })
            return messages

    @staticmethod
    def delete_document(doc_id: str) -> bool:
        with get_db() as conn:
            conn.execute("DELETE FROM chat_history WHERE document_id = ?;", (doc_id,))
            conn.execute("DELETE FROM analysis_cache WHERE document_id = ?;", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?;", (doc_id,))
            conn.commit()
            return True
