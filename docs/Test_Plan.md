# Test Plan — RAG-Based AI Legal Document Analyzer

---

## 1. Test Strategy

### 1.1 Scope

| In Scope | Out of Scope |
|----------|-------------|
| Chunking module | UI visual testing |
| Retrieval module | Load/performance testing |
| Query classification/routing | Cross-browser testing |
| Pydantic schema validation | Security testing |
| End-to-end CLI pipeline | LLM response quality (subjective) |

### 1.2 Test Levels

| Level | Tools | Description |
|-------|-------|-------------|
| Unit Testing | pytest | Test individual functions in isolation |
| Integration Testing | pytest + FAISS | Test module interactions (retriever + FAISS) |
| System Testing | Manual CLI | End-to-end pipeline on sample documents |

### 1.3 Test Environment

- **Python**: 3.10+
- **Framework**: pytest 8.3.4
- **OS**: Windows 10/11
- **Dependencies**: As per requirements.txt
- **LLM**: Not required for unit/integration tests

---

## 2. Test Cases

### 2.1 Chunker Module (test_chunker.py)

| TC-ID | Test Case | Input | Expected Result | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-01 | Create chunks from documents | Multi-section legal text | Multiple chunks created | High |
| TC-02 | Chunk size respected | Text with chunk_size=300 | Each chunk ≤ 400 chars (with tolerance) | High |
| TC-03 | Chunk ID assigned | Any document | Each chunk has unique chunk_id | High |
| TC-04 | Source metadata preserved | Doc with source="test.txt" | All chunks have source="test.txt" | High |
| TC-05 | Page metadata preserved | Doc with page=1 | All chunks have page metadata | Medium |
| TC-06 | Empty input handling | Empty document list | Returns empty list | Medium |
| TC-07 | Single short document | "Short sentence." | Returns exactly 1 chunk | Medium |
| TC-08 | Custom chunk size | Same text, sizes 150 vs 500 | Smaller size → more chunks | Medium |
| TC-09 | Overlap creates shared content | Text with overlap=50 | Adjacent chunks share words | Medium |
| TC-10 | Chunk summary statistics | Multiple chunks | Correct total, avg, min, max | Low |

### 2.2 Retriever Module (test_retriever.py)

| TC-ID | Test Case | Input | Expected Result | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-11 | Returns correct k results | top_k=3 | Exactly 3 documents | High |
| TC-12 | Handles k > total docs | top_k=10, 5 docs | Returns 5 documents | High |
| TC-13 | Results have metadata | Query about rent | source and chunk_id present | High |
| TC-14 | Relevant results ranked first | "monthly rent payment" | Top result is about rent | High |
| TC-15 | Empty query returns empty | "" | Empty list | Medium |
| TC-16 | Whitespace query returns empty | "   " | Empty list | Medium |
| TC-17 | Score-based retrieval | "arbitration" | Returns (Document, float) tuples | Medium |
| TC-18 | Scores non-negative | Any query | All scores ≥ 0 | Medium |
| TC-19 | Context formatting | Retrieved docs | Includes [Source:] headers and separators | Medium |

### 2.3 Graph Routing Module (test_graph_routing.py)

| TC-ID | Test Case | Input | Expected Result | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-20 | Classify "summarize" | "Summarize this document" | task_type = "summarize" | High |
| TC-21 | Classify "summarize" variant | "Give me an overview" | task_type = "summarize" | High |
| TC-22 | Classify "key_clauses" | "Identify key clauses" | task_type = "key_clauses" | High |
| TC-23 | Classify "key_clauses" keyword | "What about termination?" | task_type = "key_clauses" | High |
| TC-24 | Classify "extract_obligations" | "Extract all obligations" | task_type = "extract_obligations" | High |
| TC-25 | Classify "qa" (default) | "How much is the rent?" | task_type = "qa" | High |
| TC-26 | Case insensitive | "SUMMARIZE THIS" | task_type = "summarize" | Medium |
| TC-27 | Route: grounded → end | grounded=True | Returns "end" | High |
| TC-28 | Route: not grounded → retry | grounded=False, retry=0 | Returns "retry" | High |
| TC-29 | Route: not grounded after retry → fallback | grounded=False, retry=1 | Returns "fallback" | High |

### 2.4 Schema Validation Module (test_schemas.py)

| TC-ID | Test Case | Input | Expected Result | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-30 | Valid PartyInfo | name, role, address | Object created | High |
| TC-31 | Optional address | name, role only | address is None | Medium |
| TC-32 | Missing required field | name only (no role) | ValidationError raised | High |
| TC-33 | Valid Obligation | party, obligation, section | Object created | High |
| TC-34 | Valid Condition | condition, consequence | Object created | Medium |
| TC-35 | Valid Deadline | deadline, related_to | Object created | Medium |
| TC-36 | Valid Penalty | penalty, trigger, amount | Object created | Medium |
| TC-37 | Valid FinancialTerm | description, amount | Object created | Medium |
| TC-38 | Valid KeyClause | clause_type, summary | Object created | Medium |
| TC-39 | Valid Citation | source only | page/chunk_id are None | Medium |
| TC-40 | Empty DocumentExtraction | No arguments | All lists empty | Medium |
| TC-41 | Full DocumentExtraction | Nested models | All fields populated | Medium |
| TC-42 | Valid AnalysisResult | task_type, answer | Disclaimer present | High |
| TC-43 | Default disclaimer | No explicit disclaimer | Contains "not a substitute" | Medium |

---

## 3. End-to-End Test Cases (Manual)

| TC-ID | Test Case | Steps | Expected Result |
|-------|-----------|-------|-----------------|
| E2E-01 | CLI ingest sample docs | `python main.py ingest --sample` | Success message, vector store created |
| E2E-02 | CLI question answering | `python main.py query -q "What is the rent?"` | Answer with citation, disclaimer |
| E2E-03 | CLI summarization | `python main.py query -q "summary" -t summarize` | Document summary displayed |
| E2E-04 | Streamlit upload and process | Upload TXT file, click Process | Stats shown in sidebar |
| E2E-05 | Streamlit Q&A | Enter question, press Enter | Answer displayed with groundedness |
| E2E-06 | Streamlit quick actions | Click "Key Clauses" | Key clauses identified |
| E2E-07 | Anti-hallucination test | Ask "What color is the office carpet?" | "Not found in the document" |

---

## 4. Test Execution Schedule

| Phase | Tests | When |
|-------|-------|------|
| Development | Unit tests (TC-01 to TC-43) | During module development |
| Integration | Retriever + FAISS (TC-11 to TC-19) | After embeddings module complete |
| System | E2E tests (E2E-01 to E2E-07) | After full pipeline assembled |
| Regression | All tests | Before final submission |

---

## 5. Pass/Fail Criteria

- **Unit Tests**: All 43 test cases must pass (`pytest tests/ -v` exits with code 0).
- **Integration Tests**: Retriever returns relevant results from the FAISS index.
- **E2E Tests**: All 7 end-to-end scenarios produce expected outputs.
- **No critical bugs**: No crashes, unhandled exceptions, or data loss.
