# Presentation Outline — RAG-Based AI Legal Document Analyzer

**B.Tech Final Year Project — AI & ML**

---

## Slide 1: Title Slide

- **Title**: RAG-Based AI Legal Document Analyzer
- **Subtitle**: Intelligent Legal Document Analysis using Retrieval-Augmented Generation
- **Presented by**: [Your Name]
- **Guide**: [Guide Name]
- **Date**: [Presentation Date]
- **Institution**: [College Name]

---

## Slide 2: Problem Statement

**Talking Points:**
- Legal documents are lengthy, complex, and use specialized jargon
- Non-experts struggle to identify critical clauses, obligations, and deadlines
- Manual review is time-consuming and error-prone
- General-purpose LLMs hallucinate — dangerous in the legal domain
- Need: An AI tool that provides accurate, document-grounded analysis

---

## Slide 3: Objectives

**Talking Points:**
- Build a RAG pipeline for legal document analysis
- Support PDF, DOCX, and TXT uploads
- Provide 4 analysis modes: summarization, Q&A, key clause ID, structured extraction
- Implement anti-hallucination through groundedness verification
- Create a user-friendly Streamlit interface
- Evaluate with real metrics (not fabricated)

---

## Slide 4: What is RAG?

**Talking Points:**
- RAG = Retrieval-Augmented Generation (Lewis et al., 2020)
- Combines retrieval (finding relevant passages) with generation (LLM answer)
- Grounds the LLM's response in actual document content
- Reduces hallucination compared to pure LLM approaches
- Show diagram: Query → Retrieve → Generate → Verify

---

## Slide 5: Technology Stack

**Talking Points:**

| Component | Technology |
|-----------|-----------|
| Orchestration | LangChain + LangGraph |
| Vector Store | FAISS (local, serverless) |
| Embeddings | all-MiniLM-L6-v2 (384 dimensions, 80MB) |
| LLM | Google Gemini (free tier) / Ollama (local) |
| UI | Streamlit |
| Testing | pytest |

---

## Slide 6: System Architecture

**Talking Points:**
- Two-phase pipeline: Ingestion (offline) + Query Processing (online)
- Show the architecture diagram
- Explain flow: Upload → Extract → Chunk → Embed → Index → Query → Retrieve → Generate → Verify

---

## Slide 7: LangGraph Workflow

**Talking Points:**
- StateGraph with typed state (TypedDict)
- Nodes: classify → retrieve → generate → verify
- Conditional edges: grounded → end; not grounded → retry/fallback
- Max 1 retry with query rewriting
- Show the Mermaid workflow diagram

---

## Slide 8: Document Ingestion Pipeline

**Talking Points:**
- **Loading**: PyPDF (PDF), python-docx (DOCX), TextLoader (TXT)
- **Preprocessing**: Clean whitespace, remove artifacts, normalize
- **Chunking**: RecursiveCharacterTextSplitter (1000 chars, 150 overlap)
- **Embedding**: all-MiniLM-L6-v2 → 384-d vectors
- **Indexing**: FAISS flat index for exact nearest-neighbor search
- Metadata preserved: source, page, chunk_id

---

## Slide 9: Anti-Hallucination Measures

**Talking Points:**
- **Strict Prompt Engineering**: "Answer ONLY from the provided context"
- **Citation Requirement**: Every claim must reference [Source, Page, Chunk]
- **Groundedness Verification**: 
  - Step 1: Word-overlap heuristic (fast screening)
  - Step 2: LLM-as-judge (accurate verification)
- **Retry Logic**: Rewrite query and re-retrieve (max 1 retry)
- **Fallback**: "Not found in the document" if still ungrounded
- **Persistent Disclaimer**: Always visible

---

## Slide 10: Key Features Demo

**Talking Points:**
- **Live Demo** or **Screenshots** showing:
  1. Document upload and processing
  2. Question answering with citations
  3. Document summarization
  4. Key clause identification
  5. Structured extraction (JSON output)
  6. Groundedness badge (✅/❌)

---

## Slide 11: Evaluation Results

**Talking Points:**
- Evaluated on 20 Q&A pairs across 3 synthetic legal documents
- **Retrieval Hit-Rate@5**: [Insert actual value]
- **Answer Correctness**: [Insert actual value]
- **Groundedness Rate**: [Insert actual value]
- Comparison: k=3 vs k=5, chunk_size 500 vs 1000
- All metrics are from actual system execution

---

## Slide 12: Testing

**Talking Points:**
- 43 unit tests across 4 test files
- Modules tested: chunker, retriever, graph routing, Pydantic schemas
- All tests pass (show pytest output)
- Tests run without API key (self-contained FAISS index)

---

## Slide 13: Limitations

**Talking Points:**
- No OCR for scanned PDFs
- English language only
- Keyword-based query classification (not LLM-based)
- Single-document analysis (no cross-document comparison)
- Dependent on LLM provider availability
- Not a substitute for legal expertise

---

## Slide 14: Future Scope

**Talking Points:**
- OCR integration (Tesseract) for scanned documents
- Multi-language support (Hindi, regional languages)
- Document comparison (version diff)
- Legal domain-specific fine-tuned embeddings
- RAGAS evaluation framework
- Conversation memory (multi-turn Q&A)
- PDF report export

---

## Slide 15: Conclusion & Q&A

**Talking Points:**
- Successfully built a complete RAG pipeline for legal document analysis
- 4 analysis modes with citation-backed, grounded responses
- Clean, modular architecture with LangGraph orchestration
- Anti-hallucination measures for domain safety
- Practical tool with academic rigor

**Thank you! Questions?**
