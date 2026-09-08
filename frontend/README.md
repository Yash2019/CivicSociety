# Nagar Sahayak frontend

## Run locally

Start the backend from the repository root:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then, in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The frontend uses `http://127.0.0.1:8000` by
default. To change it, create `frontend/.env.local` with:

```env
VITE_API_URL=http://127.0.0.1:8000
```

API documentation: http://127.0.0.1:8000/docs

PostgreSQL must be running and configured in `backend/.env` as `DATABASE_URL`.
