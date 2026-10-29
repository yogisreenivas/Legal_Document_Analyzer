"""
evaluate.py - Evaluation script for the RAG Legal Document Analyzer.

Measures three metrics:
1. Retrieval Hit-Rate@K: What fraction of queries retrieve at least one
   chunk from the correct source document?
2. Answer Correctness: Does the generated answer contain the key
   expected information? (Keyword overlap check.)
3. Groundedness Rate: What fraction of answers are verified as grounded?

Optionally compares:
- k=3 vs k=5 retrieval
- chunk_size=500 vs chunk_size=1000

Usage:
    python evaluation/evaluate.py
    python evaluation/evaluate.py --compare-k
    python evaluation/evaluate.py --compare-chunks
"""

import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 output encoding on Windows console to support status indicators
if sys.platform == "win32":
    try:
        if sys.stdout.encoding != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr.encoding != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.config import SAMPLE_DOCS_PATH
from app.ingestion.loader import load_multiple_documents
from app.ingestion.preprocessor import preprocess_documents
from app.ingestion.chunker import create_chunks
from app.embeddings.vector_store import create_vector_store
from app.retrieval.retriever import retrieve_documents
from app.graph.workflow import run_workflow
from app.utils.logger import get_logger

logger = get_logger(__name__)

EVAL_DATASET_PATH = Path(__file__).resolve().parent / "eval_dataset.json"
RESULTS_DIR = Path(__file__).resolve().parent


def load_eval_dataset() -> list:
    """Load the evaluation dataset from JSON.

    Returns:
        List of evaluation entries with questions and expected answers.
    """
    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_index(chunk_size: int = 1000, chunk_overlap: int = 150):
    """Build a FAISS index from sample documents.

    Args:
        chunk_size: Size of text chunks.
        chunk_overlap: Overlap between chunks.

    Returns:
        FAISS vector store.
    """
    logger.info(f"Building index (chunk_size={chunk_size}, overlap={chunk_overlap})")

    # Load all sample documents.
    sample_files = [str(f) for f in SAMPLE_DOCS_PATH.iterdir() if f.is_file()]
    docs = load_multiple_documents(sample_files)
    cleaned = preprocess_documents(docs)
    chunks = create_chunks(cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Create vector store (don't save to disk for evaluation).
    from app.embeddings.embedder import get_embeddings
    from langchain_community.vectorstores import FAISS

    embeddings = get_embeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)

    logger.info(f"Index built with {len(chunks)} chunks")
    return vector_store


def evaluate_retrieval(vector_store, dataset: list, top_k: int = 5) -> list:
    """Evaluate retrieval hit-rate@k.

    A "hit" means at least one retrieved chunk comes from the correct
    source document.

    Args:
        vector_store: FAISS vector store.
        dataset: Evaluation dataset.
        top_k: Number of chunks to retrieve.

    Returns:
        List of result dictionaries.
    """
    results = []
    hits = 0

    for entry in dataset:
        question = entry["question"]
        expected_source = entry["source_doc"]

        retrieved = retrieve_documents(vector_store, question, top_k=top_k)
        sources = [doc.metadata.get("source", "") for doc in retrieved]

        hit = expected_source in sources
        if hit:
            hits += 1

        results.append({
            "id": entry["id"],
            "question": question,
            "expected_source": expected_source,
            "retrieved_sources": sources,
            "hit": hit,
        })

    hit_rate = hits / len(dataset) if dataset else 0
    logger.info(f"Retrieval Hit-Rate@{top_k}: {hit_rate:.2%} ({hits}/{len(dataset)})")

    return results


def evaluate_answer_correctness(vector_store, dataset: list) -> list:
    """Evaluate answer correctness using keyword overlap.

    Checks if key terms from the expected answer appear in the
    generated answer. This is a simple heuristic, not exact matching.

    Args:
        vector_store: FAISS vector store.
        dataset: Evaluation dataset.

    Returns:
        List of result dictionaries.
    """
    results = []
    correct_count = 0

    for entry in dataset:
        question = entry["question"]
        expected = entry["expected_answer"]

        try:
            result = run_workflow(
                query=question,
                vector_store=vector_store,
                task_type="qa",
            )
            answer = result.get("answer", "")
            grounded = result.get("grounded", False)

            # Check correctness: do key terms from expected appear in answer?
            expected_keywords = _extract_keywords(expected)
            answer_lower = answer.lower()

            matched_keywords = [kw for kw in expected_keywords if kw in answer_lower]
            keyword_match_ratio = (
                len(matched_keywords) / len(expected_keywords)
                if expected_keywords else 0
            )

            # Consider correct if >50% of keywords match.
            is_correct = keyword_match_ratio > 0.5

            # Special case: "not found" questions.
            if "not found" in expected.lower():
                is_correct = "not found" in answer_lower

            if is_correct:
                correct_count += 1

            results.append({
                "id": entry["id"],
                "question": question,
                "expected_answer": expected,
                "generated_answer": answer[:200],  # Truncate for CSV
                "keyword_match_ratio": round(keyword_match_ratio, 2),
                "is_correct": is_correct,
                "grounded": grounded,
            })

        except Exception as e:
            logger.error(f"Error evaluating Q{entry['id']}: {e}")
            results.append({
                "id": entry["id"],
                "question": question,
                "expected_answer": expected,
                "generated_answer": f"ERROR: {e}",
                "keyword_match_ratio": 0,
                "is_correct": False,
                "grounded": False,
            })

    correctness = correct_count / len(dataset) if dataset else 0
    grounded_count = sum(1 for r in results if r.get("grounded", False))
    groundedness = grounded_count / len(dataset) if dataset else 0

    logger.info(f"Answer Correctness: {correctness:.2%} ({correct_count}/{len(dataset)})")
    logger.info(f"Groundedness Rate: {groundedness:.2%} ({grounded_count}/{len(dataset)})")

    return results


def _extract_keywords(text: str) -> list:
    """Extract meaningful keywords from text for comparison.

    Removes common stop words and returns lowercase keywords.
    """
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "can", "could", "of", "in", "to", "for",
        "with", "on", "at", "from", "by", "as", "or", "and", "not", "no",
        "it", "its", "this", "that", "these", "those", "their", "they",
    }
    words = text.lower().split()
    keywords = [w.strip(".,;:\"'()[]") for w in words if w.lower().strip(".,;:\"'()[]") not in stop_words]
    return [kw for kw in keywords if len(kw) > 2]


