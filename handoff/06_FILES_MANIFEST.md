# 📦 FILES MANIFEST

> The complete list of every file that must exist in the Conforma-AI repository.
> Codex creates files exactly as listed. ChatGPT tracks status here.

**Status legend:**
- ⬜ Not yet created
- 🟡 Stub (boilerplate, needs implementation)
- 🟢 Complete and tested

---

## ROOT (`/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `README.md` | 🟡 (v0.1 from D1) | D1, polish D7 | Public-facing project README |
| `LICENSE` | 🟢 | D1 | MIT license |
| `.gitignore` | 🟢 | D1 | Standard ignores for Python/Node/secrets |
| `docker-compose.yml` | 🟢 | D1 | Local Postgres + Redis for dev |
| `docker-compose.prod.yml` | ⬜ | D6 | Production stack on Vultr |
| `.github/workflows/ci.yml` | ⬜ | D6 (optional) | CI tests on push |

---

## BACKEND (`/backend`)

### Configuration

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/requirements.txt` | 🟢 | D1 | Pinned Python deps |
| `backend/.env.example` | 🟢 | D1 | Template for env vars |
| `backend/.env` | 🟢 (local only) | D1 | Real values, gitignored |
| `backend/pyproject.toml` | ⬜ | D2 | Ruff + Black config |
| `backend/alembic.ini` | ⬜ | D2 | Alembic config |
| `backend/Dockerfile` | ⬜ | D6 | Production container |
| `backend/README.md` | ⬜ | D6 | Backend-specific docs |

### Core app (`backend/app/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/__init__.py` | 🟢 | D1 | Package marker |
| `backend/app/main.py` | 🟡 (D1 smoke) | D1, expand D2-D5 | FastAPI app entry |

### Core utilities (`backend/app/core/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/core/__init__.py` | 🟢 | D1 | Package marker |
| `backend/app/core/config.py` | 🟢 | D1 | Pydantic Settings |
| `backend/app/core/gemini_client.py` | 🟢 | D1 | Centralized Gemini wrapper |
| `backend/app/core/logging.py` | ⬜ | D2 | Structured JSON logger |
| `backend/app/core/exceptions.py` | ⬜ | D2 | Custom exception classes |

### Agents (`backend/app/agents/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/agents/__init__.py` | ⬜ | D2 | Package marker |
| `backend/app/agents/base.py` | ⬜ | D2 | `BaseAgent` abstract class |
| `backend/app/agents/scanner.py` | ⬜ | D2 | Scanner agent |
| `backend/app/agents/classifier.py` | ⬜ | D3 | Classifier agent |
| `backend/app/agents/documentation.py` | ⬜ | D4 | Documentation agent |
| `backend/app/agents/disclosure.py` | ⬜ | D4 | Disclosure agent |
| `backend/app/agents/gap_auditor.py` | ⬜ | D4 | Gap Auditor agent |
| `backend/app/agents/monitor.py` | ⬜ | D5 | Monitor agent |
| `backend/app/agents/orchestrator.py` | ⬜ | D4 | LangGraph orchestrator |

### Knowledge base (`backend/app/knowledge/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/knowledge/__init__.py` | ⬜ | D1 | Package marker |
| `backend/app/knowledge/eu_ai_act_minimal.py` | 🟢 | D1 | Minimal KB for smoke test |
| `backend/app/knowledge/eu_ai_act_kb.py` | ⬜ | D3 | Full KB (see 05_EU_AI_ACT_KB.md) |
| `backend/app/knowledge/annex_iii_categories.py` | ⬜ | D3 | Structured Annex III data |
| `backend/app/knowledge/article_50_requirements.py` | ⬜ | D3 | Article 50 subsections data |
| `backend/app/knowledge/annex_iv_template.py` | ⬜ | D3 | Annex IV section structure |

### Agent prompts (`backend/app/knowledge/prompts/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/knowledge/prompts/scanner_system.md` | ⬜ | D2 | Scanner system prompt |
| `backend/app/knowledge/prompts/classifier_system.md` | ⬜ | D3 | Classifier system prompt |
| `backend/app/knowledge/prompts/documentation_system.md` | ⬜ | D4 | Documentation system prompt |
| `backend/app/knowledge/prompts/disclosure_system.md` | ⬜ | D4 | Disclosure system prompt |
| `backend/app/knowledge/prompts/gap_auditor_system.md` | ⬜ | D4 | Gap Auditor system prompt |
| `backend/app/knowledge/prompts/monitor_system.md` | ⬜ | D5 | Monitor system prompt |

### Database (`backend/app/db/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/db/__init__.py` | ⬜ | D2 | Package marker |
| `backend/app/db/session.py` | ⬜ | D2 | Async engine + sessionmaker |
| `backend/app/db/models.py` | ⬜ | D2 | SQLAlchemy ORM models (5 tables) |

### Migrations (`backend/alembic/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/alembic/env.py` | ⬜ | D2 | Alembic env config |
| `backend/alembic/script.py.mako` | ⬜ | D2 | Migration template |
| `backend/alembic/versions/0001_initial.py` | ⬜ | D2 | Initial schema migration |

### Schemas (`backend/app/schemas/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/schemas/__init__.py` | ⬜ | D2 | Package marker |
| `backend/app/schemas/agent.py` | ⬜ | D2 | Pydantic I/O schemas per agent |
| `backend/app/schemas/audit.py` | ⬜ | D2 | Audit/AISystem/Gap schemas |
| `backend/app/schemas/job.py` | ⬜ | D2 | Background job schemas |

### Routers (`backend/app/routers/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/routers/__init__.py` | ⬜ | D2 | Package marker |
| `backend/app/routers/health.py` | ⬜ | D2 | `GET /` + KB lookup endpoints |
| `backend/app/routers/audits.py` | ⬜ | D3 | Audit lifecycle endpoints |
| `backend/app/routers/agents.py` | ⬜ | D2 | Individual agent endpoints |
| `backend/app/routers/stream.py` | ⬜ | D4 | SSE streaming endpoint |
| `backend/app/routers/exports.py` | ⬜ | D4 | PDF download endpoint |

### Services (`backend/app/services/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/services/__init__.py` | ⬜ | D2 | Package marker |
| `backend/app/services/repo_cloner.py` | ⬜ | D2 | Git clone helper |
| `backend/app/services/pdf_generator.py` | ⬜ | D4 | WeasyPrint + Jinja2 |
| `backend/app/services/compliance_score.py` | ⬜ | D4 | Deterministic scoring function |
| `backend/app/services/notifications.py` | ⬜ | D5 | Mock webhook/email (post-MVP) |

### Templates (`backend/app/templates/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/templates/pdf/annex_iv.html` | ⬜ | D4 | Jinja2 template for PDF |
| `backend/app/templates/pdf/styles.css` | ⬜ | D4 | Print CSS |

### Workers (`backend/app/workers/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/app/workers/__init__.py` | ⬜ | D4 | Package marker |
| `backend/app/workers/celery_app.py` | ⬜ | D4 | Celery configuration |

### Tests (`backend/tests/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `backend/tests/__init__.py` | ⬜ | D2 | Package marker |
| `backend/tests/conftest.py` | ⬜ | D2 | Pytest fixtures |
| `backend/tests/test_scanner.py` | ⬜ | D2 | Scanner unit tests |
| `backend/tests/test_classifier.py` | ⬜ | D3 | Classifier tests (10 cases) |
| `backend/tests/test_documentation.py` | ⬜ | D4 | Documentation tests |
| `backend/tests/test_disclosure.py` | ⬜ | D4 | Disclosure tests |
| `backend/tests/test_gap_auditor.py` | ⬜ | D4 | Gap Auditor tests |
| `backend/tests/test_orchestrator.py` | ⬜ | D4 | End-to-end orchestrator test |
| `backend/tests/test_compliance_score.py` | ⬜ | D4 | Deterministic score tests |

