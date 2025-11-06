# Backend Setup Guide

## Database Connection (Supabase)

Your database is PostgreSQL hosted on Supabase. Update your `.env` file with the connection string:

```env
DATABASE_URL=postgresql://postgres.jfbbxfbpezpupyeapgbx:!dining-bot123@aws-1-us-east-1.pooler.supabase.com:5432/postgres
OPENAI_API_KEY=your_openai_api_key_here
```

**Note:** This uses Supabase's connection pooling for better performance. The database is PostgreSQL, just hosted/managed by Supabase.

## Setup Steps

1. **Install dependencies** (if not already done):
   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Set up your `.env` file**:
   - Create a `.env` file in the `backend/` directory if it doesn't exist
   - Add the `DATABASE_URL` and `OPENAI_API_KEY` as shown above

3. **Populate the database** (first time only):
   ```powershell
   python -m app.core.init_db
   ```
   This will:
   - Connect to your Supabase database
   - Scrape menu data from UMass Dining
   - Insert the data into the `dining_hall_menu` table
   
   **Note:** The tables already exist in Supabase, so we don't create them. If you want to re-scrape, the script will ask if you want to clear existing data.

4. **Start the backend server**:
   ```powershell
   uvicorn app.main:app --reload
   ```

5. **Test the API**:
   - Visit `http://127.0.0.1:8000/docs` for API documentation
   - Test the chat endpoint: `POST /api/chat` with body `{"query": "Where's the best vegan protein at Worcester?"}`

## Database Schema

The Supabase database has the following tables:
- `users` - User accounts
- `goals` - User health goals
- `dietary_constraints` - User dietary restrictions/allergies
- `diet_history` - Log of foods consumed
- `personal_menu` - Personalized menu items
- `dining_hall_menu` - Main menu items (populated by scraper)

## Troubleshooting

- **Connection errors**: Make sure your `.env` file has the correct `DATABASE_URL`
- **Scraping fails**: Check your internet connection
- **API errors**: Ensure `OPENAI_API_KEY` is set correctly

