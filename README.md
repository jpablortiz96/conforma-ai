# Conforma-AI

Conforma-AI is a multi-agent EU AI Act compliance workspace being built for the AI Agent Olympics Hackathon. The target product uses six specialized agents across the compliance lifecycle:

1. Scanner
2. Classifier
3. Documentation
4. Disclosure
5. Gap Auditor
6. Monitor

D1 implements the repository baseline plus the Classifier agent smoke path locally. Production deployment on Vultr is intentionally deferred to D6.

## D1 Scope

- FastAPI backend on Python 3.12
- Gemini access centralized in `backend/app/core/gemini_client.py`
- Deterministic fallback classifier for the required smoke cases
- Next.js 15 frontend at `http://localhost:3000`
- Local infrastructure via Docker Compose for PostgreSQL and Redis

## Repository Layout

```text
conforma-ai/
|-- backend/
|-- frontend/
|-- handoff/
|-- scripts/
|-- docker-compose.yml
`-- README.md
```

## Local Setup

### 1. Start local infrastructure

```powershell
docker compose up -d
```

### 2. Configure backend environment

```powershell
Copy-Item backend/.env.example backend/.env
```

Then edit `backend/.env` and set at least:

```env
GEMINI_API_KEY=your_google_ai_studio_key
```

Do not commit `backend/.env`, `.env`, or `frontend/.env.local`.

### 3. Create a backend virtual environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend health should respond at `http://localhost:8000/`.

### 5. Probe Gemini model access

```powershell
cd ..
python scripts/gemini_probe.py
```

The probe checks:

- `gemini-3.1-pro-preview`
- `gemini-3-flash-preview`

If access fails, the script prints diagnostics and manual fallback suggestions without changing the app behavior.

### 6. Install and run the frontend

```powershell
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:3000` and targets `http://localhost:8000` by default.

## Curl Smoke Tests

### Health check

```bash
curl http://localhost:8000/
```

Expected shape:

```json
{
  "status": "operational",
  "service": "conforma-ai",
  "version": "0.1.0"
}
```

### Required classifier smoke cases

```bash
curl http://localhost:8000/api/v1/agents/classifier --json '{"system_description":"Bank CV ranking"}'
```

```bash
curl http://localhost:8000/api/v1/agents/classifier --json '{"system_description":"Password reset chatbot"}'
```

```bash
curl http://localhost:8000/api/v1/agents/classifier --json '{"system_description":"Real-time facial recognition shoplifter"}'
```

```bash
curl http://localhost:8000/api/v1/agents/classifier --json '{"system_description":"Email spam filter"}'
```

## D1 Status Checklist

- [x] Root health endpoint returns the required operational payload
- [x] Classifier endpoint returns the required JSON contract
- [x] Deterministic fallback covers the four D1 smoke cases
- [x] Gemini access is centralized in `backend/app/core/gemini_client.py`
- [x] Gemini probe script exists for preview model access checks
- [x] Frontend points to `localhost:8000` and surfaces fallback mode clearly
- [x] Six-agent product direction is visible in the D1 UI
- [ ] Production deployment to Vultr and Vercel
- [ ] Scanner, Documentation, Disclosure, Gap Auditor, and Monitor implementations

## Notes

- D1 is intentionally local-first. Do not deploy production yet.
- The classifier reasoning uses only the minimal handoff-backed EU AI Act knowledge needed for smoke validation.
- If Gemini is unavailable, the app remains usable in deterministic fallback mode and labels the response with `"mode": "fallback"`.
