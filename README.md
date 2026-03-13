# LexCorp Legal Assistant

> An AI-powered legal information chatbot for LexCorp Law Firm — built with RAG (Retrieval-Augmented Generation) to answer questions grounded strictly in firm documentation.

---

## Overview

LexCorp Legal Assistant is a full-stack RAG application that allows lawyers and staff to query the firm's internal constitution and policy documents through a natural language chat interface. The system retrieves only what is documented, cites its sources on every answer, and refuses to speculate — making it safe and auditable for a legal environment.

When the system does not have enough information to answer, it responds with:

> *"I don't have enough information to answer that. Please consult a lawyer directly."*

---

## Pipeline

```
PDF Document
     │
     ▼
┌─────────────────────────────────┐
│  INGESTION  (runs once)         │
│                                 │
│  pdfplumber  → extract tables   │
│  PyMuPDF     → extract text     │
│  regex       → detect structure │
│              (PART / Section /  │
│               Rule headings)    │
│                                 │
│  Clean HTML tags, bullet chars  │
│                                 │
│  SentenceTransformer → embed    │
│  (all-MiniLM-L6-v2, 384-dim)   │
│                                 │
│  Qdrant → store vectors + meta  │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  QUERY  (runs on every message) │
│                                 │
│  User message                   │
│       │                         │
│  Intent detection               │
│  (greeting / query)             │
│       │                         │
│  Query rewriting                │
│  (resolve follow-up questions)  │
│       │                         │
│  Embed query → vector           │
│       │                         │
│  Qdrant cosine similarity search│
│  top-k=4, threshold=0.2         │
│       │                         │
│  No results → fallback response │
│       │                         │
│  Build prompt with context      │
│  + conversation history         │
│       │                         │
│  Groq LLM → answer + citations  │
└─────────────────────────────────┘
     │
     ▼
  JSON response
  { answer, sources, found }
```

---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|---|---|---|
| API server | FastAPI + Uvicorn | REST API, CORS |
| PDF parsing | PyMuPDF (fitz) | Text + font metadata extraction |
| Table extraction | pdfplumber | Structured table parsing |
| Embedding model | `all-MiniLM-L6-v2` | Local sentence embeddings (384-dim) |
| Vector database | Qdrant (local) | Vector storage + similarity search |
| LLM | Llama 3.3 70B (via Groq) | Answer generation |
| Inference provider | Groq Cloud | Fast LPU-based inference, free tier |
| Environment | python-dotenv | API key management |

### Frontend
| Component | Technology |
|---|---|
| Framework | React |
| Styling | Tailwind CSS |
| HTTP client | Axios |
| Build tool | Vite |

---

## Models

| Model | Type | Where it runs | Purpose |
|---|---|---|---|
| `all-MiniLM-L6-v2` | Sentence Transformer | Local (CPU) | Embeds document chunks and user queries into 384-dimensional vectors |
| `llama-3.3-70b-versatile` | Large Language Model | Groq Cloud | Synthesizes retrieved context into a coherent, cited answer |

The embedding model runs entirely locally — no data is sent externally during ingestion or retrieval. Only the final prompt (context + question) is sent to Groq for answer generation.

---

## Project Structure

```
lexcorp-legal-rag/
│
├── backend/
│   ├── main.py           # FastAPI app + API routes
│   ├── chat.py           # Prompt building + Groq LLM call
│   ├── retriever.py      # Qdrant vector search + citation formatting
│   ├── ingest.py         # PDF parsing, chunking, embedding, upload
│   ├── qdrant_data/      # Local vector database (auto-generated)
│   └── .env              # GROQ_API_KEY (never commit)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main chat UI
│   │   ├── ChatMessage.jsx
│   │   └── api.js        # Axios API calls
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── data/
│   └── LexCorp_Law.pdf   # AI-generated sample legal document (42 pages)
│
├── .gitignore
└── requirements.txt
```

---

## Sample Document

The file `data/LexCorp_Law.pdf` is a **42-page AI-generated legal document** created specifically for this project to simulate a real law firm's internal constitution. It was generated using an LLM and contains realistic firm governance policies, professional responsibility rules, billing regulations, client intake procedures, employment law, and more — structured with parts, numbered sections, clauses, and tables exactly as a real firm document would be.

It is used purely for demonstration purposes. To use this system with a real document, replace `LexCorp_Law.pdf` with your own PDF and re-run `ingest.py`.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free [Groq API key](https://console.groq.com)

---

### 1. Clone the repository

```bash
git clone https://github.com/sarimahsan/lexcorp-legal-rag.git
cd lexcorp-legal-rag
```

### 2. Set up Python environment

```bash
cd backend
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
# create .env file in backend/
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

Get your free API key at [console.groq.com](https://console.groq.com) — no credit card required.

### 4. Ingest the document

Run this once to parse the PDF, generate embeddings, and populate the vector database:

```bash
python3 ingest.py
```

Expected output:
```
Parsing PDF...
  95 chunks extracted
  Parts: ['PART I: FIRM GOVERNANCE...', 'PART II: ...']
  Sections: 40+
  Tables: 6

Embedding chunks...
  Batches: 100%|████████| 3/3

Uploading to Qdrant...

Done. 95 vectors stored in 'qdrant_data/'
```

### 5. Start the backend

```bash
python3 main.py
```

Server runs at `http://localhost:8000`

### 6. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## API Reference

### `POST /chat`

Send a user message and receive a grounded answer with citations.

**Request:**
```json
{
  "message": "What is the billing rate for a Senior Associate?",
  "history": []
}
```

**Response:**
```json
{
  "answer": "According to Section 1.3.2 (Page 3), the billing rate for a Senior Associate (7+ years) is $475/hr, with a range of $425–$550, effective January 1, 2024.",
  "sources": [
    "1.3.2 Standard Hourly Rate Bands | PART I: FIRM GOVERNANCE | Page 3"
  ],
  "found": true
}
```

**Fallback response (when context is insufficient):**
```json
{
  "answer": "I don't have enough information to answer that. Please consult a lawyer directly.",
  "sources": [],
  "found": false
}
```

### `GET /health`

```json
{ "status": "ok" }
```

---

## Key Design Decisions

**Why RAG and not fine-tuning?**
The document changes over time. RAG means updating the knowledge base is as simple as re-running `ingest.py` with a new PDF — no retraining required.

**Why Qdrant over FAISS or ChromaDB?**
Qdrant persists metadata alongside vectors natively, supports payload filtering for future multi-document support, and is production-grade tooling used in real AI engineering roles.

**Why local embeddings?**
`all-MiniLM-L6-v2` runs on CPU with no API cost. For a law firm where document confidentiality matters, embeddings never leave the machine.

**Why a score threshold?**
Setting `score_threshold=0.2` means the retriever returns nothing — and the bot says "I don't know" — rather than hallucinating an answer from loosely related chunks. This is critical for a legal context.

---

## requirements.txt

```
fastapi
uvicorn
pdfplumber
pymupdf
sentence-transformers
qdrant-client
groq
python-dotenv
pydantic
```


## Author

**Syed Sarim Ahsan**

---

> Built as a real-world AI engineering project demonstrating RAG architecture, vector search, and LLM integration for domain-specific document Q&A.