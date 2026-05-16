# 📖 CONFORMA-AI — HANDOFF PACKAGE INDEX

> **Modelo operativo:** Claude (Anthropic) es el **arquitecto y cerebro estratégico**. ChatGPT 5.5 es el **coordinador de proyecto**. Codex es el **ejecutor de código**. Eduky es el **operador humano** que ejecuta solo lo estrictamente manual (cuentas, credenciales, deploy buttons, submission final).
>
> Este paquete contiene TODO el contexto que ChatGPT 5.5 necesita para construir Conforma-AI sin requerir más input de Claude.

---

## 🗂️ ÍNDICE DE ARCHIVOS

| # | Archivo | Propósito | Idioma | Audiencia primaria |
|---|---|---|---|---|
| 00 | `00_INDEX.md` | Este archivo. Navegación y modus operandi. | ES | ChatGPT + Eduky |
| 01 | `01_BRIEF_AND_CONTEXT.md` | Brief estratégico + contexto del hackathon | ES | ChatGPT (decisiones) |
| 02 | `02_ARCHITECTURE_AND_STACK.md` | Diseño técnico, stack, deployment | EN | Codex (referencia) |
| 03 | `03_PROJECT_PLAN.md` | Plan sprint 8 días con acceptance criteria | ES | ChatGPT (coordinación) |
| 04 | `04_AGENT_SPECS.md` | Especificación detallada de los 6 agentes | EN | Codex (implementación) |
| 05 | `05_EU_AI_ACT_KB.md` | Knowledge base legal del AI Act | EN | Agentes (RAG) |
| 06 | `06_FILES_MANIFEST.md` | Manifiesto de TODOS los archivos del repo | EN | Codex (estructura) |
| 07 | `07_CODEX_PROMPT_LIBRARY.md` | Prompts reutilizables para Codex | EN | ChatGPT (envío a Codex) |
| 08 | `08_EDUKY_MANUAL_TASKS.md` | Tareas humanas no delegables | ES | Eduky (ejecutor) |
| 09 | `09_DEMO_AND_SUBMISSION.md` | Demo, video, README final, submission | EN+ES | Eduky + Codex |

**Lectura recomendada en orden:** 01 → 03 → 02 → 04 → 05 → 06 → 07 → 08 → 09.

---

## 🤖 MODUS OPERANDI PARA CHATGPT 5.5

Cuando Eduky abra una sesión contigo, sigue este protocolo:

### 1. Al inicio de cada sesión
- Confirma qué día del sprint estamos (referencia `03_PROJECT_PLAN.md`)
- Lee el último estado conocido (Eduky te dirá: "estoy en D3, falta el RAG")
- Verifica el `06_FILES_MANIFEST.md` para saber qué archivos ya existen
- Define el objetivo de la sesión actual con Eduky

### 2. Durante la sesión
- **Una tarea atómica a la vez.** No envíes a Codex 5 archivos en un prompt; envía uno, verifica, sigue.
- **Antes de pedir código a Codex:**
  - Identifica el archivo objetivo en `06_FILES_MANIFEST.md`
  - Usa la plantilla correspondiente de `07_CODEX_PROMPT_LIBRARY.md`
  - Incluye contexto necesario de `02_ARCHITECTURE_AND_STACK.md` y `04_AGENT_SPECS.md`
- **Después de que Codex entregue:**
  - Verifica contra acceptance criteria en `03_PROJECT_PLAN.md`
  - Si falla → ajuste o re-prompt
  - Si pasa → marca como ✅ en el manifest y avanza
- **Cuando Eduky deba hacer algo manualmente:** referencia `08_EDUKY_MANUAL_TASKS.md` por número de tarea, no improvises.

### 3. Reglas duras (no negociables)

