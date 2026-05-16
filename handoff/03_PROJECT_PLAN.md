# 📅 PLAN DE SPRINT — 8 DÍAS

> Cada día tiene: objetivo, tareas atómicas, archivos involucrados, acceptance criteria, y handoff al siguiente día.
> **Total estimado:** ~40h en 8 días. Reserva de 5h para imprevistos.

---

## ⏱️ TIMELINE GLOBAL

| Día | Fecha | Horas | Objetivo macro |
|---|---|---|---|
| D1 | Mié 13 May | 3h | Smoke test: 1 agente (Classifier) end-to-end local |
| D2 | Jue 14 May | 3h | Scanner agent + DB schema + Alembic |
| D3 | Vie 15 May | 3h | RAG sobre AI Act + Classifier mejorado |
| D4 | Sáb 16 May | 10h | Documentation + Disclosure + Gap Auditor + LangGraph |
| D5 | Dom 17 May | 10h | Frontend completo + PDF generation + Monitor agent |
| D6 | Lun 18 May | 4h | Deploy producción Vultr + Vercel + caso demo real |
| D7 | Mar 19 May | 4h | Video demo + slides + README final |
| D8 | Mié 20 May | 3h | Buffer + submission lablab.ai |
| **Total** | | **40h** | |

---

## D1 — MIÉ 13 MAYO · CLASSIFIER END-TO-END

### Objetivo
Validar que el stack (FastAPI + Gemini + Next.js) funciona end-to-end con UN solo agente (Classifier), corriendo localmente. **No deploy todavía.**

### Tareas atómicas

| # | Tarea | Quién | Tiempo | Archivos |
|---|---|---|---|---|
| D1.1 | Cuentas + créditos pre-flight | Eduky | 15min | — (ver `08_EDUKY_MANUAL_TASKS.md` §1) |
| D1.2 | Provisionar Vultr VM Frankfurt | Eduky | 20min | — |
| D1.3 | Setup base server (apt, postgres, redis, ufw) | Eduky (script) | 10min | — |
| D1.4 | Crear repo GitHub + .gitignore + LICENSE + README v0.1 | Codex | 15min | `README.md`, `.gitignore`, `LICENSE` |
| D1.5 | Crear estructura de carpetas del monorepo | Codex | 5min | (estructura completa) |
| D1.6 | Setup backend: venv, requirements.txt, config.py | Codex | 15min | `backend/requirements.txt`, `backend/app/core/config.py`, `backend/.env.example` |
| D1.7 | Crear `gemini_client.py` wrapper | Codex | 10min | `backend/app/core/gemini_client.py` |
| D1.8 | Crear KB mínima del AI Act | Codex | 10min | `backend/app/knowledge/eu_ai_act_minimal.py` |
| D1.9 | Crear `main.py` con endpoint Classifier smoke test | Codex | 15min | `backend/app/main.py` |
| D1.10 | Levantar Docker Compose local (postgres + redis) | Codex + Eduky | 5min | `docker-compose.yml` |
| D1.11 | Setup frontend Next.js 15 + shadcn/ui | Codex + Eduky | 15min | `frontend/*` |
| D1.12 | Crear `frontend/app/page.tsx` con UI demo Classifier | Codex | 20min | `frontend/app/page.tsx` |
| D1.13 | Smoke test integral con 4 casos | Eduky | 10min | — |
| D1.14 | Commit final + push a main | Eduky | 5min | — |

### Acceptance criteria (todos deben ✅)

- [ ] `curl http://localhost:8000/` returns `{"status":"operational",...}`
- [ ] `POST /api/v1/agents/classifier` con un AI system description returns valid JSON con `risk_class`, `primary_article`, `reasoning`, `deadline`, `confidence`
- [ ] Los 4 casos de test smoke producen clasificaciones razonables:
  - "Bank CV ranking" → HIGH_RISK
  - "Password reset chatbot" → LIMITED_RISK
  - "Real-time facial recognition shoplifter" → HIGH_RISK o UNACCEPTABLE
  - "Email spam filter" → MINIMAL_RISK
