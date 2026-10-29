# User Manual — RAG-Based AI Legal Document Analyzer

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Using the Streamlit Web Interface](#4-using-the-streamlit-web-interface)
5. [Using the CLI](#5-using-the-cli)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. System Requirements

| Requirement | Specification |
|-------------|--------------|
| Python | 3.10 or higher |
| RAM | 4 GB minimum, 8 GB recommended |
| Disk Space | 2 GB (includes model download) |
| Internet | Required for Google Gemini API and first-time model download |
| OS | Windows 10/11, Linux, macOS |

---

## 2. Installation

### Step 1: Navigate to the project directory

```bash
cd legal-rag-analyzer
```

### Step 2: Create and activate a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

> **Note**: The first run will download the embedding model (~80 MB). This is automatic and happens once.

---

## 3. Configuration

### Step 1: Create the environment file

```bash
copy .env.example .env
```

### Step 2: Get a Google Gemini API key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

### Step 3: Add the key to `.env`

Open `.env` in a text editor and replace `your-google-api-key-here` with your actual API key:

```
GOOGLE_API_KEY=AIzaSyA...your-actual-key...
```

### Optional: Use Ollama (Local LLM)

If you prefer a local LLM instead of Gemini:

1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull llama3.2`
3. Update `.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   ```

---

## 4. Using the Streamlit Web Interface

### Launch the app

```bash
streamlit run ui/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`.

### Step 1: Upload a Document

1. In the left sidebar, click **"Browse files"** under "Document Upload"
2. Select one or more legal documents (PDF, DOCX, or TXT)
3. Click **"🔄 Process Documents"**
4. Wait for processing to complete (progress is shown in the sidebar)

*[Screenshot placeholder: Document upload sidebar]*

### Step 2: Use Quick Actions

After processing, four quick action buttons appear:

| Button | Action |
|--------|--------|
| 📝 **Summarize** | Generate a comprehensive summary of the document |
| 🔑 **Key Clauses** | Identify all key legal clauses |
| 📋 **Extract Info** | Extract obligations, deadlines, penalties as structured data |
| 🗑️ **Clear History** | Clear the analysis history |

*[Screenshot placeholder: Quick action buttons]*

### Step 3: Ask Custom Questions

Type any question in the input box, e.g.:
- "What is the termination notice period?"
- "How much is the security deposit?"
- "What are the payment terms?"

*[Screenshot placeholder: Query input and results]*

### Step 4: Review Results

Each result displays:
- **Answer**: The AI-generated response grounded in the document
- **Citations**: References to the specific document chunks used
- **Groundedness Status**: ✅ Grounded or ❌ Not Grounded
- **Disclaimer**: Reminder that this is not legal advice

*[Screenshot placeholder: Result display with citations]*

---

## 5. Using the CLI

### Ingest Sample Documents

```bash
python main.py ingest --sample
```

### Ingest Specific Files

```bash
python main.py ingest --files path/to/contract.pdf path/to/nda.txt
```

### Ask a Question

```bash
python main.py query --question "What is the termination clause?"
```

### Force a Specific Task Type

```bash
# Summarize
python main.py query --question "Summarize this document" --task summarize

# Key clauses
python main.py query --question "Key clauses" --task key_clauses

# Extract obligations
python main.py query --question "Extract obligations" --task extract_obligations
```

### View Help

```bash
python main.py --help
python main.py ingest --help
python main.py query --help
```

---

## 6. Troubleshooting

### "GOOGLE_API_KEY not found"
- Ensure you have created a `.env` file (copy from `.env.example`)
- Verify the API key is correctly set without quotes around the value

### "No vector store found"
- Run `python main.py ingest --sample` first to index documents
- In the Streamlit app, upload and process documents before querying

### "No text extracted"
- The PDF may be a scanned image without embedded text
- Try converting the PDF to a text-based format first

### Slow first run
- The embedding model (~80 MB) downloads on first use
- Subsequent runs use the cached model and are faster

### "Rate limit exceeded" (Gemini)
- The free tier has usage limits
- Wait a minute and try again, or switch to Ollama

### Import errors
- Ensure the virtual environment is activated
- Run `pip install -r requirements.txt` again
