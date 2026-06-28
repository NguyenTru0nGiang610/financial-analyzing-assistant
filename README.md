# FinNotebook — Financial Analyzing Assistant

A Retrieval-Augmented Generation (RAG) assistant for financial documents, with a
**NotebookLM-style** web interface. Upload financial PDFs (10-Ks, earnings
reports, consolidated statements), then ask questions and get answers **grounded
in your sources, with page-level citations**.

```
┌─────────────┬──────────────────────────────┬──────────────┐
│   Sources   │            Chat              │    Studio    │
│             │                              │              │
│  + Add PDF  │  Ask anything about your     │  Suggested   │
│  📑 10-K    │  documents — cited answers    │  questions   │
│  📑 Q4 ...  │  with collapsible citations   │  How it works│
└─────────────┴──────────────────────────────┴──────────────┘
```

---

## Features

- **NotebookLM-inspired UI** — three panels: **Sources** (upload & manage PDFs),
  **Chat** (grounded Q&A with citations), and **Studio** (one-click suggested
  questions tuned for financial reports).
- **Hybrid retrieval** — dense vector search (FAISS + `all-MiniLM-L6-v2`) fused
  with BM25 via Reciprocal Rank Fusion.
- **Cited answers** — every response can be expanded to show the source document,
  page number, and the retrieved text snippet.
- **Two RAG pipelines** — a custom pipeline and a LangChain-based pipeline,
  selectable per query (`/query`) and comparable side-by-side (`/query/compare`).
- **Confidence-aware prompting** — dynamic prompts and an optional web-search
  fallback when retrieval confidence is low.
- **MLOps** — experiment tracking with MLflow; an evaluation harness for
  retrieval and answer quality.
- **Session-based** — documents are indexed per session (1-hour TTL), so the API
  is multi-user friendly out of the box.

---

## Architecture

```
frontend/  (React + Vite)            rag_financial_assistant/  (Flask + RAG)
─────────────────────────            ──────────────────────────────────────
 Sources / Chat / Studio   ──HTTP──▶  api.py        REST API (/session, /upload,
 panels, citations                                  /query, /query/compare)
                                      ingestion/    PDF extract → chunk
                                      retrieval/    embeddings, FAISS, BM25
                                      rag/          pipelines, prompts, generator
                                      evaluation/   RAG & answer evaluation
                                      mlops/        MLflow tracking
```

**Request flow:** `GET /session` → `POST /upload` (extract → chunk → embed →
index into a per-session FAISS store) → `POST /query` (hybrid retrieve →
generate → return `answer` + cited `sources`).

---

## Quick start

### Option A — Docker (everything at once)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

### Option B — Run locally

**1. Backend**

```bash
cd rag_financial_assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python api.py            # serves http://localhost:8000
```

**2. Frontend** (in a second terminal)

```bash
cd frontend
npm install
npm run dev              # serves http://localhost:5173
```

Then open http://localhost:5173, click **➕ Add source**, upload a financial PDF,
and start asking questions.

> The frontend talks to `http://localhost:8000` by default. Override it with a
> `VITE_API_URL` environment variable when building/serving the frontend.

---

## Using the assistant

1. **Add a source** — upload a PDF in the left panel. It is parsed, chunked,
   embedded, and indexed for your session.
2. **Ask a question** — type in the Chat panel, or click a prompt in the Studio
   panel (e.g. *“What was total revenue and how did it change year over year?”*).
3. **Check citations** — expand the **citations** under any answer to see the
   exact source document, page, and supporting text.

### CLI (no UI)

```bash
cd rag_financial_assistant
python cli.py
```

---

## API reference

Base URL: `http://localhost:8000`

| Method | Endpoint         | Description                                                |
| ------ | ---------------- | --------------------------------------------------------- |
| `GET`  | `/`              | Health check.                                             |
| `GET`  | `/session`       | Create a session, returns `{ "session_id": "..." }`.      |
| `POST` | `/upload`        | Upload a PDF. Query param `session_id`, body `file`.      |
| `POST` | `/query`         | Ask a question. Body below.                               |
| `POST` | `/query/compare` | Run both pipelines and compare answers.                   |

**`POST /query` request**

```json
{
  "session_id": "…",
  "query": "What was total revenue in FY24?",
  "pipeline": "langchain"   // or "custom"
}
```

**`POST /query` response**

```json
{
  "answer": "…",
  "sources": [{ "source": "NASDAQ_TSLA_2024.pdf", "page": 12, "text": "…" }],
  "pipeline": "langchain"
}
```

---

## Configuration

Backend behavior is controlled by `rag_financial_assistant/config.yaml`:

| Key                         | Meaning                                          |
| --------------------------- | ------------------------------------------------ |
| `embedding_model`           | Sentence-Transformers model (`all-MiniLM-L6-v2`).|
| `chunk_size` / `chunk_overlap` | Chunking parameters.                          |
| `retrieval.score_type`      | `hybrid_rrf` (vector + BM25 fusion).             |
| `retrieval.vector_weight` / `bm25_weight` | Fusion weights.                    |
| `rag.score_threshold`       | Below this, trigger the web-search fallback.     |
| `rag.*_confidence_threshold`| Thresholds for answer confidence labelling.      |
| `mlflow.tracking_uri`       | MLflow tracking backend.                         |

LLM/generation settings live in `config_langchain.yaml` and the `rag/` modules.

---

## Project layout

```
financial-analyzing-assistant/
├── docker-compose.yaml          # frontend + backend
├── frontend/                    # React + Vite (NotebookLM-style UI)
│   └── src/
│       ├── App.jsx              # 3-panel workspace shell
│       ├── api.jsx              # API client
│       └── components/
│           ├── SourcesPanel.jsx # upload & list sources
│           ├── Chat.jsx         # conversation
│           ├── Message.jsx      # markdown + citations
│           └── StudioPanel.jsx  # suggested questions
└── rag_financial_assistant/     # Flask API + RAG engine
    ├── api.py                   # REST endpoints
    ├── cli.py                   # terminal interface
    ├── config.yaml              # main config
    ├── ingestion/               # PDF extraction & chunking
    ├── retrieval/               # embeddings, FAISS, BM25
    ├── rag/                     # pipelines, prompts, generator
    ├── evaluation/              # RAG & answer evaluation
    └── mlops/                   # MLflow tracking
```

---

## Evaluation

```bash
cd rag_financial_assistant
python run_evaluation.py
```

Results are written to `evaluation/results/` and metrics are logged to MLflow
(`sqlite:///mlflow.db`). Launch the MLflow UI with:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

---

## Tech stack

**Frontend:** React 18, Vite, plain CSS (no UI framework, zero extra deps).
**Backend:** Flask, FAISS, Sentence-Transformers, LangChain, BM25, MLflow,
PyMuPDF/pypdf.

## License

See [LICENSE](LICENSE).
