"""
llm.py - Google Gemini 2.0 Flash client with streaming and structured JSON output.
Enforces Stage 1 schema generation and Stage 2 grounded chat with inline citations.
"""

from typing import List, Dict, Any, AsyncGenerator, Tuple
import os
import json
import re

from app.config import settings
from app.models.schemas import (
    AnalysisCardData,
    DocumentMetadata,
    KeyPoint,
    OutlineItem,
    EntityItem,
    DetectedTable,
    DocumentQuality,
    ChatMessage,
    Citation,
)
from app.utils.logger import get_logger
from app.utils.security import sanitize_for_prompt_context

logger = get_logger(__name__)


class LLMService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized Gemini model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
        else:
            logger.warning("GOOGLE_API_KEY not set. LLMService operating in mock/fallback mode.")
            self.client = None

    def has_api_key(self) -> bool:
        return bool(self.api_key and self.client)

    # ─────────────────────────────────────────────────────────────
    # STAGE 1: STRUCTURED DOCUMENT ANALYSIS
    # ─────────────────────────────────────────────────────────────

    async def generate_document_analysis(
        self,
        metadata: DocumentMetadata,
        sample_pages_text: str,
        detected_tables: List[DetectedTable],
        quality: DocumentQuality
    ) -> AnalysisCardData:
        """
        Generates schema-enforced analysis JSON for Stage 1 visual card.
        """
        logger.info(f"Generating Stage 1 analysis for document: {metadata.filename}")

        if not self.has_api_key():
            logger.warning("No API key configured. Generating template analysis card.")
            return self._generate_fallback_analysis(metadata, sample_pages_text, detected_tables, quality)

        # Build prompt enforcing structured JSON
        sanitized_sample = sanitize_for_prompt_context(sample_pages_text[:12000])

        prompt = f"""
You are an expert Document Intelligence AI. Analyze the following document text and output ONLY a valid JSON object matching the requested schema.

<DOCUMENT_METADATA>
Filename: {metadata.filename}
Page Count: {metadata.page_count}
File Size: {metadata.file_size_human}
</DOCUMENT_METADATA>

<DOCUMENT_CONTENT_SAMPLE>
{sanitized_sample}
</DOCUMENT_CONTENT_SAMPLE>

Instructions:
1. Executive Summary: 3-5 concise sentences describing the document's core purpose and parties involved.
2. Document Type & Title: Infer exact document type (e.g. Non-Disclosure Agreement, Software License, Financial Audit) and exact document title.
3. Key Points: 5-8 bullet points highlighting crucial terms, findings, obligations, or dates.
4. Main Outline: 4-8 key sections with their starting page numbers and level (1=H1, 2=H2).
5. Key Entities: Extract critical People, Organizations, Dates, Financial Amounts, and Locations.

Return JSON in this EXACT structure:
{{
  "document_title": "string",
  "document_type": "string",
  "language": "English",
  "executive_summary": "string",
  "key_points": [
    {{"point": "string", "category": "Obligation | Risk | Financial | Term | General"}}
  ],
  "outline": [
    {{"title": "string", "page_number": 1, "level": 1}}
  ],
  "entities": [
    {{"name": "string", "category": "Person | Organization | Date | Financial Amount | Location | Legal Reference | Other", "context_page": 1}}
  ]
}}
Do NOT wrap in markdown formatting backticks if possible, return raw JSON.
"""

        try:
            response = self.client.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
            )
            raw_json = response.text.strip()
            # Remove any markdown backticks if present
            raw_json = re.sub(r"^```json\s*", "", raw_json)
            raw_json = re.sub(r"```$", "", raw_json).strip()

            parsed = json.loads(raw_json)

            # Update metadata with inferred title/type
            meta = DocumentMetadata(
                document_id=metadata.document_id,
                filename=metadata.filename,
                file_size_bytes=metadata.file_size_bytes,
                file_size_human=metadata.file_size_human,
                page_count=metadata.page_count,
                language=parsed.get("language", "English"),
                document_title=parsed.get("document_title", metadata.filename),
                document_type=parsed.get("document_type", "Document")
            )

            key_points = [KeyPoint(**kp) for kp in parsed.get("key_points", [])]
            outline = [OutlineItem(**item) for item in parsed.get("outline", [])]
            entities = [EntityItem(**ent) for ent in parsed.get("entities", [])]

            return AnalysisCardData(
                metadata=meta,
                executive_summary=parsed.get("executive_summary", "Document successfully parsed and indexed."),
                key_points=key_points,
                outline=outline,
                entities=entities,
                tables=detected_tables,
                charts_images=[],
                quality=quality
            )

        except Exception as e:
            logger.error(f"Error in Gemini analysis generation: {e}. Falling back to rule-based analysis.")
            return self._generate_fallback_analysis(metadata, sample_pages_text, detected_tables, quality)

    def _generate_fallback_analysis(
        self,
        metadata: DocumentMetadata,
        text: str,
        detected_tables: List[DetectedTable],
        quality: DocumentQuality
    ) -> AnalysisCardData:
        """Rule-based extractor when LLM key is absent or returns an error."""
        first_line = text.split("\n")[0][:80] if text else metadata.filename
        title = first_line if len(first_line) > 5 else metadata.filename

        return AnalysisCardData(
            metadata=DocumentMetadata(
                document_id=metadata.document_id,
                filename=metadata.filename,
                file_size_bytes=metadata.file_size_bytes,
                file_size_human=metadata.file_size_human,
                page_count=metadata.page_count,
                language="English",
                document_title=title,
                document_type="Legal / Business Document"
            ),
            executive_summary=(
                f"This document '{metadata.filename}' comprises {metadata.page_count} pages with "
                f"{len(detected_tables)} detected table(s). It has been indexed and embedded into the local vector store "
                "for semantic search and grounded question-answering."
            ),
            key_points=[
                KeyPoint(point=f"Successfully extracted {metadata.page_count} pages of text and metadata.", category="Structure"),
                KeyPoint(point="Page coordinates and bounding boxes mapped for citation jumping.", category="Navigation"),
                KeyPoint(point=f"Identified {len(detected_tables)} structural table(s) across the document.", category="Data"),
                KeyPoint(point="Anti-hallucination ground checks active for all user queries.", category="Security")
            ],
            outline=[
                OutlineItem(title="Document Header & Overview", page_number=1, level=1),
                OutlineItem(title="Core Terms & Provisions", page_number=min(2, metadata.page_count), level=1),
                OutlineItem(title="Execution & Signatures", page_number=metadata.page_count, level=1)
            ],
            entities=[
                EntityItem(name=metadata.filename, category="Other", context_page=1),
                EntityItem(name="All-MiniLM-L6-v2 Embeddings", category="Other", context_page=1)
            ],
            tables=detected_tables,
            charts_images=[],
            quality=quality
        )

    # ─────────────────────────────────────────────────────────────
    # STAGE 2: STREAMING GROUNDED CHAT WITH CITATIONS
    # ─────────────────────────────────────────────────────────────

    async def stream_grounded_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        history: List[ChatMessage]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams grounded answer token-by-token with [p. X] citations,
        yields sources list, and concludes with 3 suggested follow-up questions.
        """
        if not retrieved_chunks:
            yield {
                "event": "token",
                "data": "The uploaded document does not contain information relevant to this question. Please ask a question related to the document contents."
            }
            yield {
                "event": "done",
                "data": {}
            }
            return

        # Prepare context blocks with explicit [Page X] tags
        context_parts = []
        citations_map: Dict[int, Citation] = {}

        for idx, chunk in enumerate(retrieved_chunks):
            page_num = chunk.get("page_number", 1)
            snippet = chunk.get("text", "")
            bbox = chunk.get("bounding_box", {})

            context_parts.append(f"[SOURCE_PAGE_{page_num}]:\n{snippet}\n")

            if page_num not in citations_map:
                citations_map[page_num] = Citation(
                    page_number=page_num,
                    label=f"[p. {page_num}]",
                    snippet=snippet[:180] + "...",
                    bounding_box=bbox
                )

        full_context = "\n---\n".join(context_parts)
        sanitized_context = sanitize_for_prompt_context(full_context)

        system_instruction = (
            "You are a strict, document-grounded AI assistant. Answer the user's question ONLY using the provided "
            "document sources. You must adhere to these inviolable rules:\n"
            "1. Grounding: Every substantive assertion MUST cite its source page using the exact notation [p. X] "
            "(e.g., 'The agreement terminates in 30 days [p. 2]').\n"
            "2. Non-fabrication: If the answer cannot be determined strictly from the sources, state clearly: "
            "'This information is not found in the document.' Do not guess or extrapolate.\n"
            "3. Formatting: Use concise paragraphs, bullet points, or markdown tables where appropriate.\n"
        )

        user_prompt = f"""
{system_instruction}

