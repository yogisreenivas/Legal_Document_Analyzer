"""
streamlit_app.py - Streamlit UI for the RAG Legal Document Analyzer.

Provides a web interface for:
1. Uploading legal documents (PDF, DOCX, TXT)
2. Processing and indexing documents
3. Asking questions and getting grounded answers
4. Viewing document summaries, key clauses, and structured extractions
5. Displaying citations and groundedness checks

Run with: streamlit run ui/streamlit_app.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to Python path so we can import app modules.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.config import DISCLAIMER, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_TOP_K
from app.ingestion.loader import load_document
from app.ingestion.preprocessor import preprocess_documents
from app.ingestion.chunker import create_chunks, get_chunk_summary
from app.embeddings.vector_store import create_vector_store
from app.graph.workflow import run_workflow
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Page Configuration ────────────────────────────────────────

st.set_page_config(
    page_title="Legal Document Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────

st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .main-header h1 {
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        opacity: 0.85;
        font-size: 1.05rem;
    }

    /* Disclaimer banner */
    .disclaimer-banner {
        background: linear-gradient(90deg, #ff9a00 0%, #ff6d00 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        font-weight: 500;
        text-align: center;
    }

    /* Result card */
    .result-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Citation tag */
    .citation-tag {
        background: #e3f2fd;
        color: #1565c0;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 0.2rem;
    }

    /* Grounding badge */
    .grounded-yes {
        background: #c8e6c9;
        color: #2e7d32;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
    }
    .grounded-no {
        background: #ffcdd2;
        color: #c62828;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
    }

    /* Stats cards */
    .stat-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1565c0;
    }
    .stat-label {
        color: #666;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ──────────────────────────────

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ── Header ────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>⚖️ Legal Document Analyzer</h1>
    <p>AI-powered analysis of contracts, agreements, and policies using RAG</p>
</div>
""", unsafe_allow_html=True)

