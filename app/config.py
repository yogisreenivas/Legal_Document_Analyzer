"""
config.py - Central configuration for the RAG Legal Document Analyzer.

All settings are loaded from environment variables (.env file).
Defaults are provided so the app can start even without a .env file
(though it will fail when calling the LLM without an API key).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the project root.
# find_dotenv() walks up directories; we pin it to the project root instead.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# ── LLM Provider ──────────────────────────────────────────────
# Which LLM backend to use: "gemini" (cloud, free tier) or "ollama" (local).
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")

# ── Google Gemini ─────────────────────────────────────────────
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Ollama (local fallback) ───────────────────────────────────
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── Embedding Model ──────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Retrieval ─────────────────────────────────────────────────
# Number of top chunks to retrieve for each query.
RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# ── Chunking ─────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

# ── Paths ─────────────────────────────────────────────────────
# Where the FAISS index is persisted on disk.
VECTOR_STORE_PATH: Path = PROJECT_ROOT / os.getenv("VECTOR_STORE_PATH", "data/vector_store")
# Directory containing sample legal documents.
SAMPLE_DOCS_PATH: Path = PROJECT_ROOT / "data" / "sample_docs"

# ── Disclaimer ────────────────────────────────────────────────
DISCLAIMER: str = (
    "⚠️ AI-assisted analysis only. "
    "Not a substitute for professional legal advice."
)
