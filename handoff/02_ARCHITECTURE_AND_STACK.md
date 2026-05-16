# 🏛️ ARCHITECTURE AND STACK

> Technical reference for Codex. Do not deviate from these decisions without consulting Eduky.

---

## 1. SYSTEM OVERVIEW

Conforma-AI is a multi-agent autonomous compliance system. Six specialized agents, orchestrated via LangGraph, process a code repository or document set as input and produce a complete EU AI Act compliance package as output.

### 1.1 High-level diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  WEB CLIENT (Next.js 15)                    │
│  Upload URL → Live Agent Status → Score Dashboard → PDFs    │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + Server-Sent Events
                           ▼
┌─────────────────────────────────────────────────────────────┐
│             ORCHESTRATOR API (FastAPI on Vultr)             │
│  Routes → Auth → Validation → Job Queue → SSE streamer      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH MULTI-AGENT GRAPH                    │
│                                                             │
│   ┌──────────┐                                              │
│   │ SCANNER  │ ── inventory ──► ┌──────────────┐            │
│   └──────────┘                  │  CLASSIFIER  │            │
│   (Flash)                       └──────┬───────┘            │
│                                        │ (Pro)              │
│                       ┌────────────────┼────────────────┐   │
│                       ▼                ▼                ▼   │
│              ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│              │DOCUMENTATION │  │  DISCLOSURE  │  │  GAP   │ │
│              └──────────────┘  └──────────────┘  │AUDITOR │ │
│              (Pro)             (Flash)           └────────┘ │
│                                                  (Pro)      │
│                                        │                    │
│                                        ▼                    │
│                                  ┌──────────┐               │
│                                  │ MONITOR  │               │
│                                  └──────────┘               │
│                                  (Flash)                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│        STATE LAYER (PostgreSQL + Redis on Vultr)            │
│        Audit trail · Job state · Agent traces               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUTS: PDFs (Vultr Object Storage) · JSON · Webhooks     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Why this architecture

- **LangGraph over CrewAI/AutoGen:** mature, production-ready, supports streaming, branching, conditional edges. Best fit for a compliance workflow with branching logic.
- **FastAPI over Flask/Django:** async-native, fits Gemini's async client, automatic OpenAPI docs.
- **Postgres over MongoDB:** structured relational data (compliance is inherently tabular), strong typing, ACID for audit trail.
- **SSE over WebSockets:** simpler, sufficient for one-way agent progress streaming, plays well with Vercel.
- **Celery + Redis:** long-running PDF generation and document parsing should not block API workers.

---

## 2. TECH STACK (pinned versions)

### 2.1 Backend (`backend/`)

```
Python                3.12.x
fastapi               0.115.0
uvicorn               0.32.0  (with [standard] extras)
pydantic              2.9.0
pydantic-settings     2.5.2
google-genai          0.3.0   (NEW unified SDK, NOT google-generativeai)
langgraph             0.2.45
langchain-core        0.3.15
sqlalchemy            2.0.35
alembic               1.13.3
asyncpg               0.30.0
psycopg2-binary       2.9.10
redis                 5.1.1
celery                5.4.0
python-dotenv         1.0.1
httpx                 0.27.2
python-multipart      0.0.12
GitPython             3.1.43
weasyprint            62.3    (PDF generation)
jinja2                3.1.4   (template engine for PDFs)
tree-sitter           0.23.0  (code parsing — optional, only if needed)
pytest                8.3.3
pytest-asyncio        0.24.0
```

### 2.2 Frontend (`frontend/`)

```
Next.js               15.x         (App Router)
React                 19.x
TypeScript            5.x          (strict mode)
Tailwind CSS          3.4.x
shadcn/ui             latest       (manually added components only)
lucide-react          latest
recharts              latest       (for Compliance Score visualizations)
```

### 2.3 Infrastructure

```
Vultr Cloud Compute   Frankfurt region · Regular Performance
                      2 vCPU · 4 GB RAM · 80 GB SSD · $12/mo
                      Ubuntu 24.04 LTS

Postgres              16 (local on Vultr VM via Docker for D1-D5,
                      promote to Vultr Managed Database for D6 prod)

Redis                 7 (local on Vultr VM via Docker)

Vercel                Frontend hosting (free tier)

Coolify               Self-hosted on Vultr for automated deploys (D6)

Domain (optional)     conforma.ai / conforma-ai.eu via Namecheap
                      (skip if budget-tight; vercel.app subdomain works)
```

### 2.4 LLM (Gemini)

