# 📦 CONFORMA-AI · HANDOFF PACKAGE

> Paquete completo de contexto para que ChatGPT 5.5 coordine a Codex en la construcción de Conforma-AI durante el AI Agent Olympics 2026 (Milan AI Week, 13-20 mayo 2026).
>
> **Generado por Claude (Anthropic) · 13 mayo 2026 · Cali → Milano**

---

## 🚀 CÓMO USAR ESTE PAQUETE

### Paso 1 — Eduky abre nueva sesión con ChatGPT 5.5
Sube TODO este paquete (10 archivos .md) al chat de ChatGPT como contexto inicial. Luego pega este mensaje:

```
Hola ChatGPT. Voy a construir Conforma-AI para el AI Agent Olympics 2026.

Adjunto el paquete completo de handoff generado por Claude (10 archivos .md).
Léelos en este orden:
1. 00_INDEX.md (navegación y modus operandi)
2. 01_BRIEF_AND_CONTEXT.md (qué construimos y por qué)
3. 03_PROJECT_PLAN.md (plan día por día)
4. 02_ARCHITECTURE_AND_STACK.md (referencia técnica)
5. 04_AGENT_SPECS.md (especificación de los 6 agentes)
6. 05_EU_AI_ACT_KB.md (knowledge base legal)
7. 06_FILES_MANIFEST.md (lista de archivos del repo)
8. 07_CODEX_PROMPT_LIBRARY.md (cómo le pides cosas a Codex)
9. 08_EDUKY_MANUAL_TASKS.md (qué hago yo manualmente)
10. 09_DEMO_AND_SUBMISSION.md (video, slides, README final, submission)

Tu rol: coordinador de proyecto.
Mi rol: ejecutor humano (lo manual).
Codex: ejecutor de código.

Cuando termines de leer, dime: "Listo, leí todo. ¿Empezamos con D1?"

Hoy es Miércoles 13 mayo 2026, noche. Tenemos 7 días.
```

### Paso 2 — Cuando ChatGPT confirme que leyó todo, responde:
```
Empezamos con D1.

Mi setup actual:
- Sistema operativo: Windows 11
- Terminal: WSL Ubuntu / Git Bash
- Editor: VS Code
- Repo target: D:/conforma-ai
- GitHub repo: github.com/jpablortiz96/conforma-ai (creado vacío)

Estoy en pre-flight. Aún no he creado cuentas. Guíame paso a paso siguiendo 08_EDUKY_MANUAL_TASKS.md §1.
```

### Paso 3 — Sigue el ritmo
- ChatGPT te dice qué hacer manualmente o le pide a Codex código según el momento del día
- Tú ejecutas comandos, pegas código, capturas screenshots, haces deploys
- Al final de cada día, reportas el status según el formato en `03_PROJECT_PLAN.md`

### Paso 4 — Si algo se atasca
Vuelves a Claude (nuevo chat con este paquete + el problema específico) o usas el escalation path documentado en `08_EDUKY_MANUAL_TASKS.md` final.

---

## 🗂️ MAPA DE ARCHIVOS

```
conforma-ai-handoff/
├── README.md                      ← este archivo, instrucciones de uso
├── 00_INDEX.md                    ← navegación, modus operandi, reglas duras
├── 01_BRIEF_AND_CONTEXT.md        ← brief estratégico, por qué ganamos
├── 02_ARCHITECTURE_AND_STACK.md   ← diseño técnico (referencia para Codex)
├── 03_PROJECT_PLAN.md             ← sprint 8 días con acceptance criteria
├── 04_AGENT_SPECS.md              ← spec detallada de los 6 agentes + prompts
├── 05_EU_AI_ACT_KB.md             ← knowledge base legal completo
├── 06_FILES_MANIFEST.md           ← ~100 archivos del repo, status tracking
├── 07_CODEX_PROMPT_LIBRARY.md     ← 10 plantillas reutilizables de prompts
├── 08_EDUKY_MANUAL_TASKS.md       ← tareas humanas no delegables por día
└── 09_DEMO_AND_SUBMISSION.md      ← video script, slides, README v1.0, submission
```

**Líneas totales:** ~4,400 líneas de markdown. Léelo todo. Vale la pena.

---

## ⚙️ EL MODELO MENTAL

```
                ┌────────────────────────────────┐
                │       CLAUDE (Anthropic)       │
                │  Arquitecto · Decisiones macro │
                │  No accesible durante el sprint │
                └────────────────┬───────────────┘
                                 │
                                 ▼
                ┌────────────────────────────────┐
                │   HANDOFF PACKAGE (10 .md)     │  ← este paquete
                │   Single source of truth       │
                └────────────────┬───────────────┘
                                 │
                                 ▼
                ┌────────────────────────────────┐
                │      ChatGPT 5.5 (OpenAI)      │
                │  Project manager · Coordinador │
                │  Trabaja contigo en tiempo real │
                └────────┬───────────────┬───────┘
                         │               │
                         ▼               ▼
            ┌────────────────────┐  ┌──────────────────┐
            │  Codex (OpenAI)    │  │   EDUKY (tú)     │
            │  Ejecutor código   │  │  Ejecutor manual │
            │  Genera archivos   │  │  Clicks, deploys │
            └────────────────────┘  └──────────────────┘
```

---

## 🎯 RECORDATORIO FINAL

**Por qué este paquete existe:**
Eduky está construyendo Conforma-AI mientras también trabaja en Banco de Occidente, mantiene su comunidad Skool, y tiene VaquitaAI (deadline 6 junio). Cada hora cuenta. Este paquete elimina las preguntas que ChatGPT le habría hecho a Claude, dejando que la energía vaya a EJECUCIÓN, no a coordinación.

**El éxito de este paquete se mide así:**
- Eduky NO necesita volver con Claude durante D1-D8 salvo en problemas arquitectónicos serios
- ChatGPT puede coordinar el sprint completo solo con estos 10 archivos
- Codex genera código alineado a la visión sin alucinaciones
- El 20 mayo a las 18:00 UTC Conforma-AI está submitted en lablab.ai

**Si todo sale bien:**
$10K en premios + reputación como solo founder LATAM ganando en Milano + base de v2.0 para SaaS post-hackathon.

**Vamos. Yo soy el cerebro. ChatGPT es las manos. Codex es los dedos. Tú eres la voluntad.**
