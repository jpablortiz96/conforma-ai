# Conforma-AI Local Setup

## Prerequisites

- Python 3.12
- Node.js 20+
- Docker Engine or Docker Desktop
- Git

## 1. Clone the repository

```bash
git clone https://github.com/<your-user>/conforma-ai.git
cd conforma-ai
```

## 2. Backend environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in:

- `GEMINI_API_KEY`
- `SECRET_KEY`

Keep `DATABASE_URL` and `REDIS_URL` pointed at the local Docker services unless you intentionally override them.

## 3. Start Postgres and Redis for local development

```bash
cd ..
docker compose up -d
```

## 4. Run Alembic migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

## 5. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 6. Frontend environment

In a new terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local` if you want to override the API URL:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then start the frontend:

```bash
npm run dev
```

## 7. Local smoke tests

Backend health:

```bash
curl -fsS http://localhost:8000/
```

Synchronous audit:

```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/anukalp-mishra/Resume-Screening","max_files_to_inspect":80}'
```

Orchestrated audit:

```bash
curl -X POST http://localhost:8000/api/v1/audits/orchestrated \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/karpathy/llm.c","max_files_to_inspect":50}'
```

Frontend:

- Open `http://localhost:3000`
- Run one Resume-Screening audit
- Run one `karpathy/llm.c` audit

## 8. Frontend production simulation

```bash
cd frontend
npm run typecheck
npm run build
```

## 9. Production handoff references

- Deployment runbook: [DEPLOY.md](./DEPLOY.md)
- Production env template: `backend/.env.production.example`
- Production compose file: `docker-compose.prod.yml`
