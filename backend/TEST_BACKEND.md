# Backend Testing Guide

## Step-by-Step Troubleshooting

### 1. Check if Backend is Running

Open a PowerShell terminal and run:
```powershell
netstat -ano | findstr :8000
```

If you see output with `LISTENING`, the backend is running.
If no output, the backend is NOT running.

### 2. Start the Backend

If the backend is not running:
```powershell
cd C:\Users\dhruv\Desktop\dining-bot\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 3. Test Backend in Browser

Open your browser and visit:
- `http://127.0.0.1:8000/` - Should show `{"message": "Dining Bot API is running!"}`
- `http://127.0.0.1:8000/docs` - Should show the API documentation

### 4. Test Chat Endpoint Directly

Visit `http://127.0.0.1:8000/docs` and:
1. Click on `POST /api/chat`
2. Click "Try it out"
3. Enter: `{"query": "test"}`
4. Click "Execute"

If this works, the backend is working correctly.

### 5. Check Frontend Port

Check which port your frontend is running on:
- Look at the terminal where you ran `bun dev`
- It should show: `Local: http://localhost:3000` or `Local: http://localhost:3001`

### 6. Verify Frontend is Calling Correct URL

The frontend should be calling: `http://127.0.0.1:8000/api/chat`

Open browser DevTools (F12) → Network tab → Try sending a message → Check if the request is being made and what the error is.

### 7. Common Issues

**Backend not running:**
- Start it with: `uvicorn app.main:app --reload`

**Port conflict:**
- Backend must be on port 8000
- Frontend can be on 3000 or 3001

**CORS errors:**
- Check browser console (F12) for CORS errors
- Backend should allow the frontend origin

**Network errors:**
- Make sure Windows Firewall isn't blocking the connection
- Try using `localhost` instead of `127.0.0.1` in the frontend code