- [ ] Frontend en `localhost:3000` muestra la UI y el resultado de clasificación
- [ ] Repo público en GitHub con README v0.1 visible y professional
- [ ] Commit con mensaje `feat(D1): classifier agent end-to-end with frontend`

### Handoff a D2
- Sistema base levanta correctamente con un comando
- Documentar IP de Vultr VM en `.env.example` como comentario para uso futuro
- API key de Gemini guardada en password manager
- Eduky reporta horas reales invertidas

---

## D2 — JUE 14 MAYO · SCANNER AGENT + DB SCHEMA

### Objetivo
Implementar el primer agente de "ingestión" (Scanner) que recibe URL de repo GitHub público, lo clona, y produce un inventario de candidate AI systems. Setup completo de la base de datos con Alembic.

### Tareas atómicas

| # | Tarea | Quién | Tiempo | Archivos |
|---|---|---|---|---|
| D2.1 | Crear modelos SQLAlchemy de las 5 tablas | Codex | 25min | `backend/app/db/models.py`, `backend/app/db/session.py` |
| D2.2 | Setup Alembic + generar primera migración | Codex + Eduky | 15min | `backend/alembic/`, `backend/alembic.ini` |
| D2.3 | Aplicar migración a Postgres local | Eduky | 5min | — |
| D2.4 | Crear `BaseAgent` abstract class | Codex | 10min | `backend/app/agents/base.py` |
| D2.5 | Crear `repo_cloner.py` service | Codex | 15min | `backend/app/services/repo_cloner.py` |
| D2.6 | Implementar Scanner agent | Codex | 30min | `backend/app/agents/scanner.py`, `backend/app/knowledge/prompts/scanner_system.md` |
| D2.7 | Crear endpoint `POST /api/v1/agents/scanner` | Codex | 15min | `backend/app/routers/agents.py` |
| D2.8 | Tests unitarios del Scanner | Codex | 20min | `backend/tests/test_scanner.py` |
| D2.9 | Probar Scanner contra 3 repos reales | Eduky | 15min | — |
| D2.10 | Commit + push | Eduky | 5min | — |

### Acceptance criteria

- [ ] Migración Alembic crea las 5 tablas correctamente
- [ ] `POST /api/v1/agents/scanner` con `{"repo_url": "https://github.com/rasahq/rasa"}` devuelve lista de AI systems candidatos
- [ ] Cada AI system tiene: `name`, `description`, `source_files`
- [ ] Tests Scanner pasan (`pytest backend/tests/test_scanner.py`)
- [ ] Persistencia en DB: cada run del Scanner crea row en `audits` + N rows en `ai_systems`
- [ ] No memory leaks ni temp dirs huérfanos (cleanup verificado)

### Repos de prueba D2

| Repo | Tamaño | Sistemas IA esperados |
|---|---|---|
| `https://github.com/karpathy/llm.c` | Pequeño | 1 (educational LLM) |
| `https://github.com/rasahq/rasa` | Mediano | 3-5 (chatbot framework) |
| `https://github.com/microsoft/recommenders` | Grande | 5-8 (recommender systems) |

### Handoff a D3
- DB poblada con datos reales del primer Scanner run
- Scanner output JSON schema documentado en `04_AGENT_SPECS.md`

---

## D3 — VIE 15 MAYO · RAG + CLASSIFIER MEJORADO

### Objetivo
Reemplazar la KB mínima por una knowledge base completa del AI Act con búsqueda semántica. Mejorar el Classifier para citar artículos exactos con references.

### Tareas atómicas

| # | Tarea | Quién | Tiempo | Archivos |
|---|---|---|---|---|
| D3.1 | Expandir KB con contenido completo del AI Act | Codex | 30min | `backend/app/knowledge/eu_ai_act_kb.py`, `annex_iii_categories.py`, `article_50_requirements.py`, `annex_iv_template.py` |
| D3.2 | Refactor Classifier para usar KB completa vía prompt context | Codex | 30min | `backend/app/agents/classifier.py`, `backend/app/knowledge/prompts/classifier_system.md` |
| D3.3 | Endpoint `GET /api/v1/ai-act/risk-classes` + Annex III | Codex | 15min | `backend/app/routers/health.py` (knowledge routes) |
| D3.4 | Encadenar Scanner → Classifier en un endpoint combinado | Codex | 20min | `backend/app/routers/audits.py` (POST /audits) |
| D3.5 | Tests Classifier con 10 casos edge | Codex | 25min | `backend/tests/test_classifier.py` |
| D3.6 | Commit + push | Eduky | 5min | — |