def save_results_csv(results: list, filename: str) -> str:
    """Save evaluation results to a CSV file.

    Args:
        results: List of result dictionaries.
        filename: Output filename.

    Returns:
        Path to the saved CSV file.
    """
    filepath = RESULTS_DIR / filename
    if not results:
        logger.warning("No results to save")
        return str(filepath)

    fieldnames = list(results[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to: {filepath}")
    return str(filepath)


def print_results_table(results: list, title: str) -> None:
    """Print results as a formatted table.

    Args:
        results: List of result dictionaries.
        title: Table title.
    """
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

    if not results:
        print("  No results to display.\n")
        return

    # Compute summary metrics.
    if "hit" in results[0]:
        hits = sum(1 for r in results if r["hit"])
        total = len(results)
        print(f"  Hit-Rate: {hits}/{total} = {hits/total:.2%}\n")

        print(f"  {'ID':<5} {'Hit':<6} {'Question':<50} {'Expected Source':<20}")
        print(f"  {'─'*5} {'─'*6} {'─'*50} {'─'*20}")
        for r in results:
            hit_str = "✅" if r["hit"] else "❌"
            q = r["question"][:48]
            print(f"  {r['id']:<5} {hit_str:<6} {q:<50} {r['expected_source']:<20}")

    elif "is_correct" in results[0]:
        correct = sum(1 for r in results if r["is_correct"])
        grounded = sum(1 for r in results if r.get("grounded", False))
        total = len(results)
        print(f"  Correctness: {correct}/{total} = {correct/total:.2%}")
        print(f"  Groundedness: {grounded}/{total} = {grounded/total:.2%}\n")

        print(f"  {'ID':<5} {'Correct':<9} {'Ground.':<9} {'Match':<7} {'Question':<50}")
        print(f"  {'─'*5} {'─'*9} {'─'*9} {'─'*7} {'─'*50}")
        for r in results:
            c_str = "✅" if r["is_correct"] else "❌"
            g_str = "✅" if r.get("grounded", False) else "❌"
            q = r["question"][:48]
            print(f"  {r['id']:<5} {c_str:<9} {g_str:<9} {r.get('keyword_match_ratio', 0):<7} {q:<50}")

    print()


def main():
    """Run the evaluation pipeline."""
    parser = argparse.ArgumentParser(description="Evaluate the RAG Legal Analyzer")
    parser.add_argument("--compare-k", action="store_true", help="Compare k=3 vs k=5")
    parser.add_argument("--compare-chunks", action="store_true", help="Compare chunk_size=500 vs 1000")
    parser.add_argument("--retrieval-only", action="store_true", help="Only evaluate retrieval (no LLM needed)")
    args = parser.parse_args()

    dataset = load_eval_dataset()
    print(f"\n📊 Loaded {len(dataset)} evaluation examples\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.compare_k:
        # Compare k=3 vs k=5.
        print("🔍 Comparing k=3 vs k=5 retrieval...")
        vector_store = build_index()

        for k in [3, 5]:
            results = evaluate_retrieval(vector_store, dataset, top_k=k)
            print_results_table(results, f"Retrieval Hit-Rate @ k={k}")
            save_results_csv(results, f"results_retrieval_k{k}_{timestamp}.csv")

    elif args.compare_chunks:
        # Compare chunk_size=500 vs 1000.
        print("🔍 Comparing chunk_size=500 vs chunk_size=1000...")

        for cs in [500, 1000]:
            vs = build_index(chunk_size=cs, chunk_overlap=cs // 6)
            results = evaluate_retrieval(vs, dataset, top_k=5)
            print_results_table(results, f"Retrieval Hit-Rate (chunk_size={cs})")
            save_results_csv(results, f"results_retrieval_cs{cs}_{timestamp}.csv")

    elif args.retrieval_only:
        # Retrieval evaluation only (no LLM needed).
        print("🔍 Evaluating retrieval only (no LLM needed)...")
        vector_store = build_index()
        results = evaluate_retrieval(vector_store, dataset, top_k=5)
        print_results_table(results, "Retrieval Hit-Rate @ k=5")
        save_results_csv(results, f"results_retrieval_{timestamp}.csv")

    else:
        # Full evaluation.
        print("🔍 Running full evaluation (retrieval + answer quality)...")
        print("   Note: This requires a valid LLM API key in .env\n")

        vector_store = build_index()

        # 1. Retrieval evaluation.
        retrieval_results = evaluate_retrieval(vector_store, dataset, top_k=5)
        print_results_table(retrieval_results, "Retrieval Hit-Rate @ k=5")
        save_results_csv(retrieval_results, f"results_retrieval_{timestamp}.csv")

        # 2. Answer quality evaluation.
        answer_results = evaluate_answer_correctness(vector_store, dataset)
        print_results_table(answer_results, "Answer Correctness & Groundedness")
        save_results_csv(answer_results, f"results_answers_{timestamp}.csv")

        # 3. Summary.
        print(f"\n{'='*80}")
        print("  📊 EVALUATION SUMMARY")
        print(f"{'='*80}")

        hits = sum(1 for r in retrieval_results if r["hit"])
        correct = sum(1 for r in answer_results if r["is_correct"])
        grounded = sum(1 for r in answer_results if r.get("grounded", False))
        total = len(dataset)

        print(f"\n  Retrieval Hit-Rate@5:  {hits}/{total} = {hits/total:.2%}")
        print(f"  Answer Correctness:    {correct}/{total} = {correct/total:.2%}")
        print(f"  Groundedness Rate:     {grounded}/{total} = {grounded/total:.2%}")
        print(f"\n  Results saved to: {RESULTS_DIR}")
        print()


if __name__ == "__main__":
    main()
