# Viva Questions & Answers — RAG-Based AI Legal Document Analyzer

**40 Likely Viva Questions with Concise Answers**

---

## Section A: RAG Fundamentals (Q1-Q8)

### Q1. What is Retrieval-Augmented Generation (RAG)?

**Answer:** RAG is a technique that combines information retrieval with text generation. Instead of relying solely on an LLM's parametric knowledge (which can be outdated or inaccurate), RAG first retrieves relevant passages from a knowledge source (e.g., a document), then passes those passages as context to the LLM for generating a response. This grounds the LLM's output in actual source material, reducing hallucination.

---

### Q2. Why is RAG preferred over fine-tuning for this project?

**Answer:** Fine-tuning requires training data, GPU resources, and retraining for every new document. RAG is preferred because:
1. **No retraining needed** — new documents can be analyzed by simply indexing them.
2. **Transparency** — we can trace every answer back to specific document chunks.
3. **Cost-effective** — uses pre-trained models without GPU-intensive training.
4. **Up-to-date** — always retrieves from the latest document content.

---

### Q3. What are the main components of a RAG pipeline?

**Answer:** 
1. **Document Ingestion**: Load and extract text from files.
2. **Text Chunking**: Split text into manageable, overlapping segments.
3. **Embedding Generation**: Convert chunks into dense vector representations.
4. **Vector Indexing**: Store vectors in a vector store (FAISS) for efficient search.
5. **Retrieval**: Find the most relevant chunks for a given query via similarity search.
6. **Generation**: Use an LLM to generate an answer based on retrieved chunks.
7. **Verification** (optional): Check that the answer is grounded in the retrieved context.

---

### Q4. What is the difference between Naive RAG, Advanced RAG, and Modular RAG?

**Answer:**
- **Naive RAG**: Simple retrieve-then-generate pipeline. Our project starts here.
- **Advanced RAG**: Adds pre-retrieval optimization (query rewriting), post-retrieval processing (re-ranking, filtering), and chain-of-thought prompting.
- **Modular RAG**: Decomposes RAG into pluggable components (retriever, reranker, generator, router) that can be mixed and matched. Our LangGraph workflow is a step toward modular RAG with its classify → retrieve → generate → verify flow.

---

### Q5. What is hallucination in LLMs, and why is it dangerous for legal applications?

**Answer:** Hallucination is when an LLM generates plausible-sounding but factually incorrect or unsupported information. In legal applications, this is dangerous because:
- A fabricated clause could lead to wrong business decisions.
- Incorrect liability or penalty amounts could cause financial harm.
- Users might act on false information thinking it's from the actual document.
Our system mitigates this through strict prompts, groundedness verification, and explicit "Not found" fallback responses.

---

### Q6. How does your system handle hallucination?

**Answer:** Five layers of protection:
1. **Strict prompt engineering**: All prompts say "Answer ONLY from the provided context."
2. **Citation requirement**: LLM must cite [Source, Page, Chunk] for every claim.
3. **Word-overlap heuristic**: Quick check that answer words appear in the context.
4. **LLM-as-judge**: A second LLM call verifies the answer is grounded.
5. **Fallback**: If not grounded after 1 retry, return "Not found in the document."

---

### Q7. What is "LLM-as-judge"?

**Answer:** LLM-as-judge is a technique where we use the LLM itself to evaluate outputs. In our system, after generating an answer, we make a separate LLM call with the prompt: "Is this answer supported by the following context? Respond GROUNDED or NOT_GROUNDED." This is cheaper than human evaluation and more accurate than simple heuristics.

---

### Q8. What is grounding in the context of RAG?

**Answer:** Grounding means ensuring that every claim in the generated answer can be traced back to the source document. A "grounded" answer contains only information present in the retrieved context — nothing fabricated. We verify this through our dual-check mechanism (overlap + LLM verification).

---

## Section B: Embeddings & Vector Search (Q9-Q16)

### Q9. What are embeddings?

**Answer:** Embeddings are dense, fixed-length numerical vectors that capture the semantic meaning of text. Similar texts have vectors close together in the embedding space. For example, "termination clause" and "ending the agreement" would have similar embeddings even though they use different words. Our system uses 384-dimensional embeddings.

---

### Q10. Why did you choose all-MiniLM-L6-v2?

