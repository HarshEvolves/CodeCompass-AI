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

---

## Docker Setup Instructions

You can spin up the entire production stack (FastAPI Backend, Nginx-served SPA Frontend, and PostgreSQL Database) inside container networks with persistent storage volumes using a single Docker Compose command.

### 1. Requirements
Ensure you have **Docker** and **Docker Compose** installed on your system.

### 2. Configure Environment Secrets
Make sure `GEMINI_API_KEY` or `OPENAI_API_KEY` is exported in your host terminal shell:
```bash
export GEMINI_API_KEY="AIzaSy...your_key"
```
Or define them inside the local `backend/.env` file.

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
