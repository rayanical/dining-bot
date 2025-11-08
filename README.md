### Backend (FastAPI Server)

1.  **Seed the Database**
    Run the scraper to populate your local database with dining hall menus. **Run this from the root `dining-bot` folder:**
    ```bash
    python backend/app/data/seed_db.py
    ```

2.  **Run the Backend Server**
    Navigate into the `backend` folder and start the `uvicorn` server:
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```
    ✅ The API is now running at `http://127.0.0.1:8000`.

3.  **API Routes**
    Open this URL in your browser:
    ```
    [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    ```
    You will see a full list of all available routes (like `/api/menu`) and can test them directly from that page.
