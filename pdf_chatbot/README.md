# DocIntel AI — Two-Stage PDF Analysis & Grounded Chatbot

A production-grade Document Intelligence system inspired by ChatPDF and Acrobat AI Assistant. It combines high-speed PDF vector coordinate extraction, local dense semantic retrieval, and Large Language Models to deliver a two-stage document exploration experience:

1. **Stage 1 (Visual Analysis Card)**: Immediately upon document upload, a schema-enforced analysis card renders executive summaries, categorized takeaways, hierarchical outlines, key entities, responsive data tables, and an OCR quality audit.
2. **Stage 2 (Grounded Streaming Chat)**: Conversational RAG with token-by-token streaming, clickable inline citations (`[p. X]`), instant jump-to-page bounding box highlights in the PDF viewer, snippet previews, and dynamic follow-up suggestions.

---

## Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend: Next.js 14 + Tailwind CSS (Port 3000)"]
        UI[Split-Screen Workspace]
        Viewer[PDF Canvas Viewer + Highlighting]
        Card[Stage 1: Visual Analysis Card]
        Chat[Stage 2: Streaming Grounded Chat]
    end

    subgraph Backend["Backend: FastAPI + Uvicorn (Port 8000)"]
        UploadRouter["/api/documents/upload"]
        StatusRouter["/api/documents/:id/status"]
        ChatRouter["/api/chat (SSE Stream)"]
        Extractor[PyMuPDF / pdfplumber + OCR]
        Chunker[Page-Aware Semantic Chunker]
    end

    subgraph Storage["Persistence & Vectors"]
        Chroma[(ChromaDB Local Vector Index)]
        DiskStore["Storage: PDF & Page Rasters"]
    end

    subgraph LLM["Language Model"]
        Gemini[Google Gemini 2.0 Flash]
    end

    UI --> UploadRouter
    UploadRouter --> Extractor
    Extractor --> DiskStore
    Extractor --> Chunker
    Chunker --> Chroma
    Extractor --> Gemini
    Gemini --> Card
    
    Chat --> ChatRouter
    ChatRouter --> Chroma
    Chroma -->|Top-k Page Chunks| ChatRouter
    ChatRouter --> Gemini
    Gemini -->|Token Stream + Citations| Chat
    Chat -.->|Citation [p. X] Click| Viewer
```

---

## Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| **Backend** | Python 3.10+, FastAPI, Uvicorn | High-throughput asynchronous endpoints with SSE streaming and Pydantic v2 validation. |
| **PDF Extraction** | PyMuPDF (`fitz`), `pdfplumber`, `pytesseract` | Microsecond text and coordinate bounding-box extraction with automatic OCR fallback. |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local 384-dimensional dense semantic vectors (zero cloud cost/latency). |
| **Vector Store** | ChromaDB (`chromadb`) | Embedded serverless persistent vector database stored locally in `./storage/chroma`. |
| **LLM Provider** | Google Gemini 2.0 Flash (`google-generativeai`) | Low-latency streaming, schema-enforced JSON outputs, and generous free tier. |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS v3 | Split-screen desktop workspace and mobile tabbed view with Lucide iconography. |

---

## Project Structure

```
pdf_chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entry point
│   │   ├── config.py                   # Environment & storage settings
│   │   ├── api/
│   │   │   ├── documents.py            # Upload, status, pages, analysis endpoints
│   │   │   └── chat.py                 # Stage 2 SSE streaming endpoint
│   │   ├── core/
│   │   │   ├── extractor.py            # PyMuPDF text & coordinate extraction + OCR
│   │   │   ├── table_detector.py       # pdfplumber tabular data parser
│   │   │   ├── chunker.py              # Page-aware chunker preserving coordinates
│   │   │   ├── vector_store.py         # ChromaDB persistence & similarity search
│   │   │   └── llm.py                  # Gemini SDK client (JSON schemas & streaming)
│   │   ├── models/
│   │   │   └── schemas.py              # Pydantic models for Stage 1 & 2
│   │   └── utils/
│   │       ├── security.py             # Prompt injection defense & file validation
│   │       └── logger.py               # Structured logger
│   ├── storage/                        # Persistent uploads, page rasters, Chroma DB
│   ├── requirements.txt
│   └── tests/                          # Backend pytest suite
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx              # Root layout with theme provider
│   │   │   ├── page.tsx                # Main split-screen container
│   │   │   └── globals.css             # Tailwind configuration
│   │   ├── components/
│   │   │   ├── layout/Header.tsx       # Top bar with export & theme controls
│   │   │   ├── upload/Dropzone.tsx     # Drag-and-drop zone with presets
│   │   │   ├── upload/ProcessingTimeline.tsx # Real-time pipeline step tracker
│   │   │   ├── viewer/PDFViewer.tsx    # PDF canvas renderer with citation highlights
│   │   │   ├── analysis/AnalysisCard.tsx # Stage 1 visual intelligence card
│   │   │   └── chat/ChatPanel.tsx      # Stage 2 streaming chat with citation badges
│   │   ├── lib/
│   │   │   ├── api.ts                  # Fetch client and SSE reader
│   │   │   └── utils.ts                # Markdown exporter & formatting
│   │   └── types/                      # TypeScript definitions matching Pydantic
│   └── package.json
├── samples/                            # 3 Synthetic PDFs & Evaluation dataset
│   ├── sample_text_contract.pdf        # Text legal agreement
│   ├── sample_financial_tables.pdf     # Table-heavy financial report
│   ├── sample_scanned_receipt.pdf      # Scanned image document
│   └── eval_qa_pairs.json              # Benchmark evaluation set
└── docs/
    ├── demo_script.md                  # 5-minute walkthrough script
    └── openapi_postman_collection.json # API Postman collection
