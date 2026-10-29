"""
main.py - Enterprise-grade FastAPI application entry point for DocIntel AI.
Features SQLite lifecycle initialization, CORS, Request Correlation IDs,
Sliding-Window Rate Limiting, and standardized error handling.
"""

import time
import uuid
from typing import Dict, List
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.db.database import init_db
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.utils.logger import get_logger

logger = get_logger("main")

# In-memory sliding window rate limiter
_request_timestamps: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_MINUTE = 120
MAX_UPLOADS_PER_MINUTE = 20


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initializes SQLite database and storage."""
    logger.info("Initializing persistent storage and database schema...")
    init_db()
    yield
    logger.info("Shutting down DocIntel AI backend service...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise two-stage PDF Analysis Chatbot API with visual analysis cards and streaming grounded chat.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)


@app.middleware("http")
async def operational_middleware(request: Request, call_next):
    """
    Production middleware:
    - Generates and attaches unique X-Request-ID
    - Measures and reports execution latency in X-Process-Time
    - Enforces sliding-window rate limiting per client IP
    """
    start_time = time.time()
    req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Rate limiting check
    now = time.time()
    ip_history = _request_timestamps[client_ip]
    # Prune timestamps older than window
    ip_history = [t for t in ip_history if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _request_timestamps[client_ip] = ip_history

    limit = MAX_UPLOADS_PER_MINUTE if "/upload" in request.url.path else MAX_REQUESTS_PER_MINUTE

    if len(ip_history) >= limit:
        logger.warning(f"Rate limit exceeded for client {client_ip} on path {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please wait before making additional calls.",
                    "request_id": req_id
                }
            },
            headers={"Retry-After": "60", "X-Request-ID": req_id}
        )

    ip_history.append(now)

    # Process request
    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - len(ip_history)))

    return response


# Standardized error handling
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "path": request.url.path
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload.",
                "details": exc.errors(),
                "path": request.url.path
            }
        }
    )


# Include API routers
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/api/health")
async def health_check():
    """Health and runtime diagnostics endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_model": settings.GEMINI_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "chroma_dir": str(settings.CHROMA_DIR),
        "database": "sqlite_wal_active"
    })


@app.get("/")
async def root():
    return {
        "message": "DocIntel AI - Production PDF Analysis Chatbot API is operational.",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
