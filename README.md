# Intelli-Credit Copilot

Monorepo implementation of the Intelli-Credit underwriting workflow described in `BUILD_SPEC.md`.

## What is included

- `backend/`: FastAPI API, async SQLAlchemy models, document pipeline, schema-guided extraction, research, Five Cs scoring, recommendation engine, CAM generation, DOCX/PDF export
- `frontend/`: Next.js 14 App Router workbench for onboarding, upload, classification, extraction review, schema editing, analysis, and report preview/download
- `backend/tests/`: sample-document regression tests using the provided Aavas Financiers PDFs
- `backend/app/services/runtime/`: fast native document runtime with geometry capture, candidate-page retrieval, agentic fallback extraction, and Docling adapter benchmarks

## Runtime notes

- LLM integration uses **Gemini**, not Claude.
- Digital PDFs are processed locally with PyMuPDF + pdfplumber.
- Complex scanned pages use LandingAI when configured, otherwise fall back to Gemini vision when `GEMINI_API_KEY` is set.
- Storage defaults to local filesystem under `backend/storage/`.
- Database defaults to local SQLite via `aiosqlite`, but `DATABASE_URL` can point to PostgreSQL/Supabase.

## Setup

### Backend

```bash
cp backend/.env.example backend/.env
python3 -m pip install -e ./backend
uvicorn backend.app.main:app --reload
```

### Frontend

```bash
cp frontend/.env.local.example frontend/.env.local
cd frontend
npm install
npm run dev
```

## Verification

Backend regression tests:

```bash
python3 -m pytest backend/tests -q
```

Frontend production build:

```bash
cd frontend
npm run build
```

Fast runtime benchmark against Docling:

```bash
python3 scripts/compare_fast_runtime_vs_docling.py --company aavas --workers 8
python3 scripts/compare_fast_runtime_vs_docling.py --company home --workers 8
```

## Key routes

- `http://localhost:3000/` dashboard
- `http://localhost:3000/onboarding` new case onboarding
- `http://localhost:8000/docs` FastAPI OpenAPI docs
- `http://localhost:8000/health` API health