```
Primary (reasoning):  gemini-3.1-pro-preview
                      2M token context · paid tier
                      Used by: Orchestrator, Classifier, Documentation, Gap Auditor

Secondary (speed):    gemini-3-flash-preview
                      Default Flash · free tier with quota
                      Used by: Scanner, Disclosure, Monitor

Access:               Google AI Studio API key (single key, not service account)
                      $300 Google Cloud free credits (90 days) covers Pro usage
```

---

## 3. REPOSITORY STRUCTURE

```
conforma-ai/
├── README.md
├── LICENSE
├── .gitignore
├── docker-compose.yml          # local Postgres + Redis
│
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── pyproject.toml          # ruff + black config
│   ├── README.md
│   │
│   ├── alembic/                # DB migrations
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI entry
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # Settings (pydantic-settings)
│   │   │   ├── gemini_client.py
│   │   │   ├── logging.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # BaseAgent abstract class
│   │   │   ├── scanner.py
│   │   │   ├── classifier.py
│   │   │   ├── documentation.py
│   │   │   ├── disclosure.py
│   │   │   ├── gap_auditor.py
│   │   │   ├── monitor.py
│   │   │   └── orchestrator.py # LangGraph wiring
│   │   │
│   │   ├── knowledge/
│   │   │   ├── __init__.py
│   │   │   ├── eu_ai_act_kb.py        # full KB content
│   │   │   ├── annex_iii_categories.py
│   │   │   ├── article_50_requirements.py
│   │   │   ├── annex_iv_template.py
│   │   │   └── prompts/
│   │   │       ├── scanner_system.md
│   │   │       ├── classifier_system.md
│   │   │       ├── documentation_system.md
│   │   │       ├── disclosure_system.md
│   │   │       ├── gap_auditor_system.md
│   │   │       └── monitor_system.md
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py      # async engine + sessionmaker
│   │   │   └── models.py       # SQLAlchemy ORM models
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Pydantic I/O schemas per agent
│   │   │   ├── audit.py
│   │   │   └── job.py
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── audits.py       # POST /audits, GET /audits/{id}
│   │   │   ├── agents.py       # individual agent endpoints (testing)
│   │   │   ├── stream.py       # SSE endpoint
│   │   │   └── exports.py      # PDF download
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── repo_cloner.py  # clones GitHub repos to temp dir
│   │   │   ├── pdf_generator.py # WeasyPrint + Jinja2
│   │   │   ├── compliance_score.py
│   │   │   └── notifications.py # webhook + email (mocked for hackathon)
│   │   │
│   │   ├── templates/
│   │   │   └── pdf/
│   │   │       ├── annex_iv.html
│   │   │       └── styles.css
│   │   │
│   │   └── workers/
│   │       ├── __init__.py
│   │       └── celery_app.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_classifier.py
│       ├── test_scanner.py
│       └── ...
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── .env.local.example
│   │
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                    # landing + demo entry
│   │   ├── audit/
│   │   │   ├── new/page.tsx            # submit repo URL
│   │   │   └── [id]/page.tsx           # live audit dashboard
│   │   └── api/                         # API routes if needed
│   │
│   ├── components/
│   │   ├── ui/                          # shadcn primitives
│   │   ├── AgentCard.tsx
│   │   ├── ComplianceScoreRing.tsx
│   │   ├── RiskBadge.tsx
│   │   ├── AnnexIVPreview.tsx
│   │   └── LiveStream.tsx              # SSE consumer
│   │
│   ├── lib/
│   │   ├── api.ts                       # backend client
│   │   ├── sse.ts                       # SSE helper
│   │   └── types.ts                     # shared types matching backend schemas
│   │
│   └── public/
│       ├── favicon.ico
│       └── og-image.png
│
├── docs/
│   ├── ARCHITECTURE.md         # subset of this file for repo readers
│   ├── SETUP.md                # local dev setup
│   ├── DEPLOY.md               # Vultr + Vercel deployment
│   ├── DEMO_SCRIPT.md          # what to show in video
│   └── screenshots/
│       ├── vultr_dashboard.png
│       ├── ai_studio_prompt.png
│       └── ...
│
├── infra/
│   ├── coolify/
│   │   └── conforma-ai.yml     # Coolify service definition
│   ├── nginx/
│   │   └── conforma-ai.conf
│   └── systemd/
│       └── conforma-api.service
│
└── scripts/
    ├── seed_test_data.py
    ├── run_demo_audit.py       # CLI to trigger a full audit for testing
    └── deploy.sh                # one-shot deploy script
```

