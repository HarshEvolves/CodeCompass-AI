# 🧭 CodeCompass AI

An AI-powered codebase explorer that helps developers understand unfamiliar codebases using RAG (Retrieval-Augmented Generation).

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
