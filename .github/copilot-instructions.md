<!-- .github/copilot-instructions.md - guidance for AI coding agents working on this repo -->
# Dining-bot — Copilot instructions

Purpose: short, actionable notes to help AI agents be productive in this repo.

- **Big picture**: This repo is a two-part app: a Python FastAPI backend (backend/) that implements retrieval-augmented chat and a Next.js frontend (frontend/) that proxies UI requests to the backend. The backend performs scraping, retrieval, and RAG in `backend/app/core/*`. The frontend uses edge API routes to stream text to client components and uses Supabase for auth/storage.

- **Service boundaries**:
  - Backend: `backend/app/main.py` exposes FastAPI routes under `/api/*`. Key routers: `test`, `chat`, `users` (see `backend/app/api/routes/`).
  - Frontend: Next.js app in `frontend/app/*`. Edge route `frontend/app/api/ai-chat/route.ts` forwards streaming chat to `http://localhost:8000/api/chat` (configurable via `BACKEND_URL`).

- **Where to look first**:
  - Backend entry: `backend/app/main.py` (CORS, routers)
  - Backend config: `backend/app/core/config.py` (loads `backend/.env`, `OPENAI_API_KEY`, `DATABASE_URL`)
  - Chat flow: `backend/app/api/routes/chat.py` -> `backend/app/core/rag.py` (streaming generator) -> `backend/app/core/retrieval.py` / `scraper.py`
  - Frontend edge route: `frontend/app/api/ai-chat/route.ts` (sends `prompt` -> backend `query`, returns raw text stream)
  - Supabase client: `frontend/lib/supabase/client.ts` (expects `NEXT_PUBLIC_SUPABASE_*` env vars)

- **Dev workflows / run commands** (verified from repo files):
  - Backend: create a Python venv, install `backend/requirements.txt`, run:

    ```bash
    cd backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

  - Frontend: install and run Next.js:

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

- **Important env vars & locations**:
  - Backend `.env` (loaded by `backend/app/core/config.py`): `DATABASE_URL`, `OPENAI_API_KEY`.
  - Frontend: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, optional `BACKEND_URL` (defaults to `http://localhost:8000/api/chat` in `frontend/app/api/ai-chat/route.ts`).

- **Project-specific conventions & patterns**:
  - Streaming-first chat: backend `chat` endpoint returns a `StreamingResponse` of text chunks (see `backend/app/api/routes/chat.py`). Frontend forwards the raw stream to the UI — do not double-wrap streams.
  - DB sessions: backend uses `SessionLocal()` pattern in routers (see `get_db()` in `chat.py`) — always close sessions via `try/finally` or `Depends` pattern.
  - RAG split: `core/rag.py` orchestrates query parsing, retrieval, and calling the LLM; `core/retrieval.py` contains vector search/resolution logic. Prefer small, testable edits in retrieval before changing RAG orchestration.
  - Supabase: frontend treats Supabase as client-side auth/storage; backend PostgreSQL interactions (if any) use `DATABASE_URL` and `SQLAlchemy` (`backend/app/core/database.py`).

- **Editing & adding endpoints**:
  - Add routers under `backend/app/api/routes/` and include them in `main.py` with `app.include_router(...)` using `/api/<name>` prefixes.
  - For streaming endpoints, return `StreamingResponse(generator, media_type='text/plain')` so frontend edge worker can proxy correctly.

- **Common pitfalls to avoid**:
  - Don't assume env vars are loaded from repo root — backend explicitly loads `backend/.env` in `config.py`.
  - Frontend edge functions run in an edge runtime and expect streaming responses — avoid Node-only APIs there.
  - The README is brief; prefer reading the actual `core` modules when changing RAG logic.

- **Files to reference for examples**:
  - `backend/app/main.py` (router setup, CORS)
  - `backend/app/api/routes/chat.py` (streaming chat endpoint)
  - `backend/app/core/config.py` (env loading)
  - `backend/app/core/rag.py`, `retrieval.py`, `scraper.py` (RAG pipeline)
  - `frontend/app/api/ai-chat/route.ts` (edge proxy to backend)
  - `frontend/lib/supabase/client.ts` (Supabase client pattern)

If anything above is unclear or you'd like me to expand any section (run/test scripts, example PR description, or more file snippets), tell me which part to improve and I'll iterate.