### Acceptance criteria

- [ ] Classifier ahora cita artículos específicos del Annex III con número de párrafo
- [ ] Test suite: 10 casos cubriendo las 4 risk classes con razonamiento verificado
- [ ] `POST /api/v1/audits` flow: recibe URL → Scanner inventa → Classifier clasifica cada uno → devuelve audit_id con todos los AI systems persistidos
- [ ] Reasoning del Classifier en cada caso menciona el Omnibus deal cuando aplica para HIGH_RISK

### Handoff a D4
- KB completa
- Dos agentes encadenados funcionando

---

## D4 — SÁB 16 MAYO · DOCUMENTATION + DISCLOSURE + GAP AUDITOR + LANGGRAPH

### Objetivo
Implementar los 3 agentes restantes (Documentation, Disclosure, Gap Auditor) y orquestarlos con LangGraph. **Día más pesado del sprint.**

### Tareas atómicas (10h)

| # | Tarea | Quién | Tiempo | Archivos |
|---|---|---|---|---|
| D4.1 | Implementar Documentation agent | Codex | 60min | `backend/app/agents/documentation.py`, prompts |
| D4.2 | Templates Jinja2 para PDF Annex IV | Codex | 45min | `backend/app/templates/pdf/annex_iv.html`, `styles.css` |
| D4.3 | Service `pdf_generator.py` con WeasyPrint | Codex | 30min | `backend/app/services/pdf_generator.py` |
| D4.4 | Implementar Disclosure agent (multilenguaje) | Codex | 45min | `backend/app/agents/disclosure.py`, prompts |
| D4.5 | Implementar Gap Auditor agent | Codex | 60min | `backend/app/agents/gap_auditor.py`, prompts |
| D4.6 | Service `compliance_score.py` (cálculo 0-100) | Codex | 30min | `backend/app/services/compliance_score.py` |
| D4.7 | Orquestador LangGraph | Codex | 90min | `backend/app/agents/orchestrator.py` |
| D4.8 | Endpoint `POST /api/v1/audits` actualizado para ejecutar grafo completo async | Codex | 30min | `backend/app/routers/audits.py` |
| D4.9 | SSE endpoint para streaming | Codex | 45min | `backend/app/routers/stream.py` |
| D4.10 | Endpoint `GET /api/v1/audits/{id}/export/pdf` | Codex | 30min | `backend/app/routers/exports.py` |
| D4.11 | Tests integración end-to-end del grafo | Codex | 30min | `backend/tests/test_orchestrator.py` |
| D4.12 | Smoke test con `karpathy/llm.c` end-to-end | Eduky | 15min | — |
| D4.13 | Commit + push | Eduky | 5min | — |

### Acceptance criteria

- [ ] `POST /api/v1/audits` con repo URL ejecuta los 5 agentes y persiste resultados completos
- [ ] PDF Annex IV descargable y se ve profesional (logo, headers, tablas)
- [ ] Disclosure snippets generados en EN/IT/ES/FR/DE para cada LIMITED_RISK system
- [ ] Compliance Score 0-100 calculado con metodología documentada
- [ ] Gaps identificados con severidad, descripción, remediación, días de esfuerzo
- [ ] SSE endpoint emite eventos `agent_start`, `agent_progress`, `agent_complete`, `audit_complete`
- [ ] Test integración pasa: audit completo en <5 minutos para repo mediano

### Handoff a D5
- Backend funcional al 95%. Solo falta Monitor agent + integraciones cosméticas.
- Pipeline produce todos los artefactos finales

---

## D5 — DOM 17 MAYO · FRONTEND COMPLETO + MONITOR AGENT

### Objetivo
Construir el frontend completo: landing → submission → live audit dashboard → score visualization → artifact downloads. Implementar agente Monitor (lite). Pulir UX.