```

---

## Getting Started

### 1. Backend Setup

```powershell
cd c:\Users\dell\Downloads\legal_rag\pdf_chatbot\backend

# Ensure Python virtual environment is active
..\..\venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Create .env file with your Google Gemini API key
# Get a free key at: https://aistudio.google.com/app/apikey
echo GOOGLE_API_KEY=your_gemini_api_key_here > .env

# Run FastAPI backend (Port 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 2. Frontend Setup

In a separate terminal:
```powershell
cd c:\Users\dell\Downloads\legal_rag\pdf_chatbot\frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Open your browser at **`http://localhost:3000`** (or `http://localhost:3001` if port 3000 is occupied).

---

## Key Features & User Workflows

### 1. Stage 1: Visual Document Intelligence Card
When a PDF is uploaded, the backend immediately extracts blocks, tables, and page metadata, and generates an `AnalysisCardData` structure:
- **Executive Summary**: 3-5 lines explaining document context and parties.
- **Key Highlights**: High-impact categorized bullet points.
- **Document Outline**: Interactive section tree; clicking any section scrolls the PDF viewer directly to that page.
- **Entity Extraction**: Visual tags for Persons, Organizations, Financial Amounts, Dates, and Locations.
- **Tabular Data**: Detected tables rendered with headers and rows.
- **Quality Audit**: Diagnostics on OCR usage, scan condition, and confidence scores.

### 2. Stage 2: Grounded Chat & Instant Citation Jumping
- In the right-hand panel, users can ask free-form questions.
- Answers are streamed token-by-token over SSE.
- Claims include inline clickable badges like `[p. 2]`.
- **Clicking any citation scrolls the PDF viewer to that exact page and draws an animated amber highlight over the source passage.**
- **Sources Used Drawer**: Expandable drawer with quoted snippet previews.
- **Follow-up Chips**: 3 dynamically generated relevant questions.

### 3. Anti-Hallucination Safeguard
If a question asks about details not present in the document (e.g. *"What color is the submarine in the contract?"*), the prompt instructions enforce:
> *"This information is not found in the document."*

---

## Testing & Verification

### Unit Tests
```powershell
cd c:\Users\dell\Downloads\legal_rag\pdf_chatbot\backend
..\..\venv\Scripts\python.exe -m pytest tests -v
```

### Evaluation Benchmark
Evaluate answer accuracy and citation correctness on the 3 sample PDFs using `samples/eval_qa_pairs.json`.
