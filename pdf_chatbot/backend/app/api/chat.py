"""
chat.py - Stage 2 Conversational RAG endpoint with SSE streaming.
Streams token-by-token grounded answers with inline citations, follow-up chips,
and auto-persists conversation history to SQLite.
"""

import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import ChatRequest
from app.core.vector_store import VectorStoreService
from app.core.llm import LLMService
from app.db.database import DatabaseManager
from app.utils.security import validate_document_id, validate_chat_query
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

vector_store = VectorStoreService()
llm_service = LLMService()


@router.post("")
async def stream_chat_response(request: ChatRequest):
    """
    Stage 2 Grounded Q&A with token streaming via SSE.
    Enforces security validations, hybrid vector retrieval, and auto-saves to SQLite.
    """
    validate_document_id(request.document_id)
    clean_question = validate_chat_query(request.question)

    logger.info(f"Chat request for doc '{request.document_id}': '{clean_question[:60]}...'")

    # Persist user question into SQLite
    try:
        DatabaseManager.save_chat_message(
            doc_id=request.document_id,
            role="user",
            content=clean_question
        )
    except Exception as e:
        logger.warning(f"Could not persist user message: {e}")

    # 1. Retrieve top-k semantically and lexically relevant chunks
    retrieved_chunks = vector_store.query(
        document_id=request.document_id,
        query_text=clean_question,
        top_k=5
    )

    async def event_generator():
        accumulated_text = ""
        captured_sources = []
        captured_follow_ups = []

        try:
            async for chunk in llm_service.stream_grounded_answer(
                query=clean_question,
                retrieved_chunks=retrieved_chunks,
                history=request.conversation_history
            ):
                event_name = chunk["event"]
                event_data = chunk["data"]

                if event_name == "token":
                    accumulated_text += str(event_data)
                elif event_name == "sources":
                    captured_sources = event_data if isinstance(event_data, list) else []
                elif event_name == "follow_ups":
                    captured_follow_ups = event_data if isinstance(event_data, list) else []
                elif event_name == "done":
                    # Persist assistant response to SQLite
                    try:
                        DatabaseManager.save_chat_message(
                            doc_id=request.document_id,
                            role="assistant",
                            content=accumulated_text,
                            citations=captured_sources,
                            follow_ups=captured_follow_ups
                        )
                    except Exception as err:
                        logger.warning(f"Could not persist assistant message: {err}")

                # Serialize JSON payload
                if isinstance(event_data, (dict, list)):
                    yield {
                        "event": event_name,
                        "data": json.dumps(event_data)
                    }
                else:
                    yield {
                        "event": event_name,
                        "data": str(event_data)
                    }

        except Exception as e:
            logger.error(f"SSE generator error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream"
    )
