# 🙋 TAREAS MANUALES DE EDUKY

> Estas son las cosas que **SOLO TÚ** puedes hacer. Codex no tiene acceso a credenciales, dashboards externos, ni a tu computador físico. ChatGPT te recordará cuándo te toca cada una.
>
> **Regla de oro:** si una tarea aquí dice "Eduky", no se delega. Si dice "Codex" o "ChatGPT", no la haces tú.

---

## 📋 ÍNDICE POR DÍA

- [§1 — Pre-flight (antes de D1)](#1-pre-flight)
- [§2 — D1 (Mié 13 May)](#2-d1)
- [§3 — D2 (Jue 14 May)](#3-d2)
- [§4 — D3 (Vie 15 May)](#4-d3)
- [§5 — D4 (Sáb 16 May)](#5-d4)
- [§6 — D5 (Dom 17 May)](#6-d5)
- [§7 — D6 (Lun 18 May)](#7-d6)
- [§8 — D7 (Mar 19 May)](#8-d7)
- [§9 — D8 (Mié 20 May) — SUBMISSION](#9-d8)

---

## §1 — PRE-FLIGHT
**Tiempo total estimado: 30 min · Hacer ANTES de empezar D1**

### 1.1 Cuentas a tener listas
| Plataforma | Acción | Verificación |
|---|---|---|
| **Vultr** | Crea cuenta en https://www.vultr.com con tu email | Login funciona + ves "Account" en el dashboard |
| **Vultr créditos** | Aplica el crédito del hackathon (revisa el email/Discord de lablab para el código) | Dashboard → Billing muestra el saldo |
| **Google AI Studio** | Login en https://aistudio.google.com con tu Google | Ves la página de API keys |
| **Google Cloud** | Activa $300 trial en https://cloud.google.com/free (si no lo tienes) | Dashboard de billing visible |
| **Vercel** | Login en https://vercel.com con tu GitHub `jpablortiz96` | Ves "Your projects" |
| **lablab.ai** | Login + enroll al **AI Agent Olympics 2026** | Status "Enrolled" visible |
| **GitHub** | Crea repo **vacío** privado `conforma-ai` en tu usuario | URL `https://github.com/jpablortiz96/conforma-ai` carga (404 está bien si está privado) |

### 1.2 Credenciales a generar y guardar
**Guarda TODO en tu password manager. NUNCA en archivos de texto plano, NUNCA en el repo.**

| Credencial | Cómo obtenerla | Dónde la usarás |
|---|---|---|
| **Gemini API Key** | AI Studio → "Get API key" → Create API key in new project | `backend/.env` línea `GEMINI_API_KEY=` |
| **SSH key pair** | En tu terminal: `ssh-keygen -t ed25519 -C "eduky@conforma-ai"` (acepta default path, pon passphrase opcional) | Subir `id_ed25519.pub` a Vultr al provisionar VM |
| **Postgres DB password** | Generar string random: `openssl rand -base64 32` | Server VM al crear DB |
| **SECRET_KEY FastAPI** | `openssl rand -hex 32` | `backend/.env` línea `SECRET_KEY=` |

### 1.3 Herramientas locales en tu Windows
| Herramienta | Versión mínima | Verificación |
|---|---|---|
| Node.js | 20+ | `node -v` |
| Python | 3.12+ | `python --version` (o `python3 --version`) |
| Docker Desktop | latest | `docker --version` + corriendo |
| Git | 2.40+ | `git --version` |
| WSL Ubuntu (o Git Bash) | latest | Terminal bash funciona |
| Visual Studio Code (opcional para revisar) | latest | — |

### 1.4 Reportar a ChatGPT cuando termines pre-flight
```
✅ Pre-flight completado.
- Cuentas activas: Vultr, AI Studio, Vercel, lablab.ai, GitHub
- Gemini API key generada y guardada
- SSH key pair generada en ~/.ssh/id_ed25519
- Postgres password generada y guardada
- SECRET_KEY generada y guardada
- Listo para D1.
```

---

## §2 — D1
**Tiempo total estimado de tu parte: ~45 min de los 3h del día**

### 2.1 Provisionar Vultr VM (20 min)
1. Dashboard Vultr → **Deploy New Server**
2. Plan: **Cloud Compute** → **Regular Performance**
3. Location: **Frankfurt 🇩🇪**
4. Image: **Ubuntu 24.04 LTS x64**
5. Size: **$12/mo** (2 vCPU, 4 GB RAM, 80 GB SSD)
6. Additional Features: deja default (NO ipv6, NO auto-backups durante hackathon — ahorra créditos)
7. SSH Keys: click "Add New" → pega contenido de `~/.ssh/id_ed25519.pub` → nombre: "eduky-laptop"
8. Hostname: `conforma-ai-prod`
9. Label: `conforma-ai`
10. Click **Deploy Now**
11. Espera ~60s hasta que el status sea "Running"
12. **Copia la IP pública.** La necesitarás los próximos 7 días.

**Anota la IP en tu notes app local** — formato sugerido:
```
CONFORMA-AI VULTR VM
IP: XX.XX.XX.XX
User: root
SSH: ssh root@XX.XX.XX.XX
Created: 13 May 2026
Region: Frankfurt
```

### 2.2 Verificar SSH funciona (2 min)
En tu terminal:
```bash
ssh root@<IP_DEL_VM>
```
Debe entrar sin pedir password. Si pide password → algo falló con la SSH key. Vuelve al paso 7 y revisa.

### 2.3 Ejecutar setup inicial del server (10 min)
Una vez dentro del VM por SSH, pega el bloque completo de setup que está en `03_PROJECT_PLAN.md` D1 (o que ChatGPT te genere). **Cambia el password de Postgres por el real que generaste.**

Verifica que termina con:
```
✅ Server ready: XX.XX.XX.XX
```

### 2.4 Cuando Codex termine de generar archivos: revisar y ejecutar (15 min)
ChatGPT te dará los archivos uno por uno. Para cada archivo:
1. Verifica path correcto en tu repo local (`D:/conforma-ai/...`)
2. Pega contenido tal como Codex lo entregó (NO edites manualmente — si algo no está bien, ChatGPT lo corrige y te lo da otra vez)
3. Guarda

Cuando todos los archivos estén creados:
```bash
cd /mnt/d/conforma-ai

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# DB local
cd ..
docker compose up -d

# Levantar API
cd backend
uvicorn app.main:app --reload --port 8000
```

En otra terminal:
```bash
cd /mnt/d/conforma-ai/frontend
npm install
npm run dev
```

### 2.5 Smoke test integral (10 min)
Abre `http://localhost:3000` y prueba los 4 casos del checklist en `03_PROJECT_PLAN.md` D1.

### 2.6 Commit + push (5 min)
```bash
cd /mnt/d/conforma-ai
git add .
git commit -m "feat(D1): classifier agent end-to-end with frontend"
git push -u origin main
```

### 2.7 Reporte a ChatGPT al cerrar D1
```
=== D1 STATUS ===
- Acceptance criteria: 12/12 ✅
- Horas reales: 3.2h
- Bloqueado: ninguno
- Próxima sesión: D2 noche
==================
```

---

## §3 — D2
**Tiempo manual estimado: ~30 min de los 3h del día**

### 3.1 Ejecutar migraciones Alembic (5 min)
Cuando Codex genere los modelos + migración inicial:
```bash
cd /mnt/d/conforma-ai/backend
source .venv/bin/activate
alembic upgrade head
```
Verifica:
```bash
psql -h localhost -U conforma -d conforma_ai -c "\dt"
```
Debe mostrar 5 tablas: `audits`, `ai_systems`, `agent_runs`, `artifacts`, `gaps`.

### 3.2 Probar Scanner con 3 repos reales (15 min)
Cuando el endpoint `POST /api/v1/agents/scanner` esté listo:
```bash
# Repo pequeño
curl -X POST http://localhost:8000/api/v1/agents/scanner \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/karpathy/llm.c"}'

# Repo mediano
curl -X POST http://localhost:8000/api/v1/agents/scanner \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/rasahq/rasa"}'

# Repo grande
curl -X POST http://localhost:8000/api/v1/agents/scanner \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/microsoft/recommenders"}'
```
**Si alguno tarda >2 min → flag a ChatGPT para optimizar Scanner.**

### 3.3 Ejecutar tests (5 min)
```bash
cd backend
pytest tests/test_scanner.py -v
```
Deben pasar todos.

### 3.4 Commit + reporte (5 min)
```bash
git add .
git commit -m "feat(D2): scanner agent + DB schema + alembic migrations"
git push
```

---

## §4 — D3
**Tiempo manual estimado: ~20 min**

### 4.1 Probar Classifier mejorado (10 min)
Ejecuta los 10 casos de test que están en `04_AGENT_SPECS.md` §2.7. Si alguno falla, dile a ChatGPT exactamente cuál y qué devolvió.

### 4.2 Probar flow combinado Scanner → Classifier (5 min)
```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/rasahq/rasa"}'
```
Espera el `audit_id`. Luego:
```bash
curl http://localhost:8000/api/v1/audits/<audit_id>/systems
```
Debe mostrar sistemas IA con su clasificación.

### 4.3 Commit + reporte (5 min)
```bash
git commit -am "feat(D3): full AI Act KB + classifier with article citations"
git push
```

---

## §5 — D4 (DÍA MÁS PESADO — 10h)
**Tiempo manual estimado: ~60 min de los 10h. Mayoría es review y testing.**

### 5.1 Reviewing PDF Annex IV generado (15 min)
Cuando Codex termine PDF generation:
1. Ejecuta el flow completo en local con `karpathy/llm.c`
2. Descarga el PDF generado
3. Ábrelo y verifica:
   - Tiene cover page con nombre del sistema
   - Las 9 secciones del Annex IV están presentes
   - Las "gaps" se muestran claramente en appendix A
   - Footer cita "Regulation EU 2024/1689"
   - No hay placeholders sin reemplazar tipo `{{ nombre }}`
4. Si algo está mal → reporta a ChatGPT con screenshot

### 5.2 Testing Disclosure multi-language (10 min)
Para cada lenguaje (EN/IT/ES/FR/DE):
1. Lee el snippet generado
2. Verifica que suena natural (no Google Translate)
3. Italiano y francés: si no estás seguro, copia a DeepL en sentido inverso → debe sonar como el original

### 5.3 Smoke test integral del orquestador (15 min)
```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/karpathy/llm.c"}'

# Toma el audit_id, luego:
curl -N http://localhost:8000/api/v1/audits/<audit_id>/stream
```
Debes ver eventos SSE llegando en orden: scanner → classifier → documentation + disclosure (paralelos) → gap_auditor → completed.

### 5.4 Verificar compliance score tiene sentido (10 min)
Manualmente revisa que el score 0-100 sea coherente:
- Repo con sistemas HIGH_RISK sin documentación → score bajo (< 50)
- Repo simple con solo MINIMAL_RISK → score alto (> 85)

### 5.5 Commit + reporte (10 min)
```bash
git commit -am "feat(D4): documentation + disclosure + gap auditor + langgraph orchestrator + PDF generation"
git push
```

**ALERTA:** Si al cerrar D4 vas más de 12h en lugar de 10h → activa **kill-switch** mañana. Postpón Monitor agent o multi-language.

---

## §6 — D5
**Tiempo manual estimado: ~75 min de los 10h. Mucho testing visual.**

### 6.1 Crear OG image y favicon (30 min)
Usa Canva:
1. **OG image** `frontend/public/og-image.png` — 1200x630px:
   - Background azul EU (#003399)
   - Texto: "Conforma-AI" grande + tagline + tu nombre/handle
   - Logo de Vultr y Gemini abajo
2. **Favicon** `frontend/public/favicon.ico` — 32x32:
   - Solo iniciales "C" o ⚖️ emoji-style
3. **Brand mark** `frontend/public/conforma-logo.svg`:
   - SVG simple, idealmente generado en Canva o Figma

### 6.2 Testing del frontend completo (30 min)
Recorre cada flujo end-to-end:
1. Landing carga → CTA visible
2. Click "Start Audit" → form aparece
3. Pegas URL → click submit → redirect a `/audit/[id]`
4. Ves los 6 AgentCards activarse en vivo
5. Compliance Score Ring se llena con animación
6. Lista de AI Systems con badges
7. Tab para ver gaps
8. Tab para ver disclosures multi-language
9. Botón "Download PDF" funciona

### 6.3 Smoke test mobile-responsive (10 min)
Chrome DevTools → device mode → iPhone 14:
- No debe romperse el layout
- Texto legible
- Botones touchable
- NO es prioridad pulir, solo "no roto"

### 6.4 Commit + reporte (5 min)
```bash
git commit -am "feat(D5): full frontend + monitor agent + brand assets"
git push
```

---

## §7 — D6 (DEPLOY DAY)
**Tiempo manual estimado: ~2h de los 4h del día**

### 7.1 Migrar a Vultr Managed Database (30 min)
1. Dashboard Vultr → **Databases** → **Add Managed Database**
2. PostgreSQL 16
3. Frankfurt (misma región que VM)
4. $15/mo plan (cubierto por créditos)
5. Espera ~5 min hasta "Running"
6. Copia connection string
7. Actualiza `DATABASE_URL` en `.env` del VM
8. Corre `alembic upgrade head` apuntando al nuevo DB
9. Verifica conexión

### 7.2 Setup Coolify (20 min)
1. SSH al VM:
   ```bash
   curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
   ```
2. Espera ~3 min hasta que termine
3. Abre `http://<IP>:8000` → crea cuenta admin (NO root@ — usa tu email real)
4. Conecta tu GitHub: Settings → Sources → GitHub App
5. Configura el repo conforma-ai
6. Coolify auto-detecta `Dockerfile` y `docker-compose.prod.yml`

### 7.3 Configurar Nginx + Let's Encrypt (15 min)
Opción A — sin dominio (rápido):
- Usa nip.io: `https://<IP>.nip.io` 
- Coolify gestiona el cert auto

Opción B — con dominio (si tienes uno listo):
- Apunta `api.tudominio.com` al IP del VM (DNS A record)
- En Coolify configura el domain → SSL auto

### 7.4 Configurar variables de entorno en producción (10 min)
En Coolify → Application → Environment Variables:
```
APP_ENV=production
GEMINI_API_KEY=<tu key>
GEMINI_PRO_MODEL=gemini-3.1-pro-preview
GEMINI_FLASH_MODEL=gemini-3-flash-preview
DATABASE_URL=<managed db connection string>
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<tu secret>
CORS_ORIGINS=https://conforma-ai.vercel.app,https://*.vercel.app
```
Click **Save** → Coolify redeploya automáticamente.

### 7.5 Deploy frontend a Vercel (10 min)
1. https://vercel.com/new → Import Project → selecciona `conforma-ai` repo
2. Root directory: `frontend`
3. Framework: Next.js (auto-detected)
4. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://<tu_api_url>
   ```
5. Deploy
6. Espera ~2 min → te da URL `conforma-ai-xxx.vercel.app`
7. Optional: rename project para que URL sea `conforma-ai.vercel.app`

### 7.6 Smoke test end-to-end en producción (10 min)
Desde tu browser:
1. Abre `https://conforma-ai.vercel.app`
2. Pega URL de repo de demo: `https://github.com/karpathy/llm.c`
3. Espera resultado completo (~3 min)
4. Verifica que TODO funciona: dashboard, score, PDF download, disclosures

**Si algo falla en producción** → check logs en Coolify + Vercel + flag a ChatGPT.

### 7.7 Capturar screenshots para sponsor proof (15 min)
Captura ALTA RESOLUCIÓN (mínimo 1920x1080) los siguientes:

**Vultr (obligatorios para sponsor track):**
- `vultr_dashboard.png` — dashboard mostrando el VM running en Frankfurt
- `vultr_managed_db.png` — managed Postgres en panel
- `vultr_billing.png` — créditos siendo usados
- `coolify_deployed.png` — Coolify mostrando el deploy exitoso

**Google AI Studio / Gemini (obligatorios):**
- `ai_studio_dashboard.png` — usage stats mostrando llamadas a Gemini Pro + Flash
- `ai_studio_api_keys.png` — pantalla de API keys (TACHA la key real con un overlay)
- `gemini_usage_chart.png` — gráfico de consumo de tokens

**Producto:**
- `live_audit.png` — dashboard del audit corriendo en vivo
- `compliance_score.png` — ring con score 42/100 visible
- `annex_iv_pdf.png` — primera página del PDF generado
- `disclosures_multilang.png` — tabs de los 5 idiomas

Guarda todo en `docs/screenshots/`. Commit:
```bash
git add docs/screenshots/
git commit -m "docs(D6): sponsor proof screenshots"
git push
```

### 7.8 Seleccionar caso demo definitivo (15 min)
Corre el audit en producción contra los 3 candidatos:
- `karpathy/llm.c`
- `rasahq/rasa`
- `microsoft/recommenders`

Compara cuál produce el demo más impactante:
- Variedad de risk classes encontradas
- Score interesante (ni 0 ni 100)
- PDF se ve completo
- Tiempo razonable (<4 min)

Decide cuál es **EL** caso demo. Anota su `audit_id` — lo reusarás en el video para no esperar la ejecución en vivo.

---

## §8 — D7 (VIDEO + SLIDES + README)
**Tiempo manual estimado: ~3h de los 4h del día**

### 8.1 Preparar setup de grabación (15 min)
- Cierra todas las apps menos Chrome
- Modo "Do Not Disturb" 
- Resolución pantalla: 1920x1080 (importante para upload final)
- Micrófono testeado, sin eco
- Background limpio si vas a aparecer en cámara (opcional, no requerido)

### 8.2 Grabar pantalla (45 min)
Usa **OBS Studio** (gratis):
1. Configuración: 1080p 30fps, audio sistema + mic
2. Practica el flow 2-3 veces SIN grabar
3. Cuando grabes:
   - Empieza desde el browser cerrado
   - Abre conforma-ai.vercel.app
   - Pega URL del repo demo (NO escribas, pega — más rápido)
   - Click submit
   - Pausa mientras corre (lo cortarás en edición)
   - Cuando termine, recorre el dashboard
   - Descarga el PDF
   - Muestra los 5 idiomas
   - Click en GitHub link
4. Si te equivocas, no pares — vuelve a empezar la sección. Editas después.

### 8.3 Grabar voiceover (30 min)
Lee el script de `09_DEMO_AND_SUBMISSION.md` §1.

Tips:
- Habla más lento de lo que crees natural
- 5 takes mínimo por sección — quédate con el mejor
- Audacity (gratis) para grabar; export a WAV

### 8.4 Editar el video (60 min)
**Herramienta recomendada:** CapCut (gratis, simple, suficiente)

Estructura final:
- 0:00-0:10 — Hook con titular del Omnibus deal
- 0:10-0:30 — Problem (números en pantalla)
- 0:30-1:30 — Live demo (la grabación de pantalla, acelera 2-3x las esperas)
- 1:30-1:50 — Stack (screenshots de sponsors)
- 1:50-2:00 — Close + URL + GitHub

Música de fondo:
- Hook: tense (busca "tech news intro" en YouTube Audio Library)
- Demo: minimal upbeat (busca "ambient tech")
- Close: triumphant (busca "successful conclusion")

Export: MP4, 1080p, H.264, audio AAC 192kbps.

### 8.5 Crear cover image para lablab.ai (15 min)
1920x1080 PNG. Usa Canva template:
- Logo de Conforma-AI grande centrado
- Tagline: "The autonomous compliance officer for the EU AI Act"
- Hackathon badge: "AI Agent Olympics 2026 · Milan AI Week"
- 2 sponsor logos abajo: Vultr + Google Gemini

Guarda como `docs/cover.png`.

### 8.6 Review final del README v1.0 (15 min)
ChatGPT + Codex generan el README final con el plan en `09_DEMO_AND_SUBMISSION.md` §3. Tú haces última pasada:
- Todos los links funcionan
- Todos los screenshots cargan
- Badges arriba alineados
- Sección de hackathon tracks visible
- Tu nombre y eduky.co linkeados

### 8.7 Subir video a YouTube como **Unlisted** (10 min)
1. https://studio.youtube.com → Upload
2. Settings:
   - Title: `Conforma-AI · AI Agent Olympics 2026 · 2min Demo`
   - Description: copia el long description del producto
   - **Privacy: Unlisted** (NO Public, NO Private)
   - Category: Science & Technology
3. Copia la URL — la necesitas para lablab.ai

### 8.8 Commit final pre-submission
```bash
git add .
git commit -m "docs(D7): final README + cover + demo assets"
git tag v1.0.0-hackathon
git push --tags
```

---

## §9 — D8 — SUBMISSION DAY
**Tiempo total: ~3h. La submission misma toma 30 min; el resto es buffer.**

⚠️ **El deadline es 20 mayo a las 18:00 UTC. NO esperes a las 17:50. Submit a más tardar 14:00 UTC.**

### 9.1 Submission en lablab.ai (30 min)
Usa la checklist exacta de `09_DEMO_AND_SUBMISSION.md` §4. Tabla de campos a llenar.

### 9.2 Post LinkedIn anunciando (20 min)
Template en `09_DEMO_AND_SUBMISSION.md` §5. Postea con:
- 1 imagen (cover de Conforma-AI)
- Links: GitHub, demo, video
- Tag a @vultr, @googledeepmind, @lablab_ai

### 9.3 Post X / Twitter (10 min)
Thread de 4-5 tweets con el mismo content. Tag los mismos accounts.

### 9.4 Post Instagram Story (5 min)
Para tu audiencia Eduky LATAM. En español. Foto del laptop + caption corto.

### 9.5 Buffer ~90 min para fixes lastminute
Si algo está rota en la URL pública en este punto:
- Captura el error
- Manda screenshot a ChatGPT
- Codex hot-fix
- Redeploy
- Smoke test
- Edita la submission si es necesario

### 9.6 Cuando confirmes submission exitosa
1. **Cierra la laptop.**
2. **Come algo decente.**
3. **Descansa 12+ horas.**
4. **El 21 de mayo arrancas VaquitaAI con energía.**

---

## 🚨 ALERTAS / DECISIONES SOLO TÚ TOMAS

ChatGPT y Codex automatizan ejecución, pero TÚ decides cuando:

| Situación | Tu decisión |
|---|---|
| Pasaste 1.5x el tiempo estimado del día | Activar kill-switch (ver `03_PROJECT_PLAN.md`) |
| VaquitaAI siente que se está retrasando | Pausar features no-críticas de Conforma-AI |
| Codex sugiere cambio de arquitectura | NO — escalar a Claude (volver a chat con Claude) |
| Quedan menos de 6h al deadline y algo no funciona | Recortar feature, NO arriesgar submission |
| Surge oportunidad de partnership/intro durante el hackathon | Pausa, atiende, hackathon puede esperar 30 min |
| Estás físicamente cansado / mental fog | Para 1h. Mejor producto, no peor. |

---

## 📞 ESCALATION PATH

```
Problema técnico → ChatGPT (intentar resolver)
   ↓ (si no resuelve)
ChatGPT pide a Codex un fix con prompt de Debug (Type 9)
   ↓ (si no resuelve)
ChatGPT te avisa "esto requiere a Claude"
   ↓
TÚ abres nuevo chat con Claude, traes el handoff package + descripción del problema
   ↓
Claude da nueva guía → vuelves a ChatGPT con la guía
```

**NUNCA** improvises arquitectura para "salir del paso". El producto pierde credibilidad y los jueces se dan cuenta.