# Disclaimer banner (always visible).
st.markdown(f'<div class="disclaimer-banner">{DISCLAIMER}</div>', unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────

with st.sidebar:
    st.header("📁 Document Upload")
    st.markdown("Upload legal documents for analysis.")

    uploaded_files = st.file_uploader(
        "Upload PDF, DOCX, or TXT files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, TXT. Max file size: 200MB.",
    )

    if uploaded_files:
        if st.button("🔄 Process Documents", type="primary", use_container_width=True):
            with st.spinner("Processing documents..."):
                all_docs = []

                for uploaded_file in uploaded_files:
                    # Save uploaded file to a temp location.
                    suffix = f".{uploaded_file.name.split('.')[-1]}"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name

                    try:
                        # Load the document.
                        docs = load_document(tmp_path)
                        # Fix the source to use the original filename.
                        for doc in docs:
                            doc.metadata["source"] = uploaded_file.name
                        all_docs.extend(docs)
                        st.sidebar.success(f"✅ Loaded: {uploaded_file.name}")
                    except Exception as e:
                        st.sidebar.error(f"❌ {uploaded_file.name}: {e}")

                if all_docs:
                    # Preprocess.
                    cleaned = preprocess_documents(all_docs)

                    # Chunk.
                    chunks = create_chunks(cleaned)
                    st.session_state.chunks = chunks

                    # Create vector store (in-memory, no save).
                    embeddings_placeholder = st.sidebar.empty()
                    embeddings_placeholder.info("Generating embeddings... (first time may take ~30s to download model)")

                    vector_store = create_vector_store(chunks)
                    st.session_state.vector_store = vector_store
                    st.session_state.documents_loaded = True

                    embeddings_placeholder.empty()

                    # Show stats.
                    summary = get_chunk_summary(chunks)
                    st.sidebar.success("✅ Documents processed and indexed!")

                    st.sidebar.markdown("### 📊 Processing Stats")
                    st.sidebar.metric("Total Chunks", summary["total_chunks"])
                    st.sidebar.metric("Avg Chunk Length", f"{summary['avg_length']} chars")
                    st.sidebar.metric("Sources", len(summary.get("sources", [])))

    st.sidebar.markdown("---")
    if st.sidebar.button("📚 Load Sample Contracts (NDA / Rental / Service)", use_container_width=True):
        from app.config import SAMPLE_DOCS_PATH
        from app.ingestion.loader import load_multiple_documents
        with st.spinner("Loading and indexing sample documents..."):
            sample_files = [str(f) for f in SAMPLE_DOCS_PATH.iterdir() if f.is_file()]
            docs = load_multiple_documents(sample_files)
            cleaned = preprocess_documents(docs)
            chunks = create_chunks(cleaned)
            vector_store = create_vector_store(chunks)
            st.session_state.chunks = chunks
            st.session_state.vector_store = vector_store
            st.session_state.documents_loaded = True
            st.sidebar.success(f"✅ Loaded {len(sample_files)} sample documents ({len(chunks)} chunks)!")
            st.rerun()

    st.divider()

    # Settings.
    st.header("⚙️ Settings & API Key")
    curr_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_val = st.text_input(
        "Google Gemini API Key",
        value=curr_key,
        type="password",
        help="Free key from https://aistudio.google.com/app/apikey"
    )
    if api_key_val and api_key_val != curr_key:
        os.environ["GOOGLE_API_KEY"] = api_key_val
        st.success("API Key updated!")

    st.markdown(f"**Chunk Size:** {CHUNK_SIZE}")
    st.markdown(f"**Chunk Overlap:** {CHUNK_OVERLAP}")
    st.markdown(f"**Top-K Retrieval:** {RETRIEVAL_TOP_K}")

    st.divider()
    st.caption("Built with LangChain, LangGraph, FAISS & Streamlit")


# ── Main Content Area ─────────────────────────────────────────

if not st.session_state.documents_loaded:
    # Show welcome screen when no documents are loaded.
    st.markdown("### 👋 Welcome!")
    st.info(
        "Upload a legal document using the sidebar to get started. "
        "Supported formats: **PDF**, **DOCX**, **TXT**."
    )

    st.markdown("### 🔧 What You Can Do")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📝 Document Summarization**
        Get a plain-English summary of your legal document,
        including section-wise breakdowns.

        **❓ Question Answering**
        Ask specific questions about clauses, terms, conditions,
        and get answers with citations.
        """)
    with col2:
        st.markdown("""
        **🔑 Key Clause Identification**
        Automatically identify termination, payment, liability,
        confidentiality, and other critical clauses.

        **📋 Structured Extraction**
        Extract obligations, deadlines, penalties, and parties
        as structured data.
        """)

else:
    # Document analysis interface.
    st.markdown("### 💬 Ask About Your Document")

    # Quick action buttons.
    st.markdown("**Quick Actions:**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Summarize", use_container_width=True):
            st.session_state.quick_query = "Provide a comprehensive summary of this document"
            st.session_state.quick_task = "summarize"

    with col2:
        if st.button("🔑 Key Clauses", use_container_width=True):
            st.session_state.quick_query = "Identify all key clauses in this document"
            st.session_state.quick_task = "key_clauses"

    with col3:
        if st.button("📋 Extract Info", use_container_width=True):
            st.session_state.quick_query = "Extract all obligations, conditions, deadlines, and penalties"
            st.session_state.quick_task = "extract_obligations"

    with col4:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # Check if a quick action was clicked.
    query = ""
    task_override = None

    if "quick_query" in st.session_state:
        query = st.session_state.quick_query
        task_override = st.session_state.quick_task
        del st.session_state.quick_query
        del st.session_state.quick_task

    # Query input.
    user_query = st.text_input(
        "Ask a question about the document:",
        placeholder="e.g., What is the termination notice period?",
        key="user_query_input",
    )

    if user_query:
        query = user_query
        task_override = None

    # Process the query.
    if query:
        with st.spinner("🔍 Analyzing document..."):
            result = run_workflow(
                query=query,
                vector_store=st.session_state.vector_store,
                task_type=task_override,
            )

        # Add to chat history.
        st.session_state.chat_history.append({
            "query": query,
            "result": result,
        })

    # Display chat history.
    for i, entry in enumerate(st.session_state.chat_history):
        result = entry["result"]

        st.markdown(f"**🙋 Query:** {entry['query']}")

        # Task type badge.
        task_type = result.get("task_type", "qa")
        st.markdown(f"**Task:** `{task_type}`")

        # Answer.
        st.markdown("**📄 Answer:**")
        st.markdown(result.get("answer", "No answer generated."))

        # Citations.
        citations = result.get("citations", [])
        if citations:
            st.markdown("**📎 Citations:**")
            citation_html = " ".join(
                f'<span class="citation-tag">{c}</span>' for c in citations
            )
            st.markdown(citation_html, unsafe_allow_html=True)

        # Groundedness.
        grounded = result.get("grounded", None)
        if grounded is not None:
            if grounded:
                st.markdown(
                    '<span class="grounded-yes">✅ Grounded</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="grounded-no">❌ Not Grounded</span>',
                    unsafe_allow_html=True,
                )
            if result.get("groundedness_explanation"):
                st.caption(result["groundedness_explanation"])

        st.divider()

    # Disclaimer at the bottom.
    st.markdown(f"---\n*{DISCLAIMER}*")