---

## FRONTEND (`/frontend`)

### Configuration

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `frontend/package.json` | 🟢 | D1 | NPM deps |
| `frontend/tsconfig.json` | 🟢 | D1 | TS config |
| `frontend/tailwind.config.ts` | 🟢 | D1 | Tailwind config |
| `frontend/next.config.ts` | 🟢 | D1 | Next.js config |
| `frontend/.env.local.example` | 🟢 | D1 | API URL template |
| `frontend/components.json` | 🟢 | D1 | shadcn config |

### App Router (`frontend/app/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `frontend/app/layout.tsx` | 🟡 (Next default) | D5 | Global layout |
| `frontend/app/page.tsx` | 🟡 (D1 smoke) | D5 | Landing page |
| `frontend/app/globals.css` | 🟢 (Next default) | D1 | Tailwind imports |
| `frontend/app/audit/new/page.tsx` | ⬜ | D5 | New audit form |
| `frontend/app/audit/[id]/page.tsx` | ⬜ | D5 | Live audit dashboard |
| `frontend/app/audit/[id]/loading.tsx` | ⬜ | D5 | Skeleton loader |
| `frontend/app/audit/[id]/error.tsx` | ⬜ | D5 | Error boundary |

### Components (`frontend/components/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `frontend/components/ui/*` | 🟢 (shadcn) | D1 | shadcn primitives |
| `frontend/components/AgentCard.tsx` | ⬜ | D5 | One per agent, status + output |
| `frontend/components/ComplianceScoreRing.tsx` | ⬜ | D5 | Animated score ring (recharts) |
| `frontend/components/RiskBadge.tsx` | ⬜ | D5 | Colored badge per risk class |
| `frontend/components/AISystemCard.tsx` | ⬜ | D5 | Each AI system found |
| `frontend/components/AnnexIVPreview.tsx` | ⬜ | D5 | PDF preview + download |
| `frontend/components/DisclosureSnippets.tsx` | ⬜ | D5 | Multi-language tabs |
| `frontend/components/GapsList.tsx` | ⬜ | D5 | Sorted gap list with severity |
| `frontend/components/LiveStream.tsx` | ⬜ | D5 | SSE consumer with reconnect |
| `frontend/components/HeroSection.tsx` | ⬜ | D5 | Landing hero with Omnibus hook |
| `frontend/components/Footer.tsx` | ⬜ | D5 | Sponsor logos + license |

