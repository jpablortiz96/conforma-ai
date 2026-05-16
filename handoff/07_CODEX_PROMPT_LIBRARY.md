# 🎯 CODEX PROMPT LIBRARY

> Reusable prompt templates for ChatGPT to dispatch to Codex. Each template has: trigger condition, template body, parameters to fill in, and post-execution verification.
>
> **Critical rule:** ChatGPT NEVER asks Codex to write code without referencing the relevant section of `02_ARCHITECTURE_AND_STACK.md`, `04_AGENT_SPECS.md`, or `05_EU_AI_ACT_KB.md`. The handoff package is the source of truth, not Codex's general training.

---

## PROMPT TYPE 1: CREATE A FILE FROM SPEC

### Trigger
A file in `06_FILES_MANIFEST.md` needs to be created (⬜ → 🟢).

### Template

```
You are implementing a file for the Conforma-AI project. Read these reference files in this order, then write the requested code.

REFERENCES:
1. /handoff/02_ARCHITECTURE_AND_STACK.md (sections: {sections})
2. /handoff/04_AGENT_SPECS.md (if implementing an agent)
3. /handoff/05_EU_AI_ACT_KB.md (if the file uses AI Act content)

CONTEXT:
- File path: {full_path}
- Purpose: {one_line_purpose}
- Dependencies: {existing files this depends on}
- Day in sprint: D{n}

TASK:
Write the full content of `{full_path}` following the specifications in the references.

Requirements:
- Use pinned versions from `02_ARCHITECTURE_AND_STACK.md` §2
- Match conventions in `02_ARCHITECTURE_AND_STACK.md` §9
- Include docstrings for all public functions/classes
- Type hints throughout (Python: PEP 484; TypeScript: strict mode)
- If touching the database, never run raw SQL — use SQLAlchemy ORM
- If touching Gemini, use the `gemini_client` wrapper, never the SDK directly

ACCEPTANCE CRITERIA:
{paste_from_project_plan}

OUTPUT FORMAT:
Just the file content. No surrounding markdown. No commentary. No explanation.
```

### Parameters to fill in
- `{full_path}` — exact path from manifest (e.g., `backend/app/agents/scanner.py`)
- `{one_line_purpose}` — from manifest "Purpose" column
- `{sections}` — relevant section numbers from architecture doc
- `{n}` — sprint day number
- `{paste_from_project_plan}` — acceptance criteria for this specific file

### Post-execution verification
1. File exists at correct path
2. Syntax check passes (`python -c "import ast; ast.parse(open(path).read())"` for Python; `tsc --noEmit` for TypeScript)
3. If Python module: importable without errors (`python -c "from {module} import *"`)
4. If tests exist for this file: they pass
5. Update manifest: ⬜ → 🟢

---

## PROMPT TYPE 2: IMPLEMENT AN AGENT

### Trigger
A new agent needs to be implemented (D2 Scanner, D3 Classifier, D4 Documentation/Disclosure/GapAuditor, D5 Monitor).

### Template

```
You are implementing the {agent_name} agent for Conforma-AI.

MANDATORY READING (in order):
1. /handoff/04_AGENT_SPECS.md — Section {agent_section}
2. /handoff/05_EU_AI_ACT_KB.md — Sections {kb_sections}
3. /handoff/02_ARCHITECTURE_AND_STACK.md — §4 (data model) and §9 (conventions)

TASK:
Create the following files for the {agent_name} agent:

1. `backend/app/agents/{agent_file}.py` — Agent class inheriting from BaseAgent
2. `backend/app/knowledge/prompts/{prompt_file}.md` — System prompt (extract verbatim from §{agent_section} of agent specs)
3. `backend/app/schemas/agent.py` — Update with this agent's Input/Output schemas (don't overwrite existing schemas, add to file)
4. `backend/app/routers/agents.py` — Add the testing endpoint `POST /api/v1/agents/{agent_name}`
5. `backend/tests/test_{agent_name}.py` — Unit tests for the agent

The agent must:
- Validate input via Pydantic schema before any LLM call
- Use `core.gemini_client.call_pro()` or `call_flash()` per spec (NOT the SDK directly)
- Parse JSON output robustly (strip markdown fences, handle malformed JSON with one retry)
- Persist `agent_runs` row with tokens_in, tokens_out, model, status, input, output
- Log all errors with full traceback to the logger from `core.logging`
- Return a typed output object matching the schema

ACCEPTANCE CRITERIA:
{paste_acceptance_from_project_plan_day_n}

TEST CASES (mandatory):
{paste_test_cases_from_agent_specs}

OUTPUT FORMAT:
One file at a time, separated by clear "===== FILE: path =====" markers. No commentary between files.
```

