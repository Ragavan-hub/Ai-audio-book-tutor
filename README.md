# AI Audio Book Tutor — Gemini + Ollama
Next.js frontend + FastAPI backend starter.

## Run locally (PowerShell)
Backend:
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Put your Gemini key in backend/.env
uvicorn app.main:app --reload --port 8000
```
Frontend (new terminal):
```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```
Open http://localhost:3000 and API docs at http://localhost:8000/docs.

Get a key: https://aistudio.google.com/apikey. The key belongs only in backend/.env.
Ollama local mode: install Ollama, run `ollama pull llama3.1`, set `AI_PROVIDER=ollama`.
Cloud: deploy backend to Render (root `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Set `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.8-flash`, `AI_PROVIDER=gemini`, `FRONTEND_ORIGIN=https://YOUR.vercel.app`, `DATA_DIR=/var/data`; attach persistent disk at `/var/data`.
Deploy frontend to Vercel (root `frontend`), set `NEXT_PUBLIC_API_BASE=https://YOUR-RENDER.onrender.com`.

Notes: This is a fresh runnable foundation, not an exact migration of your Streamlit app. PDF text extraction supports selectable-text PDFs only. Retrieval uses TF-IDF. Existing FAISS/chapter JSON files are not overwritten. Edge TTS is included; Faster-Whisper transcription is not enabled in this starter. Render default disk is ephemeral; persistent disk or external storage is needed. Add authentication, per-user isolation, rate limiting and upload limits before public production.
