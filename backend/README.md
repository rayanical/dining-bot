Backend Setup

First, get the FastAPI server running.

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
python -m venv .venv
source .venv/bin/activate  # (or .\.venv\Scripts\Activate.ps1 on PowerShell)

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Scrape and populate the database
# This runs the scraper from app/core/init_db.py
python -m app.core.init_db

# 5. Run the backend server
uvicorn app.main:app --reload
```

✅ Your backend is now running at `http://127.0.0.1:8000`.