**Answer:**
- **Small size**: ~80 MB, runs efficiently on CPU.
- **Fast inference**: Suitable for real-time applications.
- **Good quality**: Trained on 1+ billion sentence pairs, performs well on semantic similarity benchmarks.
- **384 dimensions**: Good balance between quality and storage/computation.
- **Well-supported**: Integrated into LangChain via HuggingFaceEmbeddings.

---

### Q11. What is FAISS? Why not use a database like Pinecone or Weaviate?

**Answer:** FAISS (Facebook AI Similarity Search) is a library for efficient similarity search. We chose it because:
- **Local**: No server, no cloud dependency — just `pip install faiss-cpu`.
- **Fast**: Optimized C++ backend with Python bindings.
- **Simple**: Ideal for a project scope — no infrastructure management.
- **Offline**: Works without internet after initial setup.
Pinecone/Weaviate are better for production scale but add unnecessary complexity for a B.Tech project.

---

### Q12. How does similarity search work in FAISS?

**Answer:** When a query is submitted:
1. The query text is converted to a 384-d vector using the same embedding model.
2. FAISS computes the distance (L2 or cosine) between the query vector and every indexed vector.
3. The top-k vectors with the smallest distance (most similar) are returned.
4. The corresponding text chunks and metadata are retrieved from the docstore.
With normalized embeddings (as we use), L2 distance approximates cosine distance.

---

### Q13. What is cosine similarity vs L2 distance?

**Answer:**
- **Cosine similarity**: Measures the angle between two vectors. Range: [-1, 1]. Higher = more similar. Focuses on direction, not magnitude.
- **L2 (Euclidean) distance**: Measures the straight-line distance between vectors. Lower = more similar.
With L2-normalized vectors (magnitude = 1), the relationship is: L2² = 2(1 - cosine_similarity). So they give equivalent rankings when vectors are normalized, which is why we normalize our embeddings.

---

### Q14. What is the embedding dimension, and why does it matter?

**Answer:** Our model produces 384-dimensional vectors. Dimension matters because:
- **Higher dimensions** capture more semantic nuance but require more storage and computation.
- **Lower dimensions** are faster but may lose semantic detail.
- 384 is a sweet spot: models like all-MiniLM-L6-v2 achieve strong performance at this dimension.
- Each document chunk becomes a point in 384-dimensional space.

---

### Q15. How do you handle the first-time model download?

**Answer:** The sentence-transformer model is automatically downloaded from HuggingFace Hub on first use (~80 MB). It's cached in the user's local HuggingFace cache directory. Subsequent runs use the cached model. The UI shows a status message during the first download.

---

### Q16. Can embeddings capture legal terminology effectively?

**Answer:** The general-purpose all-MiniLM-L6-v2 captures semantic similarity reasonably well for legal text, since legal language still uses English sentence structures. However, it's not fine-tuned on legal corpora, so it may miss subtle legal distinctions (e.g., "indemnify" vs "hold harmless"). A future improvement would be using legal domain-specific embeddings.

---

## Section C: Chunking & Retrieval (Q17-Q22)

### Q17. Why do we chunk documents instead of embedding the entire document?

**Answer:**
1. **Token limits**: Embedding models have a max input length (typically 256-512 tokens).
2. **Precision**: Smaller chunks allow retrieval of specific, relevant passages rather than entire pages.
3. **LLM context window**: LLMs have limited context; sending only relevant chunks is more effective.
4. **Embedding quality**: Shorter texts produce more focused, meaningful embeddings.

---

### Q18. What is RecursiveCharacterTextSplitter?

**Answer:** It's a LangChain text splitter that recursively tries different separators in priority order: `\n\n` (paragraph) → `\n` (line) → `. ` (sentence) → ` ` (word) → `""` (character). It first tries to split at paragraph boundaries; if chunks are still too large, it tries line breaks, then sentences, and so on. This preserves natural text structure better than fixed-size splitting.

---

### Q19. Why use overlapping chunks?

**Answer:** Overlap ensures that sentences at chunk boundaries aren't lost. If a key sentence sits exactly at the boundary between two chunks, without overlap, it might be split across chunks and neither chunk would contain the complete sentence. With 150-character overlap, the end of chunk N overlaps with the start of chunk N+1, preserving boundary content.

---

### Q20. What is top-k retrieval? How did you choose k=5?

**Answer:** Top-k retrieval returns the k most similar chunks to the query. k=5 is a common default that balances:
- **Recall**: More chunks → more likely to include the relevant passage.
- **Precision**: Fewer chunks → less noise for the LLM.
- **Context window**: More chunks = more tokens for the LLM to process.
Our evaluation compares k=3 vs k=5 to find the optimal setting.

