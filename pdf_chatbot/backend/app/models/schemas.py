"""
schemas.py - Pydantic models for Stage 1 Analysis and Stage 2 Chat Q&A.
Enforces strict schema validation for LLM responses and client communication.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# STAGE 1: ANALYSIS CARD SCHEMAS
# ─────────────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    document_id: str = Field(description="Unique identifier for the document")
    filename: str = Field(description="Original filename of the uploaded PDF")
    file_size_bytes: int = Field(description="File size in bytes")
    file_size_human: str = Field(description="Human readable file size (e.g. '2.4 MB')")
    page_count: int = Field(description="Total page count of the document")
    language: str = Field(default="English", description="Detected primary language")
    document_title: str = Field(description="Inferred or extracted title of the document")
    document_type: str = Field(
        description="Categorization: Contract, Financial Report, Research Paper, Manual, Policy, Invoice, Legal Brief, etc."
    )


class KeyPoint(BaseModel):
    point: str = Field(description="Concise bullet point summary of a key finding or term")
    category: Optional[str] = Field(default="General", description="Category: e.g. Obligation, Finding, Risk, Metric")


class OutlineItem(BaseModel):
    title: str = Field(description="Heading or section name")
    page_number: int = Field(description="Starting page number of this section")
    level: int = Field(default=1, description="Nesting level (1=H1, 2=H2, 3=H3)")


class EntityItem(BaseModel):
    name: str = Field(description="Entity text (e.g. 'Alphabet Inc.', '$5,000,000', 'Dec 31, 2024')")
    category: Literal["Person", "Organization", "Date", "Financial Amount", "Location", "Legal Reference", "Other"] = Field(
        description="Type of entity"
    )
    context_page: Optional[int] = Field(default=None, description="Page number where entity was prominently mentioned")


class DetectedTable(BaseModel):
    table_id: str = Field(description="Unique table ID (e.g. 'table_p2_1')")
    page_number: int = Field(description="Page number where the table appears")
    caption: Optional[str] = Field(default=None, description="Title or description of the table")
    headers: List[str] = Field(default_factory=list, description="Column header strings")
    rows: List[List[str]] = Field(default_factory=list, description="Matrix of table cell values")


class DetectedImage(BaseModel):
    image_id: str = Field(description="Unique image identifier")
    page_number: int = Field(description="Page number where chart/image was detected")
    caption: str = Field(description="Brief description of what the chart or figure illustrates")
    thumbnail_url: Optional[str] = Field(default=None, description="URL or data endpoint to fetch thumbnail raster")


class DocumentQuality(BaseModel):
    is_scanned: bool = Field(default=False, description="Whether the document is a scanned image/raster")
    ocr_applied: bool = Field(default=False, description="Whether Tesseract OCR fallback was invoked")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Estimated extraction confidence (0-1)")
    quality_notes: List[str] = Field(
        default_factory=list,
        description="Observations regarding document condition (e.g. 'Clean native vector PDF', 'Low DPI on page 4')"
    )


class AnalysisCardData(BaseModel):
    """
    Stage 1 Visual Analysis Card schema.
    The LLM outputs this exact structure to populate the frontend cards, chips, and outline.
    """
    metadata: DocumentMetadata
    executive_summary: str = Field(
        description="3 to 5 sentence executive overview explaining the purpose and core substance of the PDF"
    )
    key_points: List[KeyPoint] = Field(
        description="List of 4 to 8 high-impact takeaways from the document"
    )
    outline: List[OutlineItem] = Field(
        description="Document section hierarchy with corresponding page numbers"
    )
    entities: List[EntityItem] = Field(
        description="Key people, organizations, dates, amounts, and locations extracted from text"
    )
    tables: List[DetectedTable] = Field(
        default_factory=list,
        description="Detected structured tables with headers and rows"
    )
    charts_images: List[DetectedImage] = Field(
        default_factory=list,
        description="Detected figures, charts, and diagrams with descriptions"
    )
    quality: DocumentQuality = Field(
        description="Document OCR and text extraction quality audit"
    )


# ─────────────────────────────────────────────────────────────
# STAGE 2: CHAT & CITATIONS SCHEMAS
# ─────────────────────────────────────────────────────────────

class Citation(BaseModel):
    page_number: int = Field(description="Page number referenced (e.g. 3)")
    label: str = Field(description="Display label, e.g. '[p. 3]'")
    snippet: str = Field(description="Direct text excerpt backing the claim")
    bounding_box: Optional[Dict[str, float]] = Field(
        default=None,
        description="Normalized coordinates {x0, y0, x1, y1} for highlighting on page canvas"
    )


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    citations: Optional[List[Citation]] = None
    follow_up_suggestions: Optional[List[str]] = None


class ChatRequest(BaseModel):
    document_id: str
    question: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class ChatStreamChunk(BaseModel):
    """Payload streamed over Server-Sent Events (SSE)."""
    event: Literal["token", "citation", "sources", "follow_ups", "done", "error"]
    data: Any


# ─────────────────────────────────────────────────────────────
# STATUS & PIPELINE PROGRESSION
# ─────────────────────────────────────────────────────────────

class ProcessingStatus(BaseModel):
    document_id: str
    status: Literal["uploading", "extracting", "running_ocr", "indexing", "analyzing", "ready", "failed"]
    progress_percentage: int = Field(ge=0, le=100)
    current_step_message: str
    error: Optional[str] = None
    analysis: Optional[AnalysisCardData] = None
