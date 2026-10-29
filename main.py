"""
main.py - CLI entry point for the RAG Legal Document Analyzer.

Provides a command-line interface to:
1. Ingest and index documents
2. Query the indexed documents
3. Run different analysis tasks (summarize, QA, key clauses, extract)

Usage:
    python main.py ingest --files data/sample_docs/nda_agreement.txt
    python main.py query --question "What is the termination clause?"
    python main.py query --question "Summarize the document" --task summarize
"""

import argparse
import sys
import json
from pathlib import Path

# Add the project root to the Python path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 output encoding on Windows console to support status indicators
if sys.platform == "win32":
    try:
        if sys.stdout.encoding != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr.encoding != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.config import DISCLAIMER, SAMPLE_DOCS_PATH
from app.ingestion.loader import load_document, load_multiple_documents
from app.ingestion.preprocessor import preprocess_documents
from app.ingestion.chunker import create_chunks, get_chunk_summary
from app.embeddings.vector_store import create_vector_store, load_vector_store
from app.graph.workflow import run_workflow
from app.utils.logger import get_logger

logger = get_logger(__name__)


def ingest_documents(file_paths: list) -> None:
    """Ingest documents: load, preprocess, chunk, embed, and index.

    Args:
        file_paths: List of file paths to ingest.
    """
    print(f"\n{'='*60}")
    print("📄 Document Ingestion Pipeline")
    print(f"{'='*60}\n")

    # Step 1: Load documents.
    print(f"[1/4] Loading {len(file_paths)} document(s)...")
    documents = load_multiple_documents(file_paths)
    if not documents:
        print("❌ No documents could be loaded. Check file paths and formats.")
        return

    print(f"  ✅ Loaded {len(documents)} document section(s)")

    # Step 2: Preprocess.
    print("[2/4] Preprocessing text...")
    cleaned_docs = preprocess_documents(documents)
    print(f"  ✅ Preprocessed {len(cleaned_docs)} section(s)")

    # Step 3: Chunk.
    print("[3/4] Chunking documents...")
    chunks = create_chunks(cleaned_docs)
    summary = get_chunk_summary(chunks)
    print(f"  ✅ Created {summary['total_chunks']} chunks")
    print(f"     Avg length: {summary['avg_length']} chars")
    print(f"     Sources: {', '.join(summary.get('sources', []))}")

    # Step 4: Embed and index.
    print("[4/4] Generating embeddings and building FAISS index...")
    vector_store = create_vector_store(chunks)
    print(f"  ✅ Vector store created and saved")

    print(f"\n{'='*60}")
    print("✅ Ingestion complete! You can now query the documents.")
    print(f"{'='*60}\n")


def query_documents(question: str, task_type: str = None) -> None:
    """Query the indexed documents.

    Args:
        question: The user's question.
        task_type: Optional task type override.
    """
    print(f"\n{'='*60}")
    print("🔍 Document Query")
    print(f"{'='*60}\n")

    # Load the vector store.
    vector_store = load_vector_store()
    if vector_store is None:
        print("❌ No indexed documents found. Run 'ingest' first.")
        print("   Example: python main.py ingest --files data/sample_docs/nda_agreement.txt")
        return

    print(f"Question: {question}")
    if task_type:
        print(f"Task type: {task_type}")
    print(f"\nProcessing...\n")

    # Run the RAG workflow.
    result = run_workflow(
        query=question,
        vector_store=vector_store,
        task_type=task_type,
    )

    # Display results.
    print(f"{'─'*60}")
    print(f"📋 Task Type: {result.get('task_type', 'N/A')}")
    print(f"{'─'*60}")
    print(f"\n{result.get('answer', 'No answer generated.')}\n")

    print(f"{'─'*60}")
    print(f"📎 Citations:")
    for cite in result.get("citations", []):
        print(f"  • {cite}")

    print(f"\n✅ Grounded: {result.get('grounded', 'N/A')}")
    if result.get("groundedness_explanation"):
        print(f"   {result['groundedness_explanation']}")

    print(f"\n⚠️  {DISCLAIMER}")
    print(f"{'='*60}\n")


def main():
    """Parse CLI arguments and dispatch to the appropriate handler."""
    parser = argparse.ArgumentParser(
        description="RAG-Based AI Legal Document Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Ingest sample documents:
    python main.py ingest --files data/sample_docs/nda_agreement.txt data/sample_docs/rental_agreement.txt

  Ingest all sample documents:
    python main.py ingest --sample

  Ask a question:
    python main.py query --question "What is the termination notice period?"

  Summarize:
    python main.py query --question "Summarize the document" --task summarize

  Extract obligations:
    python main.py query --question "Extract all obligations" --task extract_obligations

  Identify key clauses:
    python main.py query --question "Identify key clauses" --task key_clauses
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command.
    ingest_parser = subparsers.add_parser("ingest", help="Ingest and index documents")
    ingest_parser.add_argument(
        "--files", nargs="+", help="Paths to document files to ingest"
    )
    ingest_parser.add_argument(
        "--sample", action="store_true",
        help="Ingest all sample documents from data/sample_docs/"
    )

    # Query command.
    query_parser = subparsers.add_parser("query", help="Query indexed documents")
    query_parser.add_argument(
        "--question", "-q", required=True, help="Your question about the document"
    )
    query_parser.add_argument(
        "--task", "-t",
        choices=["summarize", "qa", "key_clauses", "extract_obligations"],
        help="Force a specific task type (optional)"
    )

    args = parser.parse_args()

    if args.command == "ingest":
        if args.sample:
            # Ingest all sample documents.
            sample_dir = SAMPLE_DOCS_PATH
            if sample_dir.exists():
                files = [str(f) for f in sample_dir.iterdir() if f.is_file()]
                if files:
                    ingest_documents(files)
                else:
                    print("❌ No files found in sample_docs/")
            else:
                print(f"❌ Sample docs directory not found: {sample_dir}")
        elif args.files:
            ingest_documents(args.files)
        else:
            print("❌ Provide --files or --sample flag. See --help for usage.")

    elif args.command == "query":
        query_documents(args.question, args.task)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
