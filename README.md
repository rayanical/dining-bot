# UMass Dining Bot

This is a RAG chatbot designed to provide personalized meal recommendations for UMass dining halls. It uses a FastAPI backend for AI logic and a Next.js frontend for the user interface.

### Tech Stack

-   **Backend:** FastAPI (Python)
-   **Frontend:** Next.js (React / TypeScript)
-   **Database:** Supabase (PostgreSQL)
-   **Authentication:** Supabase Auth
-   **AI:** OpenAI
-   **Data:** Scraped from UMass Dining website

---

## Setup and Running the Project

Follow these steps to get the full application running locally.

### 1. Prerequisites

-   Python 3.8+
-   Node.js and Bun
-   Supabase keys
-   An OpenAI API key

### 2. Environment Setup

You will need to set up two separate environment files, one for the backend and one for the frontend.

**A. Backend (`backend/.env`):**
Create a new file at `backend/.env`.

```env
# From your Supabase "Database" settings (psycopg2)
DATABASE_URL=your_supabase_connection_string_here

# Your OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

**B. Frontend (`frontend/.env.local`):**
Create a new file at `frontend/.env.local` (this is the standard for Next.js).

```env
# From your Supabase "API" settings
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

### 4. Frontend Setup

In a **new terminal**, get the Next.js app running.

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install Node modules
bun install

# 3. Run the frontend development server
bun dev
```

✅ Your frontend is now running at `http://localhost:3000`.

You can now open `http://localhost:3000` in your browser to use the app.