### Library (`frontend/lib/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `frontend/lib/api.ts` | ⬜ | D5 | Backend HTTP client |
| `frontend/lib/sse.ts` | ⬜ | D5 | EventSource wrapper hook |
| `frontend/lib/types.ts` | ⬜ | D5 | Shared types matching backend |
| `frontend/lib/utils.ts` | 🟢 (shadcn) | D1 | `cn()` helper |

### Public assets (`frontend/public/`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `frontend/public/favicon.ico` | 🟢 (default) | D1 | Browser tab icon |
| `frontend/public/og-image.png` | ⬜ | D7 | Open Graph share image |
| `frontend/public/conforma-logo.svg` | ⬜ | D5 | Brand mark |

---

## DOCUMENTATION (`/docs`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `docs/ARCHITECTURE.md` | ⬜ | D6 | Public arch doc (subset of internal) |
| `docs/SETUP.md` | ⬜ | D6 | Local dev setup instructions |
| `docs/DEPLOY.md` | ⬜ | D6 | Vultr + Vercel deployment guide |
| `docs/DEMO_SCRIPT.md` | ⬜ | D7 | 2-min video script |
| `docs/SLIDES.md` | ⬜ | D7 | Slide outline (Codex generates as .pdf via pptx skill) |
| `docs/cover.png` | ⬜ | D7 | lablab.ai listing image (1920x1080) |
| `docs/screenshots/vultr_dashboard.png` | ⬜ | D6 | Sponsor proof |
| `docs/screenshots/ai_studio_prompt.png` | ⬜ | D6 | Sponsor proof |
| `docs/screenshots/live_audit.png` | ⬜ | D6 | Product hero shot |
| `docs/screenshots/compliance_score.png` | ⬜ | D6 | Score visualization |
| `docs/screenshots/annex_iv_pdf.png` | ⬜ | D6 | Generated PDF sample |

---

## INFRASTRUCTURE (`/infra`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `infra/coolify/conforma-ai.yml` | ⬜ | D6 | Coolify service definition |
| `infra/nginx/conforma-ai.conf` | ⬜ | D6 | Nginx reverse proxy config |
| `infra/systemd/conforma-api.service` | ⬜ | D6 | Optional systemd unit |

---

## SCRIPTS (`/scripts`)

| Path | Status | Owner day | Purpose |
|---|---|---|---|
| `scripts/seed_test_data.py` | ⬜ | D3 | Populate DB with test audit |
| `scripts/run_demo_audit.py` | ⬜ | D6 | CLI: trigger full audit for demo prep |
| `scripts/deploy.sh` | ⬜ | D6 | One-shot deploy helper |
| `scripts/vultr_setup.sh` | ⬜ | D1 | Server initialization script |

---

## FILE COUNT SUMMARY

| Category | Total files | D1 status |
|---|---|---|
| Root configs | 6 | 4/6 complete |
| Backend code | ~50 | 8/50 (~16%) |
| Frontend code | ~25 | 8/25 (~32%) |
| Docs | ~11 | 0/11 |
| Infra | 3 | 0/3 |
| Scripts | 4 | 0/4 |
| **Grand total** | **~100** | **~20%** |

---

## CHANGE TRACKING PROTOCOL

When ChatGPT directs Codex to create or modify a file:

1. Verify the file is in this manifest. If not, add it.
2. Mark current status: ⬜ → 🟡 (stub created) → 🟢 (complete + tested)
3. If a file is needed that ISN'T in the manifest:
   - Pause before creating
   - Ask Eduky: "Need to create [path] for [reason]. Approve?"
   - Add to manifest with approval note before Codex creates it
   - This prevents scope creep

When Eduky reports D[n] status, ChatGPT updates this manifest's column.