### Tareas atómicas (10h)

| # | Tarea | Quién | Tiempo | Archivos |
|---|---|---|---|---|
| D5.1 | Layout global + nav | Codex | 30min | `frontend/app/layout.tsx` |
| D5.2 | Landing page con hook del Omnibus deal | Codex | 60min | `frontend/app/page.tsx` |
| D5.3 | Submit page con form + validación URL | Codex | 45min | `frontend/app/audit/new/page.tsx` |
| D5.4 | API client + types compartidos con backend | Codex | 30min | `frontend/lib/api.ts`, `frontend/lib/types.ts` |
| D5.5 | SSE consumer hook | Codex | 30min | `frontend/lib/sse.ts` |
| D5.6 | Live audit dashboard `[id]/page.tsx` | Codex | 90min | `frontend/app/audit/[id]/page.tsx` |
| D5.7 | Componente `AgentCard.tsx` con status en vivo | Codex | 45min | `frontend/components/AgentCard.tsx` |
| D5.8 | Componente `ComplianceScoreRing.tsx` (recharts) | Codex | 45min | `frontend/components/ComplianceScoreRing.tsx` |
| D5.9 | Componente `RiskBadge.tsx` y `AnnexIVPreview.tsx` | Codex | 30min | `frontend/components/*` |
| D5.10 | Implementar Monitor agent (versión lite) | Codex | 45min | `backend/app/agents/monitor.py` |
| D5.11 | Endpoint Monitor + UI alerts panel | Codex | 30min | — |
| D5.12 | Polish UX: loading states, error states, empty states | Codex | 45min | varios |
| D5.13 | OG image + favicon | Codex/Eduky | 20min | `frontend/public/*` |
| D5.14 | Smoke test completo desde browser | Eduky | 30min | — |
| D5.15 | Commit + push | Eduky | 5min | — |

### Acceptance criteria

- [ ] Landing carga rápido (<2s LCP)
- [ ] Submit URL → redirect a `/audit/[id]` dashboard
- [ ] Dashboard muestra los 6 agentes con status en vivo (idle → running → done)
- [ ] Compliance Score Ring visualmente impresionante
- [ ] Lista de AI Systems con risk badges
- [ ] Download PDF Annex IV funciona
- [ ] Snippets de Article 50 visibles en 5 idiomas con tab selector
- [ ] Gaps panel ordenado por severidad
- [ ] Mobile-responsive (no es prioridad pero no debe romperse)

### Handoff a D6
- Producto demo-ready en local
- Captura de screenshots para README y video

---

## D6 — LUN 18 MAYO · DEPLOY PRODUCCIÓN

### Objetivo
Deploy backend a Vultr VM + frontend a Vercel. Domain (opcional). HTTPS. Smoke test end-to-end en producción. Selección de caso demo definitivo.

### Tareas atómicas (4h)

| # | Tarea | Quién | Tiempo | Archivos |
|---|---|---|---|---|
| D6.1 | Dockerizar backend | Codex | 30min | `backend/Dockerfile`, `docker-compose.prod.yml` |
| D6.2 | Setup Coolify en Vultr VM | Eduky (script) | 30min | `infra/coolify/` |
| D6.3 | Configurar Nginx + Let's Encrypt | Codex + Eduky | 30min | `infra/nginx/conforma-ai.conf` |
| D6.4 | Deploy backend a Vultr | Eduky | 20min | — |
| D6.5 | Migrar Postgres a Vultr Managed DB | Eduky | 30min | — |
| D6.6 | Deploy frontend a Vercel desde GitHub | Eduky | 15min | `vercel.json` |
| D6.7 | Configurar env vars en ambos | Eduky | 15min | — |
| D6.8 | Smoke test full pipeline en producción | Eduky | 30min | — |
| D6.9 | Selección de repo demo definitivo + ejecutar audit final | Eduky + ChatGPT | 30min | — |
| D6.10 | Capturar screenshots de Vultr dashboard + AI Studio | Eduky | 15min | `docs/screenshots/` |
| D6.11 | Commit + push | Eduky | 5min | — |

