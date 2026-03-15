# Intelli-Credit - How to Start

## Every time you start the app

### Terminal 1 - Marker tunnel (keep open):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_marker_tunnel.ps1
```
Enter SSH password when prompted.
Keep this window open the entire session.

### Terminal 2 - Backend:
```powershell
cd C:\Users\labdh\vivriti\backend
.\.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 3 - Frontend:
```powershell
cd C:\Users\labdh\vivriti\frontend
npm run dev
```

### Open in browser:
```text
http://localhost:3000
```

## One-time GPU server setup:
```bash
ssh xyzxyzserver
conda activate vivriti
pip install fastapi uvicorn
cd ~/vivriti
python scripts/marker_server.py
```

## Environment variables needed:
backend/.env:
```text
GEMINI_API_KEY=your_gemini_key
FIRECRAWL_API_KEY=your_firecrawl_key
MARKER_API_URL=http://127.0.0.1:8001
```

frontend/.env.local:
```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```