---

## 4. DATA MODEL (PostgreSQL via SQLAlchemy)

### 4.1 Tables

```sql
-- Top-level audit job
audits (
  id              UUID PRIMARY KEY,
  source_url      TEXT NOT NULL,        -- e.g., github.com/org/repo
  source_type     TEXT NOT NULL,        -- 'github_repo' | 'document_set'
  status          TEXT NOT NULL,        -- queued|running|completed|failed
  compliance_score INTEGER,             -- 0-100, NULL until done
  risk_index      TEXT,                 -- LOW|MEDIUM|HIGH|CRITICAL
  fine_exposure_eur INTEGER,            -- estimated euros at risk
  created_at      TIMESTAMP NOT NULL,
  completed_at    TIMESTAMP,
  metadata        JSONB                 -- arbitrary org info
)

-- Each AI system found in the audit
ai_systems (
  id              UUID PRIMARY KEY,
  audit_id        UUID NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,        -- e.g., "credit_scoring_model_v2"
  description     TEXT NOT NULL,
  source_files    TEXT[],                -- list of file paths in repo
  risk_class      TEXT,                  -- UNACCEPTABLE|HIGH_RISK|LIMITED_RISK|MINIMAL_RISK
  primary_article TEXT,                  -- e.g., "Annex III §5(b)"
  reasoning       TEXT,
  deadline        TEXT,
  confidence      NUMERIC(3,2),          -- 0.00 to 1.00
  created_at      TIMESTAMP NOT NULL
)

-- Agent execution trace (one row per agent run on one system)
agent_runs (
  id              UUID PRIMARY KEY,
  audit_id        UUID NOT NULL REFERENCES audits(id),
  ai_system_id    UUID REFERENCES ai_systems(id),
  agent_name      TEXT NOT NULL,         -- 'scanner'|'classifier'|...
  status          TEXT NOT NULL,         -- running|completed|failed
  input           JSONB,
  output          JSONB,
  tokens_in       INTEGER,
  tokens_out      INTEGER,
  model           TEXT,                  -- 'gemini-3.1-pro-preview' etc
  started_at      TIMESTAMP NOT NULL,
  completed_at    TIMESTAMP,
  error           TEXT
)

-- Generated documentation artifacts
artifacts (
  id              UUID PRIMARY KEY,
  audit_id        UUID NOT NULL REFERENCES audits(id),
  ai_system_id    UUID REFERENCES ai_systems(id),
  kind            TEXT NOT NULL,         -- 'annex_iv_pdf'|'article_50_snippet'|'remediation_plan'
  language        TEXT,                   -- ISO 639-1: en|it|es|fr|de
  storage_url     TEXT,                   -- Vultr Object Storage URL
  content         TEXT,                   -- inline text for small artifacts
  created_at      TIMESTAMP NOT NULL
)

-- Identified compliance gaps
gaps (
  id              UUID PRIMARY KEY,
  audit_id        UUID NOT NULL REFERENCES audits(id),
  ai_system_id    UUID REFERENCES ai_systems(id),
  category        TEXT NOT NULL,         -- 'documentation'|'transparency'|'oversight'|...
  severity        TEXT NOT NULL,         -- LOW|MEDIUM|HIGH|CRITICAL
  description     TEXT NOT NULL,
  remediation     TEXT NOT NULL,
  effort_days     INTEGER,
  deadline        DATE
)
```

### 4.2 Migrations
All schema changes via Alembic. Initial migration generated on D2.

---

## 5. API SURFACE (FastAPI)

### 5.1 Public endpoints

```
GET  /                                       Health check
GET  /api/v1/ai-act/risk-classes             Static KB lookup
GET  /api/v1/ai-act/annex-iii                Annex III categories
GET  /api/v1/ai-act/annex-iv-template        Annex IV template structure

POST /api/v1/audits                          Start new audit (returns audit_id)
GET  /api/v1/audits/{audit_id}               Get audit state
GET  /api/v1/audits/{audit_id}/stream        SSE: live agent progress
GET  /api/v1/audits/{audit_id}/systems       List AI systems found
GET  /api/v1/audits/{audit_id}/artifacts     List generated artifacts
GET  /api/v1/audits/{audit_id}/gaps          List compliance gaps
GET  /api/v1/audits/{audit_id}/export/pdf    Download full compliance package

# Individual agent endpoints (for testing and demo flexibility)
POST /api/v1/agents/scanner                  Scan-only
POST /api/v1/agents/classifier               Classify a system description
POST /api/v1/agents/documentation            Generate Annex IV for a system
POST /api/v1/agents/disclosure               Generate Art. 50 snippet
POST /api/v1/agents/gap-auditor              Compute gaps + score
POST /api/v1/agents/monitor                  Trigger monitoring check
```

