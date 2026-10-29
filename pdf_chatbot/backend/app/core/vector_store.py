"""
vector_store.py - ChromaDB embedded vector store with local sentence-transformers embeddings.
Features Hybrid Retrieval combining Dense Cosine Embeddings with Lexical Keyword Scoring
and Reciprocal Rank Fusion (RRF) for high precision legal & technical document retrieval.
"""

from typing import List, Dict, Any, Optional
import json
import re
import math
from app.config import settings
from app.core.chunker import Chunk
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level embedding model cache
_embedding_model: Optional[Any] = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL}")
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedding_model


class VectorStoreService:
    def __init__(self):
        self._client = None
        self._model = None

    @property
    def client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        return self._client

    @property
    def model(self):
        if self._model is None:
            self._model = get_embedding_model()
        return self._model

    def _get_collection_name(self, document_id: str) -> str:
        clean_id = document_id.replace("-", "_")
        return f"doc_{clean_id}"[:60]

    def add_chunks(self, document_id: str, chunks: List[Chunk]) -> None:
        """
        Embeds and indexes chunks into a dedicated document collection.
        """
        if not chunks:
            logger.warning(f"No chunks to index for document {document_id}")
            return

        collection_name = self._get_collection_name(document_id)
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "page_number": c.page_number,
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "bounding_box": json.dumps(c.bounding_box),
            }
            for c in chunks
        ]

        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()

        # Batch insert into ChromaDB
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            collection.upsert(
                ids=ids[i:i + batch_size],
                embeddings=embeddings[i:i + batch_size],
                documents=texts[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )

        logger.info(f"Indexed {len(chunks)} chunks into Chroma collection '{collection_name}'")

    def query(self, document_id: str, query_text: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Hybrid Retrieval: Combines dense semantic vector search with lexical keyword scoring
        using Reciprocal Rank Fusion (RRF).
        """
        k = top_k or settings.RETRIEVAL_TOP_K
        collection_name = self._get_collection_name(document_id)

        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            logger.warning(f"Collection '{collection_name}' not found.")
            return []

        total_count = collection.count()
        if total_count == 0:
            return []

        # 1. Dense Semantic Search (retrieve candidates)
        fetch_k = min(max(k * 3, 10), total_count)
        query_embedding = self.model.encode([query_text], convert_to_numpy=True).tolist()

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=fetch_k
        )

        if not results or "documents" not in results or not results["documents"]:
            return []

        docs = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)

        # 2. Extract significant query terms for Lexical Scoring
        stop_words = {"what", "is", "the", "and", "or", "in", "of", "to", "a", "an", "for", "with", "by", "on", "are", "as", "at"}
        raw_terms = re.findall(r"\b[\w\$\.]+\b", query_text.lower())
        query_terms = [t for t in raw_terms if len(t) > 1 and t not in stop_words]

        # 3. Score both dense and lexical ranks
        candidates = []
        for rank_dense, (doc_text, meta, dist) in enumerate(zip(docs, metadatas, distances), start=1):
            bbox = json.loads(meta.get("bounding_box", "{}"))
            doc_lower = doc_text.lower()

            # Lexical score calculation
            lex_score = 0.0
            # Phrase match boost
            if query_text.lower() in doc_lower:
                lex_score += 4.0

            # Term overlap count
            for term in query_terms:
                if term in doc_lower:
                    # Higher weight if term is a number or currency (e.g. "4.1", "$500")
                    if any(char.isdigit() for char in term) or "$" in term:
                        lex_score += 2.0
                    else:
                        lex_score += 1.0

            candidates.append({
                "text": doc_text,
                "page_number": int(meta.get("page_number", 1)),
                "chunk_id": meta.get("chunk_id", ""),
                "similarity_score": round(1.0 - float(dist), 4),
                "bounding_box": bbox,
                "rank_dense": rank_dense,
                "lex_score": lex_score,
            })

        # Rank candidates by lexical score descending
        candidates_by_lex = sorted(candidates, key=lambda c: c["lex_score"], reverse=True)
        for rank_lex, c in enumerate(candidates_by_lex, start=1):
            c["rank_lex"] = rank_lex

        # 4. Reciprocal Rank Fusion (RRF constant C = 60)
        C = 60.0
        for c in candidates:
            rrf_dense = 1.0 / (C + c["rank_dense"])
            rrf_lex = 1.0 / (C + c["rank_lex"]) if c["lex_score"] > 0 else 0.0
            c["rrf_score"] = rrf_dense + (1.2 * rrf_lex)

        # Sort by final RRF score
        candidates.sort(key=lambda c: c["rrf_score"], reverse=True)
        top_candidates = candidates[:k]

        logger.info(f"Hybrid retrieval selected {len(top_candidates)} chunks (dense+lexical RRF) for '{query_text[:50]}...'")
        return [
            {
                "text": c["text"],
                "page_number": c["page_number"],
                "chunk_id": c["chunk_id"],
                "similarity_score": c["similarity_score"],
                "bounding_box": c["bounding_box"],
            }
            for c in top_candidates
        ]

    def delete_document_index(self, document_id: str) -> bool:
        collection_name = self._get_collection_name(document_id)
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.warning(f"Could not delete collection '{collection_name}': {e}")
            return False