---

### Q21. How do you preserve chunk metadata for citations?

**Answer:** When documents are loaded, metadata (source filename, page number) is attached. During chunking, the splitter preserves this metadata and we add a sequential `chunk_id`. When the LLM generates an answer, we format citations as `[Source: filename, Page: N, Chunk: N]` using this metadata.

---

### Q22. What happens if the query is about something not in the document?

**Answer:** The pipeline handles this at multiple levels:
1. **Retrieval**: FAISS still returns top-k chunks, but they'll be semantically distant from the query.
2. **Prompt**: The LLM is instructed to say "Not found in the document" if the context doesn't contain the answer.
3. **Groundedness check**: If the LLM fabricates an answer anyway, the verifier flags it as NOT_GROUNDED.
4. **Fallback**: After a failed retry, the system returns a safe "Not found" message.

---

## Section D: LangChain & LangGraph (Q23-Q30)

### Q23. What is LangChain?

**Answer:** LangChain is an open-source framework for building applications with LLMs. It provides:
- **Document loaders**: Read PDF, DOCX, TXT, etc.
- **Text splitters**: Chunk documents.
- **Embeddings**: Interface to embedding models.
- **Vector stores**: Interface to FAISS, Pinecone, etc.
- **LLM wrappers**: Uniform interface to OpenAI, Gemini, Ollama, etc.
- **Prompt templates**: Parameterized prompts.
- **Output parsers**: Parse LLM output into structured data.

---

### Q24. What is LangGraph, and how is it different from LangChain?

**Answer:** LangGraph is built on top of LangChain for orchestrating multi-step workflows as graphs. Key differences:
- **LangChain**: Provides building blocks (loaders, splitters, LLM wrappers).
- **LangGraph**: Provides orchestration — connecting blocks into a stateful graph with conditional edges, loops, and retry logic.
In our project, LangChain handles individual operations; LangGraph orchestrates the classify → retrieve → generate → verify → retry flow.

---

### Q25. Explain your LangGraph StateGraph.

**Answer:** Our StateGraph has:
- **State**: A TypedDict with fields: query, task_type, retrieved_docs, context, answer, citations, grounded, retry_count, error.
- **Nodes**: classify_query, retrieve, generate, verify_grounding, rewrite_query, fallback.
- **Edges**: classify→retrieve→generate→verify (sequential), then conditional edges from verify: grounded→END, not grounded+retry<1→rewrite, not grounded+retry≥1→fallback.
- The state flows through each node, with each node updating specific fields.

---

### Q26. What are conditional edges in LangGraph?

**Answer:** Conditional edges route the workflow to different nodes based on a condition function. In our graph, after `verify_grounding`, a routing function checks:
- `grounded == True` → go to END
- `grounded == False and retry_count < 1` → go to rewrite_query (retry)
- `grounded == False and retry_count >= 1` → go to fallback
This enables dynamic branching without hardcoded paths.

---

### Q27. Why did you use keyword-based classification instead of LLM-based?

**Answer:**
1. **Speed**: Keyword matching is instantaneous; LLM classification adds 1-3 seconds.
2. **Reliability**: LLM classification can be inconsistent, especially with borderline queries.
3. **Cost**: Saves an API call per query.
4. **Simplicity**: Easy to understand, debug, and modify.
The trade-off is that ambiguous queries might be misclassified, but for well-defined legal analysis tasks, keywords work well.

---

### Q28. How does the provider-agnostic LLM factory work?

**Answer:** The `llm_factory.py` module reads `LLM_PROVIDER` from the `.env` file. Based on the value:
- `"gemini"` → creates a `ChatGoogleGenerativeAI` instance with the API key.
- `"ollama"` → creates a `ChatOllama` instance connecting to the local Ollama server.
Both return a LangChain `BaseChatModel`, so the rest of the code doesn't know or care which provider is being used. Switching providers requires only changing one line in `.env`.

---

### Q29. What is a prompt template, and why use one?

**Answer:** A prompt template is a parameterized string with placeholders (like `{context}` and `{query}`) that get filled at runtime. Benefits:
- **Consistency**: Every query uses the same instruction format.
- **Reusability**: Same template for different queries.
- **Maintainability**: Change the prompt in one place, affects all queries.
We have separate templates for summarization, Q&A, key clauses, and extraction, each with task-specific instructions and anti-hallucination rules.

---

### Q30. What are Pydantic output parsers?

