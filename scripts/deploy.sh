#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.prod.yml"
ENV_FILE="${REPO_ROOT}/backend/.env.production"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8000/}"

echo "==> Conforma-AI D6 deploy"
echo "Repo root: ${REPO_ROOT}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} does not exist."
  echo "Create it from backend/.env.production.example before deploying."
  exit 1
fi

cd "${REPO_ROOT}"

echo "==> Pulling latest main"
git fetch --all --prune
git checkout main
git pull --ff-only origin main

echo "==> Building and starting production services"
docker compose -f "${COMPOSE_FILE}" up -d --build

echo "==> Running Alembic migrations inside the API container"
docker compose -f "${COMPOSE_FILE}" exec -T api alembic upgrade head

echo "==> Verifying API health"
curl --fail --silent "${HEALTHCHECK_URL}" | tee /tmp/conforma-health.json

echo
echo "==> Deploy checks complete"
echo "Health endpoint: ${HEALTHCHECK_URL}"
echo "Orchestrated audit endpoint: ${HEALTHCHECK_URL%/}/api/v1/audits/orchestrated"
echo "If Nginx is installed, point it at: infra/nginx/conforma-ai.conf"
echo "If Vercel is configured, set NEXT_PUBLIC_API_URL to your public API domain."
