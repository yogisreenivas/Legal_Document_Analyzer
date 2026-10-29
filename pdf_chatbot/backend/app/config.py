"""
config.py - Central configuration settings for PDF Analysis Chatbot.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Root paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env file from backend directory or project root
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / ".env")


class Settings(BaseSettings):
    # Service Information
    APP_NAME: str = "PDF Analysis Chatbot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "*"
    ]

    # File Storage Paths
    STORAGE_DIR: Path = BACKEND_DIR / "storage"
    UPLOAD_DIR: Path = BACKEND_DIR / "storage" / "uploads"
    PAGES_DIR: Path = BACKEND_DIR / "storage" / "pages"
    CHROMA_DIR: Path = BACKEND_DIR / "storage" / "chroma"

    # Ingestion & Limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    MAX_PAGE_COUNT: int = int(os.getenv("MAX_PAGE_COUNT", "250"))
    ALLOWED_EXTENSIONS: set[str] = {".pdf"}

    # Processing & Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))

    # LLM Settings (Google Gemini)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # OCR Settings
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    OCR_DPI: int = 300
    MIN_TEXT_CHARS_PER_PAGE: int = 40  # Triggers OCR fallback if page has fewer chars

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }


settings = Settings()

# Ensure storage directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PAGES_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