**Answer:** Pydantic is a Python library for data validation using type annotations. In our project, we define Pydantic models like `DocumentExtraction` with typed fields (parties, obligations, deadlines, etc.). LangChain's output parsers can instruct the LLM to return JSON matching these schemas and then validate the output automatically. This gives us structured, type-safe extraction instead of raw text.

---

## Section E: Evaluation & Testing (Q31-Q36)

### Q31. How do you evaluate retrieval quality?

**Answer:** We measure **Hit-Rate@K**: for each test question, we check if at least one of the top-k retrieved chunks comes from the correct source document. A hit-rate of 1.0 means every question retrieved at least one relevant chunk. We test with k=3 and k=5 and compare performance.

---

### Q32. How do you evaluate answer correctness?

**Answer:** We use **keyword overlap**: we extract meaningful keywords from the expected answer and check what fraction appears in the generated answer. If >50% of keywords match, we consider the answer correct. For "not found" test cases, we check if the generated answer contains "not found." This is a simple heuristic — a more rigorous approach would use human evaluation or semantic similarity.

---

### Q33. What is the groundedness rate?

**Answer:** The groundedness rate is the fraction of generated answers that pass the groundedness verification check. A high groundedness rate means the system rarely hallucinates. Our system verifies groundedness using a dual approach: word-overlap heuristic + LLM-as-judge.

---

### Q34. What testing framework do you use?

**Answer:** We use **pytest**, the standard Python testing framework. We have 4 test files covering chunking, retrieval, graph routing, and Pydantic schemas. Tests are designed to run without an API key — the retriever tests create a small in-memory FAISS index, and the routing tests only test the classification logic.

---

### Q35. How are your tests designed to run without an API key?

**Answer:** 
- **Chunker tests**: Use hardcoded text, no external dependencies.
- **Retriever tests**: Create a small FAISS index with 5 test documents using the embedding model (local, no API needed).
- **Graph routing tests**: Only test the `classify_query` function (keyword matching) and `_route_after_grounding` (simple if/else logic).
- **Schema tests**: Test Pydantic model creation and validation — pure Python.

---

### Q36. Why not use RAGAS for evaluation?

**Answer:** RAGAS (Retrieval Augmented Generation Assessment) provides more sophisticated metrics (faithfulness, answer relevancy, context precision), but it requires additional dependencies and LLM calls for each evaluation. For our project scope, keyword-overlap and hit-rate provide meaningful insights. RAGAS integration is listed as a future enhancement.

---

## Section F: Architecture & Design (Q37-Q40)

### Q37. Why did you use the Singleton pattern for the embedding model and LLM?

**Answer:** Both the embedding model and LLM are expensive to initialize:
- Embedding model: ~80 MB load into memory.
- LLM: API connection setup and validation.
The Singleton pattern ensures they're loaded once and reused across all requests. Without it, each function call would reload the model, wasting time and memory.

---

### Q38. How does your system handle different document types?

**Answer:** We use format-specific loaders:
- **PDF**: `PyPDFLoader` from LangChain, which uses pypdf to extract text page-by-page.
- **DOCX**: Direct use of `python-docx` to extract paragraphs.
- **TXT**: `TextLoader` from LangChain with UTF-8 encoding.
The `load_document` function detects the file extension and dispatches to the correct loader. All loaders output LangChain `Document` objects with metadata.

---

### Q39. What happens if a user uploads a very large document?

**Answer:** The system handles it through chunking:
1. The document is split into ~1000-character chunks with 150-character overlap.
2. A 100-page PDF might produce 200+ chunks — all indexed in FAISS.
3. FAISS is designed for billion-scale search, so even thousands of chunks are trivial.
4. Only the top-k most relevant chunks are sent to the LLM, so the context window isn't overwhelmed.
The main bottleneck is embedding generation time, which scales linearly with document size.

---

### Q40. If you had to scale this system for a law firm with thousands of documents, what would you change?

**Answer:**
1. **Vector store**: Switch from FAISS (local) to a managed vector database like Pinecone, Weaviate, or Qdrant for concurrent access and persistence.
2. **Embedding**: Use batch processing and potentially GPU acceleration.
3. **LLM**: Use a dedicated API tier (not free) or self-hosted model for reliability and throughput.
4. **Authentication**: Add user login and document access control.
5. **Caching**: Cache frequent queries and their results.
6. **Document management**: Add metadata search, tagging, and version tracking.
7. **Deployment**: Containerize with Docker and deploy on cloud infrastructure.