| Regla | Por qué |
|---|---|
| ❌ NUNCA cambies el stack técnico sin consultar | Decisiones fueron tomadas por el arquitecto con razonamiento documentado |
| ❌ NUNCA propongas reemplazar Gemini por otro LLM | Gemini es requisito del sponsor track |
| ❌ NUNCA reduzcas a menos de 6 agentes | Es diferenciador clave vs single-agent baselines |
| ❌ NUNCA inventes contenido del AI Act | Usa solo `05_EU_AI_ACT_KB.md` o cita fuente oficial |
| ❌ NUNCA dejes datos fake obvios en el demo | Anti-patrón #1 que pierde hackathons |
| ✅ SIEMPRE pide a Codex que escriba tests para código no-trivial | Acceptance criteria lo requiere |
| ✅ SIEMPRE incluye screenshots de Vultr + AI Studio en la doc del sponsor | Multiplicador de prize |
| ✅ SIEMPRE escribe commits semánticos: `feat(Dn): descripción` | Trazabilidad para jueces |

### 4. Cuando algo se atasque

Antes de pedirle a Eduky que vuelva con Claude, intenta:
1. Re-leer la sección relevante de la doc
2. Pedir a Codex que escriba un script de diagnóstico
3. Buscar en docs oficiales (Gemini, Vultr, FastAPI, LangGraph, Next.js)

**Solo si después de 2-3 intentos sigue atascado:** Eduky vuelve a Claude con:
- Qué intentaste
- Qué falla exactamente (error message completo)
- Logs relevantes
- Estado del sistema

---

## 👷 MODUS OPERANDI PARA EDUKY

### Tu rol en este sistema
Eres el **operador humano** con acceso a credenciales, hardware físico, y autoridad de aprobación. NO escribes código línea por línea — eso es trabajo de Codex.

### Lo que TÚ haces (ver `08_EDUKY_MANUAL_TASKS.md`)
- Crear cuentas en plataformas (Vultr, Google AI Studio, Vercel, lablab.ai)
- Redimir créditos de sponsors
- Generar y guardar API keys (en password manager, NO en repo)
- Provisionar VMs en Vultr (clicks en dashboard)
- Ejecutar comandos terminal cuando ChatGPT te los pase
- Revisar y aprobar PRs/commits que Codex genere
- Grabar video demo (May 19)
- Submission final en lablab.ai (May 20)

### Lo que NUNCA haces
- Escribir código manualmente (Codex lo hace)
- Decidir arquitectura técnica (Claude ya lo decidió, documentado aquí)
- Improvisar fuera del plan (rompe el cronograma)
- Cambiar prompts de agentes sin verificación (toca la fundación del producto)

### Reportar progreso a ChatGPT
Al cerrar cada sesión, dile a ChatGPT:
```
Estado D[n]:
- Completado: [tareas]
- Pendiente: [tareas]
- Bloqueado en: [problema]
- Horas invertidas: [n]
- Próxima sesión: [fecha/hora]
```

---

## 🚦 ESTADO ACTUAL (al inicio del handoff)

- **Día actual:** D1 (Miércoles 13 mayo 2026)
- **Hora estimada de inicio:** Noche del D1
- **Completado por Claude:** Análisis estratégico, decisiones de stack, D1 execution package
- **Próximo paso:** Eduky ejecuta D1 con ayuda de ChatGPT, siguiendo `03_PROJECT_PLAN.md` sección D1
- **Deadline final:** Miércoles 20 mayo 2026 (submission day)

---

## ⚠️ RECORDATORIO CRÍTICO PARA CHATGPT

Conforma-AI compite por **$10K** en dos tracks simultáneos: Vultr ($5K) + Google Gemini ($5K). Cada decisión técnica debe servir a AMBOS sponsors. Si una optimización ayuda a uno pero perjudica al otro, **consulta con Eduky antes de aplicarla.**

El segundo recordatorio: Eduky tiene un proyecto paralelo (**VaquitaAI**, deadline 6 junio). Si Conforma-AI consume más de 45h en estos 8 días, prioriza descartar features no esenciales para preservar VaquitaAI.

---

_Construido por Claude (Anthropic) para Eduky · 13 mayo 2026 · Cali → Milano_
