# Demo Script — PDF Analysis Chatbot (DocIntel AI)

This script provides a 5-minute demonstration script showcasing all key capabilities of the PDF Analysis Chatbot.

---

## Prerequisites
1. Backend running: `http://localhost:8000`
2. Frontend running: `http://localhost:3000` (or 3001)
3. Sample documents available in `samples/`

---

## Flow 1: Uploading & Stage 1 Visual Document Analysis

### Step 1: Drag-and-Drop Ingestion
- Open the web interface at `http://localhost:3000`.
- In the central dropzone, click **"1. Legal Contract"** or drag `sample_text_contract.pdf` into the dropzone.
- **What to observe**: The **Processing Timeline** activates live, stepping through:
  1. *Upload & File Security Validation*
  2. *Page Text & Coordinate Extraction (PyMuPDF)*
  3. *OCR Scan Verification*
  4. *Page-Aware Chunking & ChromaDB Indexing*
  5. *LLM Stage 1 Document Intelligence*

### Step 2: The Stage 1 Analysis Card
- Once indexing finishes, the UI transitions to the **Split-Screen Workspace**.
- On the **Right Panel**, review the schema-enforced **Analysis Card**:
  - **Header Badge**: Shows "Master Software Services Agreement", "Legal / Business Document", 2 Pages, and file size.
  - **Executive Summary**: 3-5 sentences outlining the agreement between Apex Global Technologies and NovaCloud Systems.
  - **Key Highlights**: Bullet points categorizing fees ($24,500/mo), termination terms, and IP ownership.
  - **Document Outline**: Clickable section headings (e.g. "Term and Termination", "Governing Law").
  - **Key Entities**: Chips identifying *Apex Global Technologies*, *NovaCloud Systems*, *$24,500 USD*, *San Francisco, CA*.
  - **Quality Audit**: Confirms "Digital Vector PDF with 98% confidence".

### Step 3: Interactive Outline Navigation
- On the Analysis Card, click **"Governing Law and Arbitration" (Page 2)**.
- **What to observe**: The left-hand PDF viewer instantly scrolls to Page 2.

---

## Flow 2: Stage 2 Grounded Chat & Citation Jumping

### Step 4: Ask a Clause-Specific Question
- Switch to the **Stage 2: Chat & Q&A** tab (or type into the input at the bottom).
- Enter:
  > *"What is the notice period required for termination without cause?"*
- **What to observe**:
  - The answer streams token-by-token in real time.
  - The answer explicitly cites the page: `...sixty (60) days prior written notice [p. 1].`
  - The **Sources Used** drawer displays Page 1 with an excerpt preview.

### Step 5: Citation Click-to-Highlight
- In the assistant's answer bubble, click the citation tag **`[p. 1]`**.
- **What to observe**:
  - The PDF viewer on the left immediately scrolls to **Page 1**.
  - A prominent **amber glowing bounding box** overlays the termination clause with the label: `Source Citation [p. 1]`.

### Step 6: Follow-Up Questions with Memory
- Notice the **3 Suggested Follow-Up Questions** generated at the bottom of the answer (e.g. *"What are the payment terms and fees?"*).
- Click one of the suggested chips.
- **What to observe**: The follow-up question executes immediately, demonstrating conversational context and grounded page citations.

---

## Flow 3: Tabular Extraction & Anti-Hallucination

### Step 7: Testing Tabular PDF
- Click **"Upload PDF"** in the top header.
- Select `sample_financial_tables.pdf`.
- Notice the **Detected Tables** section on the Analysis Card rendering real HTML tables with columns (Q1, Q2, Q3, YoY Growth).
- In Chat, ask: *"What was the YoY growth rate for AI Solutions in Q3 2024?"*
- Observe: Cites `[p. 1]` and outputs `+97.8%`.

### Step 8: Anti-Hallucination Negative Test
- In Chat, ask:
  > *"What color is the submarine mentioned in the contract?"*
- **What to observe**:
  - The system responds strictly:
    > *"This information is not found in the document."*
  - Zero hallucination or guesswork.

### Step 9: Export Report
- Click **"Export Report"** in the top navigation bar.
- A comprehensive Markdown file (`.md`) is downloaded containing the executive summary, key points, outline, entities, tables, and full Q&A chat transcript.
