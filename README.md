# 🧭 CodeCompass AI

CodeCompass AI turns an unfamiliar codebase into something you can talk to. Upload a repository as a ZIP, and it runs a full pipeline — tree-sitter AST parsing, semantic chunking, vector embedding, and a grounded RAG chat — so you can ask real questions about the code and get answers backed by cited source snippets instead of hallucinated guesses.

The interesting engineering is in the pipeline reliability: AST-aware parsing instead of naive line splitting, a three-provider LLM fallback chain so a single rate limit doesn't take down chat, and a Docker build that doesn't ship gigabytes of unused CUDA wheels.

---

## Technical Highlights

- **AST-aware code chunking** — uses tree-sitter (not regex or fixed-size splitting) to parse source files into a syntax tree and chunk along function/class boundaries across multiple languages, so retrieved snippets are always syntactically coherent rather than cut mid-block.
- **Multi-provider LLM fallback chain** — chat requests try Groq first, fall back to Gemini, then OpenAI, with explicit 429/rate-limit detection at each hop. A key outage or quota exhaustion on one provider degrades gracefully instead of breaking chat.
- **CPU-optimized Docker build** — the backend Dockerfile installs `torch` from the CPU-only PyTorch wheel index *before* `requirements.txt`, avoiding a multi-gigabyte CUDA dependency pull for a container that never touches a GPU.
- **Grounded RAG with citations and conversation memory** — answers are constrained to retrieved chunks with file-path and line-range citations attached, and recent conversation turns are passed into the prompt so follow-up questions resolve pronouns and context correctly.
- **Similarity-filtered retrieval** — low-relevance chunks are dropped below a similarity threshold before being sent to the LLM, so a sparse or unrelated index produces an honest "can't find that" instead of a confident wrong answer.
- **Guest access mode** — a one-click guest login skips registration entirely, so a reviewer can try the full upload → index → chat pipeline in under a minute.

---

## Tech Stack

**Backend:** FastAPI, SQLAlchemy (async) + Alembic, PostgreSQL, ChromaDB (vector store), tree-sitter, sentence-transformers, httpx

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, Axios, Framer Motion

**Infrastructure:** Docker Compose (Postgres + FastAPI + Nginx-served SPA), Nginx as reverse proxy

---

## Project Structure

```
Code Compass/
├── backend/               # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/routes/ # API Endpoints
│   │   ├── core/          # Settings Configuration
│   │   ├── db/            # Database Session (Phase 2+)
│   │   ├── models/        # SQLAlchemy Models (Phase 2+)
│   │   ├── schemas/       # Request/Response validation (Phase 2+)
│   │   ├── services/      # Business Logic (Phase 2+)
│   │   └── main.py        # FastAPI Entry Point
│   ├── requirements.txt
│   └── .env.example
├── frontend/              # React + Vite + TS Frontend
│   └── .env.example
├── .gitignore
└── README.md
```

---

## Setup Instructions

### 1. Backend Setup
1. Navigate to `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment config and populate values:
   ```bash
   cp .env.example .env
   ```
5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
   * Access API Docs at: http://localhost:8000/docs
   * Access health check endpoint at: http://localhost:8000/api/v1/health

### 2. Frontend Setup
1. Navigate to `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Start the dev server:
   ```bash
   npm run dev
   ```
   * Access client application at: http://localhost:5173

---

## Docker Setup Instructions

You can spin up the entire production stack (FastAPI Backend, Nginx-served SPA Frontend, and PostgreSQL Database) inside container networks with persistent storage volumes using a single Docker Compose command.

### 1. Requirements
Ensure you have **Docker** and **Docker Compose** installed on your system.

### 2. Configure Environment Secrets
Set at least one LLM provider key — `GROQ_API_KEY`, `GEMINI_API_KEY`, or `OPENAI_API_KEY` — exported in your host terminal shell:
```bash
export GROQ_API_KEY="gsk_...your_key"
```
Or define them inside the local `backend/.env` file. Chat tries Groq first, then Gemini, then OpenAI, so configuring more than one gives you automatic fallback if a provider is rate-limited.

### 3. Spin up the Containers
From the root project directory, run:
```bash
docker compose up --build
```

- **Frontend Application:** Available at `http://localhost:5173`
- **Backend API Server:** Available at `http://localhost:8000`
- **Interactive OpenAPI Documentation:** Available at `http://localhost:8000/docs`
- **Health Check Endpoint:** Available at `http://localhost:8000/health`

### 4. Stopping the containers
To stop the stack and keep volume state intact:
```bash
docker compose down
```

To stop and wipe database/workspace volumes:
```bash
docker compose down -v
```

---

## Known Limitations

- **Broad queries**: Very generic questions (e.g. "what does this do") are recall-optimized using heuristics (README/entry-point files are always included), but highly specific follow-up questions will generally get more precise, better-grounded answers than open-ended ones.
- **Conversation memory is session-local**: Recent turns are passed to the LLM per-request from the frontend (not persisted server-side), and the browser only keeps chat history in `localStorage`, so context doesn't sync across devices or browsers.
- **Free-tier LLM providers**: Chat automatically falls back across Groq → Gemini → OpenAI depending on which API keys are configured and current rate-limit status.
- **Chunk relevance filtering**: Low-similarity matches are filtered out of retrieval results, so if a repository has sparse or unclear indexing for a topic, the assistant may say it can't find relevant information rather than guessing from a weak match.