<DOCUMENT_SOURCES>
{sanitized_context}
</DOCUMENT_SOURCES>

User Question: {query}
"""

        # Yield citations/sources first so UI prepares source list
        sources_list = [c.model_dump() for c in citations_map.values()]
        yield {
            "event": "sources",
            "data": sources_list
        }

        accumulated_answer = ""

        if self.has_api_key():
            try:
                response = self.client.generate_content(
                    user_prompt,
                    stream=True,
                    generation_config={"temperature": 0.1}
                )

                for chunk in response:
                    text_token = chunk.text
                    accumulated_answer += text_token
                    yield {
                        "event": "token",
                        "data": text_token
                    }

            except Exception as e:
                logger.error(f"Error during Gemini streaming: {e}")
                top_chunk = retrieved_chunks[0] if retrieved_chunks else {}
                fallback_tokens = [
                    f"\n\nBased on the document text [p. {top_chunk.get('page_number', 1)}]:\n\n",
                    f"> \"{top_chunk.get('text', '')[:280]}...\"\n\n",
                    f"*(Note: Gemini API returned: `{type(e).__name__}`. You can update your `GOOGLE_API_KEY` in `backend/.env` for full generative responses.)*"
                ]
                for tok in fallback_tokens:
                    accumulated_answer += tok
                    yield {"event": "token", "data": tok}
        else:
            # Fallback mock streaming if API key is not entered
            top_chunk = retrieved_chunks[0] if retrieved_chunks else {}
            mock_tokens = [
                "Based on the document excerpts ",
                f"[p. {top_chunk.get('page_number', 1)}], ",
                "here is the relevant information:\n\n",
                f"> \"{top_chunk.get('text', '')[:280]}...\"\n\n",
                "*(To enable complete generative AI answers, please provide your Google Gemini API Key in `backend/.env`)*."
            ]
            for tok in mock_tokens:
                accumulated_answer += tok
                yield {"event": "token", "data": tok}

        # Generate 3 relevant follow-up questions
        follow_ups = await self.generate_follow_up_questions(query, accumulated_answer)
        yield {
            "event": "follow_ups",
            "data": follow_ups
        }

        yield {
            "event": "done",
            "data": {"status": "complete"}
        }

    async def generate_follow_up_questions(self, query: str, answer: str) -> List[str]:
        """Suggests 3 intelligent follow-up questions based on the answer given."""
        if not self.has_api_key():
            return [
                "What are the main financial terms or fees?",
                "What are the termination and notice conditions?",
                "Who are the designated parties and signers?"
            ]

        prompt = f"""
Based on the user's question and the grounded answer below, suggest exactly 3 short, relevant follow-up questions that the user might want to ask next about this document.

User Question: {query}
Answer: {answer[:600]}

Return JSON array of 3 strings:
["Question 1", "Question 2", "Question 3"]
"""
        try:
            res = self.client.generate_content(
                prompt,
                generation_config={"temperature": 0.4, "response_mime_type": "application/json"}
            )
            raw = res.text.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"```$", "", raw).strip()
            questions = json.loads(raw)
            if isinstance(questions, list) and len(questions) >= 3:
                return questions[:3]
        except Exception:
            pass

        return [
            "What are the main termination provisions?",
            "What liabilities or penalties are specified?",
            "Summarize the governing law and dispute terms."
        ]