### Specific instantiations

**For Scanner (D2):**
```
{agent_name} = Scanner
{agent_section} = §1
{kb_sections} = none (Scanner only inventories, doesn't classify)
{agent_file} = scanner
{prompt_file} = scanner_system
```

**For Classifier (D3):**
```
{agent_name} = Classifier
{agent_section} = §2
{kb_sections} = §1 (Omnibus context), §2 (all four risk classes)
{agent_file} = classifier
{prompt_file} = classifier_system
```

**For Documentation (D4):**
```
{agent_name} = Documentation
{agent_section} = §3
{kb_sections} = §4 (Annex IV)
{agent_file} = documentation
{prompt_file} = documentation_system
```

**For Disclosure (D4):**
```
{agent_name} = Disclosure
{agent_section} = §4
{kb_sections} = §3 (Article 50 placement standards and snippets)
{agent_file} = disclosure
{prompt_file} = disclosure_system
```

**For Gap Auditor (D4):**
```
{agent_name} = GapAuditor
{agent_section} = §5
{kb_sections} = §2 (risk classes), §4 (Annex IV gaps), §5 (penalties)
{agent_file} = gap_auditor
{prompt_file} = gap_auditor_system
```

**For Monitor (D5):**
```
{agent_name} = Monitor
{agent_section} = §6
{kb_sections} = §1 (Omnibus deadlines)
{agent_file} = monitor
{prompt_file} = monitor_system
```

### Post-execution verification
1. All 5 listed files exist
2. Agent class imports without errors
3. POST endpoint reachable and returns 200 on a valid test input
4. Output schema validates against Pydantic
5. Test suite passes
6. `agent_runs` row is created in DB after a call

---

## PROMPT TYPE 3: SETUP DATABASE / MIGRATIONS

### Trigger
D2 morning task: setup SQLAlchemy + Alembic from scratch.

### Template

```
You are setting up the database layer for Conforma-AI.

MANDATORY READING:
1. /handoff/02_ARCHITECTURE_AND_STACK.md §4 (data model with all 5 tables)
2. /handoff/06_FILES_MANIFEST.md (db/ section)

TASK:
1. Create `backend/app/db/session.py` with:
   - Async SQLAlchemy engine using `DATABASE_URL` from settings
   - `async_sessionmaker` returning AsyncSession
   - Dependency injection function `get_db()` for FastAPI

2. Create `backend/app/db/models.py` with SQLAlchemy 2.0 declarative models for:
   - `Audit`
   - `AISystem`
   - `AgentRun`
   - `Artifact`
   - `Gap`
   Match schemas in §4 of architecture doc EXACTLY (column names, types, constraints).

3. Setup Alembic:
   - `backend/alembic.ini` with `sqlalchemy.url` pulling from env via `alembic/env.py`
   - `backend/alembic/env.py` configured for async + autogenerate
   - Generate `versions/0001_initial.py` migration

4. Add a helper `scripts/run_migrations.sh` that runs `alembic upgrade head`.

REQUIREMENTS:
- All timestamps must be `TIMESTAMP WITH TIME ZONE`
- All IDs must be UUID with `server_default=text("gen_random_uuid()")` (requires pgcrypto extension — include in migration)
- Use `Mapped[type]` syntax (SQLAlchemy 2.0), not legacy `Column()`
- Foreign keys must have `ondelete` specified
- Indexes on `audit_id` in `ai_systems` and `agent_runs` for performance

OUTPUT FORMAT:
File-by-file with "===== FILE: path =====" separators. After all files, output the exact commands Eduky needs to run:
```
$ alembic init alembic   # (skip — already initialized by you)
$ alembic upgrade head
```
```

