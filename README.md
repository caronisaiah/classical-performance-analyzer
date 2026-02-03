# Classical Performance Analyzer

Upload a classical music recording and get a tempo + dynamics analysis over time, with an interactive visualization synced to playback.

## Tech Stack
- Backend: FastAPI (Python), librosa
- Frontend: React (Vite)

## Local Development

### Backend
cd backend
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
uvicorn main:app --reload

### Frontend
cd frontend
npm install
npm run dev