### 5.2 SSE event format

```
event: agent_start
data: {"agent":"scanner","audit_id":"...","timestamp":"..."}

event: agent_progress
data: {"agent":"scanner","message":"Found 7 candidate AI systems","timestamp":"..."}

event: agent_complete
data: {"agent":"scanner","output_summary":{...},"timestamp":"..."}

event: audit_complete
data: {"audit_id":"...","compliance_score":42,"timestamp":"..."}

event: error
data: {"agent":"...","error":"...","timestamp":"..."}
```

---

## 6. DEPLOYMENT TOPOLOGY

### 6.1 Development (D1-D5)
- Backend: local on Eduky's Windows (WSL or native Python)
- Postgres + Redis: local Docker
- Frontend: local Next.js dev server
- LLM: Gemini API direct

### 6.2 Staging on Vultr (D6)
- Vultr VM in Frankfurt
- Docker Compose stack: api + worker + postgres + redis
- Nginx reverse proxy with Let's Encrypt
- Coolify for automated deploys from GitHub
- Domain: TBD or `<vm-ip>.nip.io` for quick HTTPS

### 6.3 Frontend on Vercel (D6)
- Connected to GitHub repo
- Auto-deploys main branch
- Env var: `NEXT_PUBLIC_API_URL=https://api.conforma.ai` (or VM domain)

### 6.4 Why not all on Vultr?
- Vercel free tier is faster, has better DX for Next.js, and won't compete with backend resources on the Vultr VM.
- Vultr scoring still strong: backend (the AI core) lives there, plus database, plus storage.

---

## 7. SECURITY & SECRETS

| Secret | Where stored | Rotation |
|---|---|---|
| `GEMINI_API_KEY` | `.env` (gitignored) + Vultr env vars | After demo only |
| `DATABASE_URL` | `.env` + Vultr env vars | After demo only |
| `SECRET_KEY` (FastAPI) | `.env` + Vultr env vars | Generate fresh per env |
| SSH key | `~/.ssh/id_ed25519` on Eduky's machine | Not rotated |
| Vultr API token (if used) | password manager | After demo |

**Never commit:** `.env`, `*.pem`, `*.key`, screenshots with visible keys, postgres passwords in plain text.

---

## 8. OBSERVABILITY

- **Logging:** structured JSON to stdout, captured by systemd/journald on Vultr
- **Tracing:** Langfuse self-hosted on Vultr (one extra Docker service) — shows multi-agent traces for jury demo
- **Metrics:** Postgres `agent_runs` table is the source of truth for token usage, latency, errors

---

## 9. CONVENTIONS

### 9.1 Naming
- Files: `snake_case.py` / `kebab-case.tsx`
- Python classes: `PascalCase`
- Python functions: `snake_case`
- TypeScript: `camelCase` for vars/functions, `PascalCase` for types/components
- API routes: `/api/v1/kebab-case`
- DB columns: `snake_case`

### 9.2 Git
- Branch strategy: single `main` branch during hackathon (no PRs, no feature branches — wastes time)
- Commits: semantic prefixes — `feat(D2): scanner agent`, `fix: classifier JSON parsing`, `docs: README updates`
- Tag final version: `v1.0.0-hackathon` at submission

### 9.3 Code style
- Python: `ruff` for linting, `black` for formatting (config in `pyproject.toml`)
- TypeScript: rely on Next.js defaults
- No tests required for UI components during hackathon
- Tests required for: each agent's core function, compliance score computation, classifier output parsing

---

## 10. EXPLICIT NON-GOALS

To preserve scope discipline, Conforma-AI will **NOT** include in v1.0:

- ❌ User authentication / multi-tenancy (mock single-user only)
- ❌ Billing / Stripe
- ❌ Real-time collaboration features
- ❌ Mobile apps
- ❌ Speechmatics integration (decided in strategy phase)
- ❌ Kraken / xStocks integration (decided in strategy phase)
- ❌ Direct integrations with Jira/Notion/Slack (mock these with webhook output only)
- ❌ Production-grade error retries (best-effort during demo)
- ❌ Internationalization of the UI (demo in English, snippets multilingual)

These belong to v2.0 post-hackathon.
