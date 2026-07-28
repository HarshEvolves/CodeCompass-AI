# 🧭 CodeCompass

**AI-powered codebase explorer** — upload a repository, ask questions in plain English, and get answers grounded in your actual code.

---

## Tech Stack

| Layer    | Technologies                                      |
|----------|---------------------------------------------------|
| Frontend | React · TypeScript · Tailwind CSS v4 · Vite       |
| Backend  | FastAPI · Pydantic                                 |
| AI *(coming)* | Tree-sitter · ChromaDB · Sentence Transformers · Gemini |

---

## Quick Start

### Prerequisites

- **Python 3.12+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)

### 1. Clone the project

```bash
git clone https://github.com/YOUR_USERNAME/codecompass.git
cd codecompass
```

### 2. Start the Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env

# Start the server (auto-reloads on code changes)
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**
API docs at **http://localhost:8000/docs**

### 3. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:5173**

### 4. Verify it works

Open **http://localhost:5173** in your browser.
The landing page should show a green **"✓ healthy"** status in the System Status card.

You can also test the API directly:

```bash
curl http://localhost:8000/api/v1/health
# → {"status":"healthy","app":"CodeCompass","version":"1.0.0"}
```

---

## Project Structure

```
Code Compass/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/   # API endpoint handlers
│   │   ├── core/            # Config and settings
│   │   ├── db/              # Database (Phase 2+)
│   │   ├── models/          # ORM models (Phase 2+)
│   │   ├── schemas/         # Request/response schemas (Phase 2+)
│   │   ├── services/        # Business logic (Phase 2+)
│   │   ├── utils/           # Helper functions
│   │   └── main.py          # App entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── lib/             # Axios client, shared configs
│   │   ├── pages/           # Page components
│   │   ├── App.tsx          # Root component
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Tailwind + global styles
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
├── .gitignore
└── README.md
```

---

## Current Phase

✅ **Phase 1** — Project Scaffolding & Foundation

---

## License

MIT