### Post-execution verification
```
$ docker compose up -d   # postgres running
$ cd backend && alembic upgrade head
# expected: "Running upgrade -> 0001_initial"
$ psql $DATABASE_URL -c "\dt"
# expected: 5 tables visible
```

---

## PROMPT TYPE 4: BUILD A FRONTEND COMPONENT

### Trigger
A component from the manifest needs implementation.

### Template

```
You are building a React component for Conforma-AI's frontend.

MANDATORY READING:
1. /handoff/02_ARCHITECTURE_AND_STACK.md §2.2 (frontend stack), §9 (conventions)
2. /handoff/04_AGENT_SPECS.md (if visualizing agent output)
3. /handoff/06_FILES_MANIFEST.md (component description)

STACK CONSTRAINTS:
- Next.js 15 App Router (not Pages Router)
- React 19 (use `use()` hook where needed)
- TypeScript strict mode — no `any`, no `@ts-ignore`
- Tailwind CSS — only utility classes, no custom CSS files
- shadcn/ui components for primitives — import from `@/components/ui/*`
- Server Components by default; only use `"use client"` if needed (state, hooks, event handlers)
- For data fetching: `fetch()` with revalidate options, OR client-side via `lib/api.ts`

ACCESSIBILITY:
- Semantic HTML (button is `<button>`, link is `<a>`, etc.)
- ARIA attributes on dynamic state changes
- Keyboard navigation must work
- Color contrast WCAG AA minimum

TASK:
Create `frontend/components/{ComponentName}.tsx` implementing:
{purpose}

Props interface:
{props_spec}

Visual requirements:
{visual_description}

States to handle:
- Loading
- Error
- Empty
- Success

OUTPUT FORMAT:
Just the .tsx content. No commentary.
```

---

## PROMPT TYPE 5: WRITE TESTS

### Trigger
A unit/integration test file needs to be created.

### Template

```
You are writing tests for Conforma-AI.

MANDATORY READING:
1. /handoff/04_AGENT_SPECS.md (test cases for the agent under test)
2. Implementation file being tested

TASK:
Create `backend/tests/test_{name}.py` with pytest tests for {file_under_test}.

REQUIREMENTS:
- Use pytest fixtures from `conftest.py` (don't redefine)
- Async tests use `@pytest.mark.asyncio`
- Mock Gemini calls using `unittest.mock.patch` on `app.core.gemini_client.call_pro` and `.call_flash`
- Tests must run in isolation (no shared state between tests)
- Each test has a docstring explaining what it verifies

TEST CASES TO INCLUDE:
{paste_test_cases}

ADDITIONAL EDGE CASES TO COVER:
- Empty input
- Malformed Gemini response (invalid JSON)
- Network error from Gemini
- DB write failure

OUTPUT FORMAT:
Just the test file content.
```

---

## PROMPT TYPE 6: WIRE LANGGRAPH ORCHESTRATOR

### Trigger
D4 critical path: building the multi-agent orchestrator.

### Template

```
You are wiring the LangGraph orchestrator for Conforma-AI.

MANDATORY READING:
1. /handoff/04_AGENT_SPECS.md (ALL sections, especially "ORCHESTRATOR" at the end)
2. /handoff/02_ARCHITECTURE_AND_STACK.md §1.1 (architecture diagram)
3. LangGraph docs: https://langchain-ai.github.io/langgraph/

TASK:
Create `backend/app/agents/orchestrator.py` implementing the audit graph.

GRAPH STRUCTURE (from agent specs):
clone_repo → scanner → classifier_batch → [documentation_batch, disclosure_batch] (parallel) → gap_auditor → compute_score → finalize

REQUIREMENTS:
- `AuditState` TypedDict matching spec
- Each node is an async function `async def {name}_node(state: AuditState) -> AuditState`
- Parallel execution of documentation and disclosure using `langgraph.constants.Send` or branch routing
- Each node yields SSE events to the `audit_id` channel (use a simple in-memory pubsub: dict[audit_id, asyncio.Queue])
- Compute_score node is DETERMINISTIC (uses `services.compliance_score`, not the LLM)
- finalize node updates the `audits` table with final compliance_score and status='completed'
- Error in any node logs to `agent_runs.error`, sets status='failed', but doesn't crash the whole graph

DELIVER:
1. `backend/app/agents/orchestrator.py`
2. `backend/app/services/sse_bus.py` (in-memory pubsub for SSE)
3. Update `backend/app/routers/audits.py` so `POST /api/v1/audits` launches the orchestrator as a background task and returns audit_id immediately

OUTPUT FORMAT:
File-by-file.
```

---

## PROMPT TYPE 7: DEPLOY TO PRODUCTION

### Trigger
D6 task: deploy backend to Vultr and frontend to Vercel.

### Template

```
You are preparing Conforma-AI for production deployment.

MANDATORY READING:
1. /handoff/02_ARCHITECTURE_AND_STACK.md §6 (deployment topology)
2. /handoff/08_EDUKY_MANUAL_TASKS.md §6 (D6 manual tasks)

TASK 1: Dockerize the backend
Create `backend/Dockerfile` with:
- Multi-stage build (builder + runtime)
- Python 3.12-slim base
- Non-root user
- HEALTHCHECK directive hitting `GET /`
- EXPOSE 8000

TASK 2: Create production Docker Compose
Create `docker-compose.prod.yml` at repo root with services:
- api (the backend Dockerfile)
- worker (same image, command: celery -A app.workers.celery_app worker)
- (postgres comes from Vultr Managed DB, not Docker)
- (redis comes from Docker on the same VM)

TASK 3: Nginx config
Create `infra/nginx/conforma-ai.conf` with:
- Reverse proxy to localhost:8000
- HTTPS via Let's Encrypt
- Proper CORS for the Vercel domain
- SSE support (proxy_buffering off, longer timeouts)

TASK 4: Vercel config
Create `frontend/vercel.json` with:
- Build command
- Output directory
- Env vars passthrough

TASK 5: Deploy script
Create `scripts/deploy.sh` that Eduky runs from his local machine:
- rsync code to Vultr
- ssh into Vultr
- docker compose pull
- docker compose up -d --build
- alembic upgrade head
- verify health endpoint

OUTPUT FORMAT:
File-by-file, then a final block with the exact sequence of commands for Eduky.
```

---

## PROMPT TYPE 8: GENERATE DEMO ASSETS

### Trigger
D7 task: video script, slides, README v1.0, cover image.

### Template (script)

```
You are writing the demo video script for Conforma-AI.

MANDATORY READING:
1. /handoff/01_BRIEF_AND_CONTEXT.md §6 (demo structure)
2. /handoff/09_DEMO_AND_SUBMISSION.md (full demo plan)

TASK:
Write the complete 2-minute video script with:
- Per-second timing
- Exact spoken voiceover (English, professional but not stiff)
- On-screen action notes (what's being shown)
- Music cue notes (energetic intro, calm middle, building climax)

Total target: 120 seconds. Hard limit: 150 seconds.

OUTPUT FORMAT:
A markdown file `docs/DEMO_SCRIPT.md` with a single table:

| Time | Voiceover | On-screen | Music |
|---|---|---|---|
| 0:00 | "On May 7, 2026..." | News headline of Omnibus deal | Suspense intro |
| ... | ... | ... | ... |
```

### Template (slides)

```
You are producing a 10-slide pitch deck for Conforma-AI to submit alongside the demo video.

MANDATORY READING:
1. /handoff/01_BRIEF_AND_CONTEXT.md (full file)
2. /handoff/02_ARCHITECTURE_AND_STACK.md §1.1 (diagram)

DELIVER:
A PowerPoint .pptx file at `docs/slides.pptx` with these 10 slides:

1. Title — Conforma-AI logo + tagline + hackathon name
2. The Moment — May 7, 2026 Omnibus deal headline
3. The Problem — 3 numbers: 27K companies, €20M fines, 2 deadlines
4. The Solution — 6 agents diagram (from §1.1)
5. Live Demo — screenshot of dashboard with score
6. Compliance Score — methodology breakdown
7. Multi-Agent Architecture — LangGraph flow
8. Built on Vultr + Gemini — sponsor logos + integration screenshots
9. Roadmap — v1 hackathon, v2 Q3 2026, v3 2027
10. Thank You — call to action + URL + GitHub

Use a clean, professional style. EU blue (#003399) and gold (#FFCC00) accents. Sans-serif fonts. Minimal text per slide (≤25 words). Always one big visual per slide.

OUTPUT FORMAT:
Generate the .pptx file using the python-pptx library or equivalent. Then output the path.
```

---

## PROMPT TYPE 9: DEBUG / TROUBLESHOOT

### Trigger
Something fails. Eduky reports the issue with logs and error message.

### Template

```
You are debugging an issue in Conforma-AI.

MANDATORY READING:
1. The relevant file(s) currently in the repo
2. /handoff/02_ARCHITECTURE_AND_STACK.md (for context on intended behavior)
3. /handoff/04_AGENT_SPECS.md (if agent-related)

REPORTED ISSUE:
{paste_eduky_report_with_logs_and_error}

ENVIRONMENT:
- D{n} of the sprint
- {local|production}

TASK:
1. Diagnose the root cause. Be specific — name the file and line if possible.
2. Propose minimum-viable fix that doesn't expand scope.
3. Provide the exact diff (file paths + before/after code blocks).
4. Provide a verification command Eduky can run to confirm the fix.

CONSTRAINTS:
- Don't refactor more than necessary
- Don't add new dependencies without flagging
- Don't change architecture decisions
- If the issue requires architectural rethinking → STOP and escalate to Eduky to consult Claude

OUTPUT FORMAT:
1. Diagnosis (1 paragraph)
2. Root cause (1 sentence)
3. Fix (diff)
4. Verification (commands)
```

---

## PROMPT TYPE 10: REFACTOR / OPTIMIZE

### Trigger
Late in the sprint, something needs polishing without changing functionality.

### Template

```
You are refactoring {target} in Conforma-AI.

REFACTOR CONSTRAINTS (hackathon mode):
- NEVER change public API surfaces
- NEVER touch agent prompts or compliance score formulas
- NEVER add new dependencies
- Only acceptable refactors during a hackathon:
  - Extract magic numbers to constants
  - Split a function >100 lines into 2-3 smaller ones
  - Rename a variable for clarity
  - Add missing type hints
  - Fix code smell flagged by linter

DO NOT:
- "Improve" UI styling without explicit user request
- Replace libraries
- Rewrite from scratch
- Add features

GOAL:
{specific_goal}

OUTPUT FORMAT:
Diff only. List each file change atomically.
```

---

## SAFETY PROMPTS

### When ChatGPT is unsure
If ChatGPT receives a request from Eduky that conflicts with anything in this handoff package, ChatGPT MUST stop and respond:

```
"Eduky, the request to {action} conflicts with {section} of {handoff_file}.
Before proceeding, confirm one of:
(a) The handoff doc is wrong → I won't proceed without Claude updating the doc.
(b) The change is intentional override → I'll note it as a deviation in the next status report.
(c) I'm misreading the conflict → please clarify."
```

Never silently override the handoff package.

### When Codex returns garbage
If Codex output:
- Hallucinates a file path not in the manifest
- Imports a library not in `requirements.txt` or `package.json`
- References AI Act articles/annex numbers without basis in `05_EU_AI_ACT_KB.md`
- Skips required acceptance criteria

→ Re-prompt with: "Your previous output violated constraint {X}. Re-read {file} and fix. Specifically: {issue}."

Do NOT accept Codex output that has any of the above issues. Quality bar > velocity.

---

## METRICS TO REPORT BACK TO EDUKY

After each Codex run, ChatGPT reports:

```
✅ Files created: [list]
✅ Acceptance criteria met: X/Y
⚠️  Open questions: [if any]
⚠️  Deviations from handoff: [if any]
⏭️  Next task in the day's plan: [task]
```

Keep it terse. Eduky is the executor, not the listener.
