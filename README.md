# RAG-Based AI Legal Document Analyzer

An intelligent system that helps users understand contracts, agreements, policies, and terms & conditions using Retrieval-Augmented Generation (RAG) with Large Language Models.

> ⚠️ **Disclaimer**: This tool is for AI-assisted information analysis only. It is NOT a substitute for professional legal advice.

## Features

- **📄 Document Upload**: Support for PDF, DOCX, and TXT legal documents
- **📝 Document Summarization**: Plain-English summaries with section-wise breakdown
- **❓ Question Answering**: Clause-level Q&A with citations and source quotes
- **🔑 Key Clause Identification**: Automatic detection of termination, payment, confidentiality, liability, indemnity, governing law, dispute resolution, renewal, and IP clauses
- **📋 Structured Extraction**: Extract obligations, conditions, deadlines, penalties, and parties as structured data
- **🛡️ Anti-Hallucination**: Groundedness verification ensures answers come from the document
- **🔄 Provider-Agnostic LLM**: Switch between Google Gemini and Ollama with a config change

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | LangChain + LangGraph |
| Vector Store | FAISS (local) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Google Gemini (default) / Ollama (local) |
| UI | Streamlit |
| Testing | pytest |
| Language | Python 3.10+ |

## Quick Start

### 1. Clone and Setup

```bash
cd legal-rag-analyzer
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your Google API key
# Get free key at: https://aistudio.google.com/app/apikey
```

### 4. Run the Application

#### Option A: Streamlit UI (Recommended)
```bash
streamlit run ui/streamlit_app.py
```

#### Option B: CLI
```bash
# Ingest sample documents
python main.py ingest --sample

# Ask a question
python main.py query --question "What is the termination notice period?"

# Summarize
python main.py query --question "Summarize the document" --task summarize

# Extract obligations
python main.py query --question "Extract all obligations" --task extract_obligations
```

## Project Structure

```
legal-rag-analyzer/
├── app/
│   ├── config.py              # Central configuration
│   ├── ingestion/             # Document loading, preprocessing, chunking
│   ├── embeddings/            # Embedding generation, FAISS vector store
│   ├── retrieval/             # Semantic search
│   ├── llm/                   # LLM factory, prompt templates
│   ├── graph/                 # LangGraph workflow
│   ├── schemas/               # Pydantic output models
│   └── utils/                 # Logger, helpers
├── ui/streamlit_app.py        # Streamlit web interface
├── data/sample_docs/          # 3 synthetic legal documents
├── tests/                     # Unit tests (pytest)
├── evaluation/                # Evaluation dataset and scripts
├── docs/                      # Academic documentation
├── main.py                    # CLI entry point
└── requirements.txt           # Dependencies
```

## Running Tests

```bash
pytest tests/ -v
```

## Evaluation

```bash
# Retrieval-only evaluation (no LLM needed)
python evaluation/evaluate.py --retrieval-only

# Full evaluation (requires API key)
python evaluation/evaluate.py

# Compare k=3 vs k=5
python evaluation/evaluate.py --compare-k
```

## Configuration

All settings are in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM backend: `gemini` or `ollama` | `gemini` |
| `GOOGLE_API_KEY` | Google Gemini API key | (required) |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash` |
| `EMBEDDING_MODEL` | Sentence-transformer model | `all-MiniLM-L6-v2` |
| `RETRIEVAL_TOP_K` | Number of chunks to retrieve | `5` |
| `CHUNK_SIZE` | Characters per chunk | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `150` |

## Pipeline Architecture

```
User uploads document
    → Text Extraction (PDF/DOCX/TXT)
    → Preprocessing (clean, normalize)
    → Chunking (RecursiveCharacterTextSplitter)
    → Embedding (all-MiniLM-L6-v2)
    → FAISS Indexing

User asks a question
    → Query Classification
    → Semantic Retrieval (top-k chunks)
    → LLM Generation (task-specific prompt)
    → Groundedness Verification
    → Retry (if not grounded, max 1 retry)
    → Response with Citations
```

## License

This project is developed for academic purposes as a B.Tech final-year project.

## Authors

B.Tech AI & ML Final Year Project
