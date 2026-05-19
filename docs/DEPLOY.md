# Conforma-AI Deployment Guide

## Vultr VM prerequisites

- Ubuntu 24.04 LTS VM is provisioned.
- Docker Engine and Docker Compose plugin are installed.
- Git is installed.
- Port `80` is open for Nginx and TLS bootstrapping.
- Optional: a public API hostname such as `<server-ip>.nip.io` or `api.yourdomain.com`.
- Optional: Managed PostgreSQL on Vultr. If you do not use it, the production compose file contains a profile-based fallback Postgres service.

## 1. Verify Docker on the VM

```bash
docker --version
docker compose version
docker info
```

## 2. Clone the repository

```bash
git clone https://github.com/<your-user>/conforma-ai.git
cd conforma-ai
```

## 3. Create `backend/.env.production`

Do not commit this file.

```bash
cp backend/.env.production.example backend/.env.production
```

Fill in at least:

- `DATABASE_URL`
- `REDIS_URL` if you are not using the bundled Redis service
- `GEMINI_API_KEY`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `FRONTEND_URL`

For a Managed PostgreSQL deployment, `DATABASE_URL` should point to the managed instance.

## 4. Start the production stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

If you want the local fallback Postgres instead of Managed PostgreSQL:

```bash
docker compose -f docker-compose.prod.yml --profile fallback-db up -d --build
```

## 5. Run Alembic migrations

```bash
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
```

## 6. Test the API health endpoint

```bash
curl -fsS http://127.0.0.1:8000/
```

Expected:

```json
{"status":"operational","service":"conforma-ai","version":"0.1.0"}
```

## 7. Test the orchestrated audit endpoint

```bash
curl -X POST http://127.0.0.1:8000/api/v1/audits/orchestrated \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/karpathy/llm.c","max_files_to_inspect":50}'
```

Then open the SSE stream URL returned by the response:

```bash
curl -N http://127.0.0.1:8000/api/v1/audits/<audit_id>/stream
```

## 8. Configure Nginx

Copy the provided config and replace the placeholder `server_name`.

```bash
sudo cp infra/nginx/conforma-ai.conf /etc/nginx/sites-available/conforma-ai.conf
sudo ln -sf /etc/nginx/sites-available/conforma-ai.conf /etc/nginx/sites-enabled/conforma-ai.conf
sudo nginx -t
sudo systemctl reload nginx
```

The config already disables proxy buffering for SSE.

## 9. Deploy the frontend to Vercel

When importing the repository in Vercel:

- Set the **Root Directory** to `frontend`
- Framework preset: `Next.js`
- Build command: `npm run build`

Environment variable in Vercel:

```text
NEXT_PUBLIC_API_URL=https://<your-vultr-api-domain>
```

Use the value from `frontend/.env.production.example` as the template.

## 10. Optional one-command deploy

```bash
bash scripts/deploy.sh
```

The script:

- pulls the latest `main`
- checks `backend/.env.production`
- rebuilds the stack
- runs Alembic
- hits `GET /`

## Smoke test checklist

- `docker compose -f docker-compose.prod.yml ps`
- `curl -fsS http://127.0.0.1:8000/`
- `POST /api/v1/audits/orchestrated` returns an `audit_id`
- `GET /api/v1/audits/{audit_id}/stream` streams SSE events
- Resume-Screening still produces `HIGH_RISK`, `Annex III Section 4(a)`, and `2027-12-02`
- `karpathy/llm.c` still produces `LIMITED_RISK`, `Article 50(2)`, and disclosures
- Frontend on Vercel can reach the Vultr API over HTTPS
