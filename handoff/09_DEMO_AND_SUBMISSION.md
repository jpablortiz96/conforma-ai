# 🎬 DEMO & SUBMISSION PACKAGE

> Contains: video script (English), 10-slide deck outline, README v1.0 spec, lablab.ai submission checklist, social media announcement templates.

---

## §1 — VIDEO SCRIPT (2 minutes)

### Production specs
- **Duration:** 120 seconds (hard cap: 150s)
- **Resolution:** 1920x1080, 30fps
- **Audio:** 192kbps AAC, voiceover in English (Eduky's natural accent is fine — judges are EU-international)
- **Format:** MP4 H.264
- **Hosting:** YouTube unlisted

### Full script

| Time | Voiceover (English) | On-screen action | Music |
|---|---|---|---|
| **0:00–0:05** | *"On May 7th, 2026, the European Commission made a decision that left every AI company in Europe with one question."* | Black screen → fade in: news headline screenshot "Digital Omnibus: AI Act deadlines postponed". Subtle date stamp. | Tense intro pad |
| **0:05–0:15** | *"What do we do now? The Annex Three deadline moved to December 2027. But Article 50 transparency? Enforceable in seven months. The nudifier ban? Same."* | Three deadline cards animating in: ANNEX III → 2 DEC 2027 · ARTICLE 50 → 2 DEC 2026 · NUDIFIER BAN → 2 DEC 2026 | Pad continues, percussive accent |
| **0:15–0:25** | *"For 27,000 European companies in scope, manual compliance costs 80 thousand to 300 thousand euros. Consultancies are booked through Q4 2027. The fines? Up to 20 million euros, or 4 percent of global turnover."* | Number callouts animating: 27,000 · €80K-€300K · BOOKED · €20M / 4% | Pulse beat starts |
| **0:25–0:32** | *"Meet Conforma-AI."* | Hard cut to Conforma-AI logo + tagline "The autonomous compliance officer for the EU AI Act" | Music hits — energetic uplift |
| **0:32–0:42** | *"Six specialized agents audit your AI systems. They classify them under the EU AI Act, generate Annex IV technical documentation, draft Article 50 disclosures in five languages, and produce a compliance score zero to one hundred."* | Architecture diagram animating: Scanner → Classifier → Documentation + Disclosure (parallel) → Gap Auditor → Monitor | Beat building |
| **0:42–0:55** | *"Watch this. We point Conforma-AI at a real open source machine learning repository."* | Screen recording: Eduky in browser, pastes `https://github.com/microsoft/recommenders` URL, clicks Submit | Suspense build |
| **0:55–1:15** | *"Four minutes later: full AI system inventory, classified under specific Annex Three paragraphs. Article 50 transparency snippets in English, Italian, Spanish, French, and German. Technical documentation rendered to PDF. And a Compliance Score of 42 out of 100, with a prioritized remediation plan and estimated fine exposure of 7.2 million euros."* | Screen recording (sped up 3x): dashboard fills with results, score ring animates to 42, PDF preview, multi-language tabs | Continues building |
| **1:15–1:25** | *"Every agent runs Gemini 3.1 Pro for reasoning and Gemini 3 Flash for speed. The backend is on Vultr Cloud Compute, Frankfurt. The frontend is on Vercel. Database is Vultr Managed Postgres."* | Stack diagram with Vultr + Gemini logos prominent. Screenshots flash: Vultr dashboard, AI Studio usage chart | Beat steady |
| **1:25–1:40** | *"This is not a chatbot wrapped in a prompt. This is a multi-agent system with structured outputs, deterministic compliance scoring, and citations to specific articles of Regulation EU 2024 slash 1689."* | Show: code snippet of Compliance Score formula · sample JSON output of Classifier with "Annex III §4(a)" citation | Beat continues |
| **1:40–1:50** | *"Conforma-AI: built solo by Eduky in Cali, for the AI Agent Olympics at Milan AI Week 2026."* | Eduky's name + location + hackathon logos | Beat resolving |
| **1:50–2:00** | *"Try it. Conforma-ai.vercel.app. The code is open source on GitHub. The clock to December 2026 is ticking."* | Final CTA card: URL + GitHub link + countdown widget showing days until 2 Dec 2026 | Triumphant close |

### Editing notes
- **Cut aggressively.** Every shot is on screen ≤4 seconds.
- **Speed up loading spinners.** Real audit takes ~3 min; show it as 10 seconds.
- **No transitions longer than 0.5s.** No fade-outs to black mid-video.
- **Watermark:** small "@eduky_co" bottom-right throughout (you're building the personal brand).
- **End slate:** 2 seconds of clean URL + GitHub link, no music. Lets the eye rest.

---

## §2 — SLIDE DECK (10 slides)

### Production specs
- **Format:** PowerPoint (.pptx) or Google Slides exported to PDF
- **Aspect:** 16:9
- **Style:** Clean, EU-blue (#003399) + gold accent (#FFCC00), one big visual per slide, ≤25 words text
- **Font:** Inter (free Google Font) — fallback to Arial/Helvetica
- **Page numbers:** bottom right, subtle
- **Footer:** "Conforma-AI · AI Agent Olympics 2026 · @eduky_co"

### Slide outline

**Slide 1 — TITLE**
- Centered: large "Conforma-AI" wordmark
- Subtitle: "The autonomous compliance officer for the EU AI Act"
- Bottom: "AI Agent Olympics · Milan AI Week 2026"
- Author: "Juan Pablo Enríquez Ortiz · @eduky_co"

**Slide 2 — THE MOMENT**
- Background: subtle EU stars pattern
- Center: headline-style "7 May 2026: Digital Omnibus deal reshapes AI Act"
- Below: 3 small cards with the 3 deadlines (Annex III, Article 50, Nudifier Ban)
- Footnote: "Source: European Commission press release, 7 May 2026"

**Slide 3 — THE PROBLEM**
- Three columns, each with a giant number + label:
  - "27,000" — companies in EU scope
  - "€80K–€300K" — per company compliance cost
  - "€20M / 4%" — maximum fine
- Caption below: "Specialized consultancies booked through Q4 2027. Manual audit takes 6+ months."

**Slide 4 — THE SOLUTION**
- Visual: 6-agent architecture diagram (the one from `02_ARCHITECTURE_AND_STACK.md` §1.1, simplified)
- Title: "Six autonomous agents. End-to-end audit."
- Brief tag under each agent (3-4 words max)

**Slide 5 — LIVE DEMO**
- Full-bleed screenshot: dashboard with Compliance Score Ring at 42/100, list of AI systems with risk badges, agent status indicators
- Top-left badge: "LIVE PRODUCT"
- Bottom: URL "conforma-ai.vercel.app"

**Slide 6 — COMPLIANCE SCORE METHODOLOGY**
- Title: "Score is deterministic and transparent"
- Formula visual:
  ```
  Base: 100
  – 25 per CRITICAL gap
  – 10 per HIGH gap
  – 4 per MEDIUM gap
  – 1 per LOW gap
  – 20 per HIGH_RISK system without Annex IV
  – 10 per LIMITED_RISK without Article 50 disclosure
  Min: 0 · Max: 100
  ```
- Caption: "Published in our README. Auditable by external compliance officers."

**Slide 7 — MULTI-AGENT ARCHITECTURE**
- Title: "Six specialists, not one generalist"
- Visual: LangGraph diagram showing parallel branches (Documentation + Disclosure run simultaneously)
- Tech stack icons row: LangGraph · FastAPI · Postgres · Redis · Next.js · WeasyPrint
- Caption: "Built with LangGraph for production-grade orchestration"

**Slide 8 — BUILT ON VULTR + GEMINI**
- Top half: Vultr logo + 3 mini-screenshots (VM dashboard · Managed DB · Coolify)
- Bottom half: Google Gemini logo + AI Studio usage stats screenshot
- Caption: "Backend, database, queue, storage: all on Vultr Frankfurt. Reasoning: Gemini 3.1 Pro. Speed: Gemini 3 Flash."

**Slide 9 — ROADMAP**
- Three columns:
  - **v1.0 — May 2026 (now):** Compliance audit, 6 agents, 5 languages, single-tenant
  - **v2.0 — Q3 2026:** Multi-tenant SaaS, integration with Jira/Notion, continuous monitoring with webhooks
  - **v3.0 — 2027:** Pre-certified compliance package partner with EU notified bodies, support for AI Liability Directive
- Caption: "Pricing target: €5K/year per company. ROI: ~95% reduction vs manual consulting."

**Slide 10 — THANK YOU + CTA**
- Center: "Try Conforma-AI today"
- URL: conforma-ai.vercel.app
- GitHub: github.com/jpablortiz96/conforma-ai
- Bottom: "Juan Pablo Enríquez Ortiz · Cali → Milan · @eduky_co"
- Tiny: "Built solo in 7 days for AI Agent Olympics 2026"

---

## §3 — README v1.0 SPECIFICATION

Final structure for `README.md` at submission. Codex generates this on D7 based on this spec.

```markdown
<div align="center">

# Conforma-AI 🇪🇺

### The autonomous compliance officer for the EU AI Act.
### Audit. Classify. Document. — In hours, not months.

[![Status](https://img.shields.io/badge/status-hackathon%20build-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Powered by Vultr](https://img.shields.io/badge/powered%20by-Vultr-007BFC)]()
[![Built with Gemini](https://img.shields.io/badge/built%20with-Gemini%203.1-4285F4)]()
[![Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://conforma-ai.vercel.app)

[**Live Demo →**](https://conforma-ai.vercel.app) · [**2-min Video →**](https://youtu.be/XXXX) · [**lablab.ai →**](https://lablab.ai/event/ai-agent-olympics/conforma-ai)

</div>

---

![Conforma-AI Hero](./docs/screenshots/live_audit.png)

## The Moment

On **7 May 2026** — six days before this project began — the EU's Digital Omnibus deal reshaped the AI Act compliance timeline:

| Provision | Deadline |
|---|---|
| Annex III high-risk systems | **2 December 2027** (postponed from August 2026) |
| Article 50 transparency obligations | **2 December 2026** |
| Nudifier ban (Article 5(1)(i)) | **2 December 2026** |
| Penalties | Up to **€20M or 4% of global turnover** |

The market math:
- ~27,000 EU companies in scope
- Manual compliance: €80K–€300K per company
- Specialized AI Act consultancies: booked through Q4 2027

## How Conforma-AI Works

Six autonomous agents audit a code repository and produce an Annex IV-grade compliance package — without a human in the loop.

```
                  ┌──────────┐
                  │ SCANNER  │ — inventory candidate AI systems
                  └─────┬────┘
                        ▼
                  ┌────────────┐
                  │ CLASSIFIER │ — map to EU AI Act risk class
                  └─────┬──────┘
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
       ┌──────────┐  ┌───────┐  ┌────────┐
       │  DOCS    │  │DISCL. │  │  GAP   │
       └────┬─────┘  └───┬───┘  │AUDITOR │
            │            │      └────┬───┘
            └────────────┼──────────┘
                         ▼
                   ┌──────────┐
                   │ MONITOR  │ — ongoing post-market checks
                   └──────────┘
```

| Agent | Job | Model |
|---|---|---|
| Scanner | Inventories AI systems in a codebase | Gemini 3 Flash |
| Classifier | Maps each system to AI Act risk class with article citation | Gemini 3.1 Pro |
| Documentation | Generates Annex IV technical docs (PDF) | Gemini 3.1 Pro |
| Disclosure | Drafts Article 50 transparency notices in EN/IT/ES/FR/DE | Gemini 3 Flash |
| Gap Auditor | Identifies gaps + computes Compliance Score 0–100 | Gemini 3.1 Pro |
| Monitor | Tracks regulatory updates + deadline approaches | Gemini 3 Flash |

## What You Get

Drop in a GitHub repo URL. ~4 minutes later:

✅ Full inventory of AI systems found
✅ Risk classification for each, citing specific Articles/Annexes
✅ Annex IV-compliant technical documentation as PDF
✅ Article 50 transparency snippets in 5 EU languages
✅ Compliance Score 0–100 with deterministic methodology
✅ Estimated fine exposure in euros
✅ Prioritized remediation plan with effort estimates

## Tech Stack

| Layer | Choice |
|---|---|
| **Multi-agent orchestration** | LangGraph 0.2.45 |
| **Reasoning core** | Google Gemini 3.1 Pro |
| **Fast inference** | Google Gemini 3 Flash |
| **Backend** | FastAPI 0.115 · SQLAlchemy 2.0 async · Celery |
| **Database** | PostgreSQL 16 (Vultr Managed) |
| **Cache / Queue** | Redis 7 |
| **PDF generation** | WeasyPrint + Jinja2 |
| **Frontend** | Next.js 15 App Router · TypeScript strict · Tailwind · shadcn/ui |
| **Infrastructure** | **Vultr Cloud Compute (Frankfurt) + Coolify** |
| **Frontend hosting** | Vercel |
| **Observability** | Langfuse |

## Compliance Score Methodology

The score is **deterministic**, not LLM-judged. Agents identify gaps; the score is computed by formula:

```
Base:    100
Penalty: −25 per CRITICAL gap
         −10 per HIGH gap
         −4  per MEDIUM gap
         −1  per LOW gap
         −20 per HIGH_RISK system without Annex IV
         −10 per LIMITED_RISK system without Article 50 disclosure
         −50 per UNACCEPTABLE system found

Floor: 0  ·  Ceiling: 100
```

Methodology is auditable, reproducible, and published. External compliance officers can validate every score.

## Try It

🌐 **Live demo:** https://conforma-ai.vercel.app
🎬 **Video walkthrough:** https://youtu.be/XXXX
📦 **Self-hosted setup:** see [`docs/SETUP.md`](./docs/SETUP.md)
🚀 **Deployment guide:** see [`docs/DEPLOY.md`](./docs/DEPLOY.md)

## Screenshots

| | |
|---|---|
| ![Dashboard](./docs/screenshots/live_audit.png) | ![Score Ring](./docs/screenshots/compliance_score.png) |
| Live audit dashboard | Compliance score visualization |
| ![PDF](./docs/screenshots/annex_iv_pdf.png) | ![Multilang](./docs/screenshots/disclosures_multilang.png) |
| Generated Annex IV PDF | Article 50 disclosures (5 languages) |

## Hackathon Tracks Submitted

This project is competing for:
- **Best Use of Vultr** — backend, database, queue, deployment all on Vultr Cloud Compute (Frankfurt)
- **Best Use of Google Gemini** — Gemini 3.1 Pro orchestrator + Gemini 3 Flash agent fleet

## Roadmap

- **v1.0 (May 2026, this hackathon):** Single-tenant audit, 6 agents, 5 languages, public source repos
- **v2.0 (Q3 2026):** Multi-tenant SaaS, Jira/Notion/Slack integrations, real-time monitoring with webhooks, support for private repos
- **v3.0 (2027):** Pre-certified compliance package partnership with EU notified bodies, AI Liability Directive support

## Architecture Decisions

For the reasoning behind every major choice (LangGraph over CrewAI, FastAPI over Flask, Postgres over MongoDB, SSE over WebSockets, etc.), see [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

## Local Development

See [`docs/SETUP.md`](./docs/SETUP.md) for full instructions.

Quick start:
```bash
git clone https://github.com/jpablortiz96/conforma-ai.git
cd conforma-ai
docker compose up -d        # postgres + redis

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# in another terminal
cd frontend
npm install
npm run dev
```

## Contributing

This is a hackathon submission. After awards (post 20 May 2026), the project transitions to OSS. PRs welcome on:
- Additional language support (Polish, Dutch, Portuguese, Swedish prioritized)
- Coverage for Annex I product categories
- Integration adapters (Jira, Linear, Notion)

## License

MIT — see [LICENSE](./LICENSE)

## Author

**Juan Pablo Enríquez Ortiz** ([@eduky_co](https://eduky.co))
Senior Productivity & Applications · Banco de Occidente
Industrial Engineer · AI/Data Educator
Cali, Colombia → Milan, Italy (in spirit)

Built solo in 7 days for AI Agent Olympics 2026 @ Milan AI Week.

---

## Acknowledgments

- **Anthropic's Claude** — architectural co-pilot for this project
- **OpenAI's ChatGPT + Codex** — execution coordination
- **lablab.ai** — for organizing AI Agent Olympics
- **Vultr** — for compute infrastructure
- **Google** — for Gemini 3.1 Pro and Flash access
- The **European Commission AI Office** — for clear regulatory text

---

_If the AI Act is the rule, Conforma-AI is the auditor that ensures you're never out of compliance._
```

---

## §4 — LABLAB.AI SUBMISSION CHECKLIST

Fields you'll fill on the lablab.ai project submission form. Fill them in this order.

### 4.1 Basic info

| Field | Value to enter |
|---|---|
| **Project Title** | `Conforma-AI` |
| **Tagline** (≤80 chars) | `The autonomous compliance officer for the EU AI Act.` |
| **Short Description** (~280 chars) | `Six AI agents audit your codebase against the EU AI Act in hours, not months. Compliance Score 0-100, Annex IV PDFs, Article 50 disclosures in 5 languages. Built for the moment the Omnibus deal of 7 May 2026 reshaped Europe's AI regulation timeline.` |
| **Long Description** (~500 words) | _See template below_ |

### 4.2 Long description template (paste this, edit details if needed)

```
Conforma-AI is a multi-agent autonomous compliance system for the EU AI Act (Regulation EU 2024/1689), built solo in 7 days for the AI Agent Olympics at Milan AI Week 2026.

THE MOMENT
On 7 May 2026 — six days before this project began — the EU's Digital Omnibus deal postponed the Annex III high-risk system deadlines to December 2027, but kept the Article 50 transparency obligations and the new nudifier ban for December 2026. Every European company with AI is suddenly recalibrating its compliance roadmap.

THE MARKET
~27,000 EU companies are in scope. Manual compliance costs €80K–€300K per company. Specialized consultancies are booked through Q4 2027. Penalties reach €20M or 4% of global turnover.

THE SOLUTION
Six specialized agents, orchestrated via LangGraph, ingest a code repository and produce a complete EU AI Act compliance package:
1. SCANNER — inventories AI systems in the codebase
2. CLASSIFIER — maps each system to a risk class (Unacceptable / High / Limited / Minimal) with specific Article and Annex citations
3. DOCUMENTATION — generates Annex IV technical documentation as PDF
4. DISCLOSURE — drafts Article 50 user-facing transparency notices in English, Italian, Spanish, French, and German
5. GAP AUDITOR — computes a deterministic Compliance Score 0-100 and a prioritized remediation plan with estimated fine exposure
6. MONITOR — tracks regulatory updates and deadline approaches

THE STACK
Backend: FastAPI + LangGraph + SQLAlchemy 2.0 async, all deployed on Vultr Cloud Compute (Frankfurt). Postgres 16 on Vultr Managed Database. Redis 7 for queue. WeasyPrint + Jinja2 for PDF generation. Coolify for automated deploys.

Reasoning: Gemini 3.1 Pro for orchestration, Classifier, Documentation, and Gap Auditor. Gemini 3 Flash for Scanner, Disclosure, and Monitor. All accessed through the unified google-genai SDK.

Frontend: Next.js 15 App Router with TypeScript strict mode, Tailwind, shadcn/ui, deployed on Vercel.

WHAT'S DIFFERENT
- This is not a chatbot wrapped around a prompt. Six agents with distinct responsibilities, structured outputs, JSON schemas, and database persistence.
- Compliance Score is deterministic — agents identify gaps, score is computed by published formula. External compliance officers can audit our scoring.
- Outputs are professional artifacts: Annex IV PDF with cover page, table of contents, 9 sections, gap appendix, regulation citations. Not just "AI thoughts" displayed in a chat.
- The Omnibus deal of 7 May 2026 is woven into every agent's reasoning — deadlines, exemptions, and the new nudifier ban are all current.

ROADMAP
v1.0 ships at this hackathon. v2.0 (Q3 2026) adds multi-tenancy, Jira/Notion/Slack integrations, and real-time monitoring. v3.0 (2027) partners with EU notified bodies for pre-certified compliance packages.

BUILT BY
Juan Pablo Enríquez Ortiz (@eduky_co) — solo founder from Cali, Colombia. Industrial Engineer, AI/Data educator, Senior Productivity at Banco de Occidente.

TRY IT
Live demo: https://conforma-ai.vercel.app
GitHub: https://github.com/jpablortiz96/conforma-ai
2-minute video: https://youtu.be/XXXX
```

### 4.3 Tags / Categories
- **Technology tags:** `AI Agents`, `LangGraph`, `FastAPI`, `Next.js`, `PostgreSQL`, `Multi-Agent`, `Compliance`, `EU AI Act`, `RegTech`, `LegalTech`
- **Sponsor tracks selected:** `Vultr Best Use`, `Google Gemini Best Use`
- **Olympic tracks selected:** `Agentic Workflows`, `Enterprise Utility`, `Collaborative Systems`

### 4.4 Assets to upload

| Asset | File | Path on your machine |
|---|---|---|
| Cover image (1920x1080) | `cover.png` | `D:/conforma-ai/docs/cover.png` |
| Video URL | YouTube unlisted | (paste URL) |
| GitHub repo URL | Public link | `https://github.com/jpablortiz96/conforma-ai` |
| Demo URL | Vercel deployed | `https://conforma-ai.vercel.app` |
| Slides | PDF | `D:/conforma-ai/docs/slides.pdf` |

### 4.5 Team
- Solo project. List yourself as the only member.
- Bio: short, professional, in English. Example:
  > "Solo founder, full-stack engineer, AI/data educator. Senior Productivity & Applications at Banco de Occidente. Based in Cali, Colombia. Building Conforma-AI for European enterprises navigating the AI Act."

### 4.6 Pre-submit checklist
Run this list mentally before clicking submit:

- [ ] Demo URL responds 200 from a fresh browser (no cache)
- [ ] Full audit pipeline executes end-to-end without errors
- [ ] PDF Annex IV downloads correctly
- [ ] GitHub repo is **public**, README v1.0 visible, no `.env` files committed
- [ ] Video plays on YouTube (unlisted setting confirmed)
- [ ] All asset files <50MB each (lablab.ai limit)
- [ ] Long description has no typos
- [ ] Sponsor tracks both checked
- [ ] Cover image has no broken layout
- [ ] Slides PDF opens correctly on a different device

### 4.7 Final submission moment
Submit at least **4 hours before** the deadline (so target: by 14:00 UTC on 20 May for an 18:00 UTC deadline). This leaves buffer if anything fails.

---

## §5 — SOCIAL MEDIA ANNOUNCEMENT TEMPLATES

### 5.1 LinkedIn post (English, primary audience)

```
🇪🇺 Just submitted Conforma-AI to the AI Agent Olympics at Milan AI Week 2026.

On 7 May 2026, the EU's Digital Omnibus deal reshaped the AI Act timeline. ~27,000 European companies are now recalibrating their compliance roadmaps. Manual audits cost €80K–€300K per company. Specialized consultancies are booked through Q4 2027.

Conforma-AI is an autonomous compliance officer for the EU AI Act. Six specialized agents — orchestrated via LangGraph, powered by Gemini 3.1 Pro and Gemini 3 Flash — audit a code repository and produce:

→ Full inventory of AI systems
→ Risk classification with citations to specific Articles and Annexes
→ Annex IV technical documentation as PDF
→ Article 50 transparency snippets in EN/IT/ES/FR/DE
→ Deterministic Compliance Score 0–100
→ Prioritized remediation plan with estimated fine exposure

Built solo in 7 days on Vultr Cloud Compute (Frankfurt) + Vercel + Google Gemini.

Try it: https://conforma-ai.vercel.app
GitHub: https://github.com/jpablortiz96/conforma-ai
2-min demo: https://youtu.be/XXXX

Special thanks to @lablab.ai for organizing, @Vultr for infrastructure, and Google for Gemini API access.

#EUAIAct #AICompliance #RegTech #LegalTech #MultiAgent #LangGraph #Gemini #Vultr #AIAgentOlympics #MilanAIWeek
```

### 5.2 X / Twitter thread (5 tweets)

**Tweet 1:**
```
🇪🇺 Just shipped Conforma-AI to the AI Agent Olympics 2026.

It's a multi-agent autonomous compliance system for the EU AI Act. 6 specialized agents audit your codebase in minutes, not months.

Demo: conforma-ai.vercel.app
🧵 1/5
```

**Tweet 2:**
```
The trigger: on 7 May 2026, the EU Digital Omnibus deal reshaped the AI Act timeline.

Annex III HIGH_RISK: postponed to Dec 2027
Article 50 transparency: still Dec 2026
Nudifier ban: new, also Dec 2026

Every EU company with AI is recalibrating right now.
2/5
```

**Tweet 3:**
```
The agents:

→ Scanner: finds AI in your repo
→ Classifier: maps to risk class with article citations
→ Documentation: generates Annex IV PDF
→ Disclosure: drafts Article 50 notices in 5 languages
→ Gap Auditor: deterministic Compliance Score 0-100
→ Monitor: tracks deadlines

3/5
```

**Tweet 4:**
```
Stack:
🧠 Gemini 3.1 Pro (reasoning) + Gemini 3 Flash (speed)
🛠 LangGraph + FastAPI + SQLAlchemy 2.0 async
🇩🇪 Vultr Cloud Compute (Frankfurt) + Managed Postgres
⚡️ Next.js 15 + Tailwind + shadcn on Vercel
📄 WeasyPrint + Jinja2 for PDFs

Solo build, 7 days.
4/5
```

**Tweet 5:**
```
🌐 conforma-ai.vercel.app
📦 github.com/jpablortiz96/conforma-ai
🎬 youtu.be/XXXX

Big shoutout to @lablab_ai @Vultr @googleaistudio for the resources.

This is for the 27,000 EU companies trying to figure out what comes next.

5/5 🙌
```

### 5.3 Instagram post (Spanish, your LATAM audience)

Image: cover de Conforma-AI

```
🇪🇺 ¡Acabo de submitar Conforma-AI al AI Agent Olympics de Milán!

Conforma-AI es un sistema autónomo multi-agente que audita el cumplimiento de la EU AI Act (la ley europea de IA). 6 agentes especializados con Gemini 3.1 Pro y Vultr.

¿Qué hace? En lugar de pagar €100K a una consultora para evaluar tu compliance manualmente, le pasas tu repo de GitHub y en 4 minutos tienes:
✅ Inventario de todos los sistemas IA
✅ Clasificación de riesgo bajo el AI Act
✅ Documentación técnica Anexo IV en PDF
✅ Snippets de transparencia en 5 idiomas
✅ Score 0-100 con plan de acción

Hecho solo, en 7 días. Esto es lo que pasa cuando combinas un cerebro arquitectónico potente (Claude) con un ejecutor disciplinado (ChatGPT + Codex) y mucha cafeína colombiana ☕️.

Link en bio al demo en vivo.

#IA #AIAct #Compliance #LegalTech #LATAMTech #SoloFounder #Hackathon #MilanAIWeek
```

### 5.4 Facebook (Spanish, casual)

```
🚀 Nuevo hito: acabo de terminar Conforma-AI para el hackathon más grande de IA en Europa (Milan AI Week 2026).

7 días, una persona, 6 agentes IA trabajando coordinados para resolver un problema de €5K millones al año: el cumplimiento de la nueva ley europea de inteligencia artificial.

Si te interesa el demo, link en bio.

Gracias a todos los que me han seguido en esta semana de horarios locos 🙏
```

### 5.5 Skool community announcement (Spanish)

```
🎯 Equipo de la community, update importante:

Acabo de submitar mi segundo hackathon en menos de 30 días: Conforma-AI al AI Agent Olympics de Milán.

¿Qué aprendí en este sprint que les puedo enseñar en sesión futura?

1. Cómo clasificar hackathons en 4 tipos (Creative vs Enterprise vs Platform vs Hybrid) y por qué importa
2. Cómo usar Claude + ChatGPT + Codex como "trinity" (cerebro + coordinador + ejecutor)
3. Multi-agent systems con LangGraph en producción
4. Deployment en Vultr con Coolify (mucho más simple que Kubernetes)
5. Gemini 3.1 Pro como reasoning engine ¿vale la pena vs GPT-5.5?

¿Quieren que prepare una masterclass de esto en junio? Reaccionen con 🔥 si sí.

Si ganamos algo, lo celebramos juntos 💪
```

---

## §6 — POST-SUBMISSION CHECKLIST (after clicking submit)

- [ ] Screenshot of confirmation page (in case lablab.ai has glitches later)
- [ ] Verify submission shows in lablab.ai project listing
- [ ] Post on LinkedIn
- [ ] Post X thread
- [ ] Post Instagram
- [ ] Post Facebook
- [ ] Update Skool community
- [ ] Reply to any DMs that come in
- [ ] **CLOSE LAPTOP**
- [ ] **EAT**
- [ ] **SLEEP**

The next morning (21 May): start VaquitaAI with full energy. June 6 deadline.

---

## 🏆 IF YOU WIN

Awards ceremony is **20 May at Milan AI Week**. You won't be there physically; lablab.ai handles remote winners.

If Conforma-AI wins Vultr Best Use or Gemini Best Use:
1. Acknowledge on social immediately (template: "🏆 Conforma-AI won [track]! ...")
2. Update README with winner badge
3. Email the sponsor contact to coordinate prize payment
4. Update LinkedIn headline with "Winner — Vultr Best Use Award · AI Agent Olympics 2026"
5. Save the moment — record a quick video reaction to share with your audience

If you don't win: still valuable. You shipped a real product in 7 days. Use it to convert your audience to Skool members and start v2.0 conversations with potential B2B customers.

Either way: **mission accomplished.**
