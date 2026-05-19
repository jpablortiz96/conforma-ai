# Conforma-AI Deployment Guide

## Vultr VM prerequisites

- Ubuntu 24.04 LTS VM is provisioned.
- Docker Engine and Docker Compose plugin are installed.
- Git is installed.
- Port `80` and `443` are open for Caddy and HTTPS.
- A public API hostname is available. The working deployment pattern is:
  - `https://api.140.82.34.171.nip.io`
  - replace `140.82.34.171` with your VM public IP.

## Public reverse proxy: Caddy

The production backend is exposed through **Caddy**, not directly from Docker and not through Nginx in the live path.

Why `nip.io`:

- `sslip.io` hit Let's Encrypt rate-limit friction during the live deploy window.
- `nip.io` resolved cleanly and let Caddy issue certificates for the API hostname pattern immediately.
- The working public endpoint pattern is:
  - `https://api.<your-server-ip>.nip.io`
  - example: `https://api.140.82.34.171.nip.io`

### Caddyfile example

```caddy
api.140.82.34.171.nip.io {
    encode zstd gzip

    reverse_proxy 127.0.0.1:8000 {
        flush_interval -1
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

This keeps the public HTTPS surface in Caddy while the API container remains bound to `127.0.0.1:8000`.

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

Default production compose now includes a local `postgres:16-alpine` service. If you still want Managed PostgreSQL, replace `DATABASE_URL` with the external DSN and keep the bundled Postgres service stopped or unused.

## 4. Start the production stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

The production stack now includes:

- `api`
- `postgres`
- `redis`

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

## 8. Configure Caddy

Create or update `/etc/caddy/Caddyfile` with the `nip.io` host you are using:

```bash
sudo nano /etc/caddy/Caddyfile
```

Example:

```caddy
api.140.82.34.171.nip.io {
    encode zstd gzip

    reverse_proxy 127.0.0.1:8000 {
        flush_interval -1
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

Then reload Caddy:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

The repo still contains `infra/nginx/conforma-ai.conf` as a reverse-proxy reference, but the working production edge now uses Caddy.

## 9. Deploy the frontend to Vercel

When importing the repository in Vercel:

- Set the **Root Directory** to `frontend`
- Framework preset: `Next.js`
- Build command: `npm run build`

Environment variable in Vercel:

```text
NEXT_PUBLIC_API_URL=https://api.<your-server-ip>.nip.io
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
- `curl -fsS https://api.<your-server-ip>.nip.io/`
- `POST /api/v1/audits/orchestrated` returns an `audit_id`
- `GET /api/v1/audits/{audit_id}/stream` streams SSE events
- Resume-Screening still produces `HIGH_RISK`, `Annex III Section 4(a)`, and `2027-12-02`
- `karpathy/llm.c` still produces `LIMITED_RISK`, `Article 50(2)`, and disclosures
- Frontend on Vercel can reach the Vultr API over HTTPS