### Acceptance criteria

- [ ] `https://api.conforma.ai` (o subdomain Vultr) responde 200
- [ ] Frontend en `https://conforma-ai.vercel.app` carga
- [ ] Full audit pipeline corre end-to-end en producción
- [ ] Compliance Score se calcula y persiste correctamente
- [ ] PDF descarga sin errores
- [ ] Screenshots de sponsor dashboards capturados

---

## D7 — MAR 19 MAYO · VIDEO + SLIDES + README FINAL

### Objetivo
Producir todos los assets de presentación: video demo de 2 min, slides de 10, README v1.0 con badges y diagrams.

### Tareas atómicas (4h)

| # | Tarea | Quién | Tiempo | Archivos |
|---|---|---|---|---|
| D7.1 | Escribir script final del video | ChatGPT + Eduky | 30min | `docs/DEMO_SCRIPT.md` |
| D7.2 | Grabar pantalla del flow completo | Eduky | 30min | — |
| D7.3 | Grabar voiceover | Eduky | 30min | — |
| D7.4 | Editar video (CapCut/DaVinci/iMovie) | Eduky | 60min | — |
| D7.5 | Crear slide deck (10 slides) | Codex + Eduky | 60min | `docs/slides.pdf` |
| D7.6 | Refinar README v1.0 con diagrama + screenshots + badges | Codex | 30min | `README.md` |
| D7.7 | Crear cover image 1920x1080 | Eduky (Canva) | 20min | `docs/cover.png` |
| D7.8 | Commit + push final | Eduky | 5min | — |

### Acceptance criteria

- [ ] Video ≤2:30 min, audio claro, demo en vivo visible, screenshots de sponsors
- [ ] Slides cubren: Problem → Solution → Demo → Architecture → Score → Stack → Roadmap → Ask
- [ ] README v1.0 incluye: badges, hero image, problem, how it works, tech stack, screenshots, hackathon tracks, license
- [ ] Cover image impactante para lablab.ai listing

---

## D8 — MIÉ 20 MAYO · SUBMISSION

### Objetivo
Subir todo a lablab.ai con tiempo de sobra. Buffer para errores de última hora.

### Tareas atómicas (3h)

| # | Tarea | Quién | Tiempo |
|---|---|---|---|
| D8.1 | Subir video a YouTube (unlisted) | Eduky | 15min |
| D8.2 | Submit en lablab.ai con todos los campos | Eduky | 30min |
| D8.3 | Post LinkedIn + X anunciando submission | Eduky | 30min |
| D8.4 | Buffer / fix lastminute issues | Eduky | 90min |
| D8.5 | Celebrar y descansar para arrancar VaquitaAI | Eduky | ∞ |

### Acceptance criteria

- [ ] Submission completa en lablab.ai antes de las 18:00 UTC del 20 mayo
- [ ] Video público (unlisted) en YouTube con link en submission
- [ ] Repo GitHub público con README v1.0
- [ ] Demo URL responde y funciona

---

## 🚨 KILL-SWITCH / SCOPE REDUCTION

Si en algún día la dedicación real supera 1.5x lo estimado, **recorta de este orden:**

1. **Primero recorta:** Monitor agent (puede ser mocked en demo)
2. **Después recorta:** Multi-language disclosures (deja solo EN + IT)
3. **Después recorta:** Frontend polish (loading states, animations)
4. **Después recorta:** Tests E2E (deja solo unit tests críticos)
5. **NUNCA recortes:** Classifier quality, PDF generation, Compliance Score, video demo

**Lema:** *Mejor 5 agentes perfectos que 6 mediocres.*

---

## 📊 PROGRESS TRACKING

Cada noche al cerrar, Eduky reporta a ChatGPT:

```
=== D[n] STATUS ===
- Acceptance criteria pasados: X/Y
- Horas reales invertidas: Z
- Bloqueado en: [descripción]
- Decisiones tomadas fuera del plan: [si aplica]
- Acumulado total: W horas
- Confianza en deadline: HIGH | MEDIUM | LOW
==================
```

Si confianza baja a LOW dos días seguidos → activar kill-switch.
