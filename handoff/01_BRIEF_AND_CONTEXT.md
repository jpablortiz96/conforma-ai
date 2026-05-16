# 🎯 BRIEF ESTRATÉGICO Y CONTEXTO

## 1. MISIÓN DEL PROYECTO

Construir **Conforma-AI**, un sistema autónomo multi-agente que audita codebases empresariales contra la EU AI Act (Regulation EU 2024/1689) y produce un paquete de cumplimiento listo para auditoría externa, en horas en lugar de meses.

**Una frase pitch:**
> *"Conforma-AI es el oficial de cumplimiento autónomo para la EU AI Act: seis agentes inventan, clasifican, documentan y monitorean cada sistema de IA en tu empresa — antes de que el regulador llegue."*

---

## 2. POR QUÉ GANAMOS (Razonamiento documentado)

### 2.1 Timing perfecto
- El **Omnibus deal del 7 mayo 2026** (6 días antes del kickoff del hackathon) postpuso los deadlines del Anexo III de agosto 2026 a **diciembre 2027**, pero mantuvo las reglas del **Artículo 50 (transparencia)** para **diciembre 2026**.
- Toda empresa europea está en modo "qué hacemos ahora" → ventana de mercado abierta.
- Los jueces del Milan AI Week (managers, entrepreneurs, engineers europeos) tienen este tema en su mesa esta misma semana.

### 2.2 Especificidad geográfica = multiplicador de impacto
- Quipu ganó AI Dev Days Grand Prize porque era hyper-específico (Perú, municipios, alertas tempranas).
- Conforma-AI es hyper-específico para EU enterprises + GDPR-context + AI Act regulation.
- En Milan AI Week ese sesgo geográfico es nuestra arma.

### 2.3 Pain real con números reales
- Multas hasta **€20M o 4% facturación global**.
- Costo manual de compliance estimado en **€80K–€300K por empresa**.
- ~27,000 empresas EU con >50 empleados en scope.
- Consultoras especializadas booked hasta Q4 2027.

### 2.4 Multi-agent justificado naturalmente
- 6 agentes especializados, no 1 "que hace todo".
- Cada agente corresponde a una fase distinta del compliance lifecycle (Inventory → Classify → Document → Disclose → Audit → Monitor).
- Anti-patrón "un solo agente haciendo todo" → evitado.

### 2.5 Output cuantificable
- **Compliance Score 0–100** por sistema IA.
- **Portfolio Risk Index** agregado.
- **Time-to-Compliant** estimado en días.
- **Estimated Fine Exposure** en €.

Esto es exactamente lo que ganó a PRism (Confidence Score 0-100) y NimbusIQ (cloud architecture scoring).

### 2.6 Sponsor stack profundo
- **Vultr:** backend completo + Postgres + Redis + Coolify + Object Storage (PDFs).
- **Google Gemini:** Gemini 3.1 Pro como orquestador + Gemini 3 Flash en agentes + multimodal real (PDFs, screenshots, código).
- Cada feature documentada con screenshot del dashboard del sponsor.

### 2.7 WTF→WOW dentro de enterprise
Mientras 80% de equipos construirán customer support agents o RAG chatbots, nosotros traemos **"AI que audita AI bajo regulación europea"**. Es inesperado dentro de la categoría enterprise, sin perder profundidad.

---

## 3. CONTEXTO DEL HACKATHON

### 3.1 Identidad del evento
- **Nombre:** AI Agent Olympics Hackathon
- **Marco:** Milan AI Week 2026 (Europa, AI Week más grande del continente)
- **Audiencia:** 25,000+ asistentes, 700+ speakers, 250+ AI exhibitors
- **Jueces:** Managers, entrepreneurs, engineers europeos
- **Organizador:** lablab.ai
- **Premios totales:** $32,000+

### 3.2 Fechas críticas
| Fecha | Evento |
|---|---|
| Mié 13 mayo | Kickoff online |
| 13-19 mayo | Build phase online |
| Mar 19 mayo | On-site build day (Milan) — no asistimos |
| Mié 20 mayo | Demo Showcase & Awards Ceremony |

### 3.3 Tracks oficiales (escogemos solo los relevantes para nuestro stack)
1. 🧠 Intelligent Reasoning
2. 🔄 Agentic Workflows ⬅️ **encajamos aquí naturalmente**
3. 🌍 Enterprise Utility ⬅️ **encajamos aquí naturalmente**
4. 🧩 Multimodal Intelligence ⬅️ **encajamos aquí (Gemini multimodal)**
5. 🤝 Collaborative Systems ⬅️ **encajamos aquí (6 agentes coordinados)**

### 3.4 Tracks de sponsors que atacamos

#### 🎯 Vultr — Best Use of Vultr ($5K + $1K credits)
**Requisitos confirmados:**
- ✅ GitHub repository con setup y documentación
- ✅ Vultr VM backend deployment
- ✅ Public demo URL
- ✅ Recorded demo video
- ✅ Clear explanation of architecture and use case

**Bonus prize signals:**
- Usar Vultr como "central system of record"
- Vultr Serverless Inference disponible (no usaremos — Gemini es mejor)
- Documentar uso con screenshots

#### 🎯 Google Gemini — Best Use of Gemini ($5K)
**Requisitos confirmados:**
- ✅ Usar Gemini vía AI Studio o Gemini API
- ✅ Implementar agent-driven o automated workflows
- ✅ Demostrar valor práctico con working prototype
- ✅ Recomendado: Gemini Flash + Gemini Pro mix

**Bonus prize signals:**
- Mostrar uso de AI Studio en el demo
- Multimodal (texto + imágenes + PDFs + código)
- $300 Google Cloud credits disponibles

#### ❌ Tracks descartados con razonamiento
- **Kraken (Trading PnL):** Requiere capital real, riesgo financiero, 30 días de tracking. No encaja con perfil de hackathon corto.
- **Kraken (Social Engagement):** Distrae del core. Si ganamos los principales, momentum viene gratis.
- **Featherless:** Solo créditos como premio, no cash. Gemini ya cumple el rol.
- **Speechmatics:** No encaja orgánicamente en flow de compliance. Forzarlo restaría credibilidad.

### 3.5 Criterios de juzgamiento (4 pilares)

| Criterio | Peso (estimado) | Cómo ganamos |
|---|---|---|
| **Application of Technology** | ~30% | 6 agentes Gemini, multimodal, LangGraph, Vultr deep integration |
| **Business Value** | ~30% | Mercado de 27K empresas, multas €20M, deadlines vivos |
| **Originality** | ~20% | "AI que audita AI" + Omnibus deal hook + EU-specific |
| **Presentation** | ~20% | Video pulido, README pro, demo con caso real, slides con números |

### 3.6 Lo que debemos submitir (deliverables obligatorios)

**Información básica:**
- Project Title: **Conforma-AI**
- Short Description (~50 palabras)
- Long Description (~500 palabras)
- Tech & Category Tags

**Assets:**
- Cover Image (1920x1080)
- Video Presentation (≤3 min recomendado, 2 min target)
- Slide Presentation (10 slides)

**Código & Hosting:**
- Public GitHub Repository
- Demo Application URL (Vercel frontend + Vultr backend)
- README profesional

---

## 4. ANTI-PATRONES (Lo que NO hacemos)

| Anti-patrón | Por qué pierde | Cómo lo evitamos |
|---|---|---|
| Chatbot wrapper de LLM | 60% lo hace, cero diferenciación | Multi-agent con responsabilidades distintas |
| Dashboard sin acciones | Visualizar sin resolver = incompleto | Outputs accionables: PDFs, snippets de código, alertas |
| "AI que hace todo" | Sin foco = sin profundidad | Specificity: solo EU AI Act |
| Demo con datos fake obvios | Resta credibilidad | Demo sobre repo open-source real |
| Un solo agente haciendo todo | No demuestra orquestación | LangGraph con 6 agentes coordinados |
| README vacío | Jueces evalúan en 5 min sin README | README desde commit #1, profesional |
| No usar herramientas del sponsor | Desperdicio del multiplicador | Screenshots de Vultr + AI Studio en docs |
| Inventar contenido del AI Act | Pérdida de credibilidad legal | KB con citas verificables a Reg EU 2024/1689 |

---

## 5. PRINCIPIOS DE EJECUCIÓN

### 5.1 "Parece un PRODUCTO, no un hack"
Test mental: *Si un VP de Compliance europeo viera este demo, ¿pediría una reunión para comprarlo?*

Si la respuesta es no → agregar profundidad hasta que sea sí.

### 5.2 Velocidad sobre perfección, pero NO sobre credibilidad
- Acepta UI menos pulida si el agente razona correctamente.
- NO aceptes razonamiento incorrecto del agente aunque la UI sea bonita.
- La fundación es la calidad del razonamiento legal.

### 5.3 Multi-agent debe parecer NATURAL, no forzado
Cada agente tiene un job-to-be-done distinto. Si dos agentes hacen tareas muy similares, fusiónalos. Si un agente hace dos cosas no relacionadas, divídelo.

### 5.4 Demo con caso real
Para el demo final usamos un repo open-source REAL, conocido, con sistemas IA reales en él. Candidatos:
- **rasahq/rasa** (chatbot framework → LIMITED_RISK)
- **mindsdb/mindsdb** (ML platform multipropósito → varía)
- **karpathy/llm.c** (educational LLM → MINIMAL_RISK)
- **microsoft/recommenders** (recommender systems → puede ser HIGH_RISK si se usa para credit/hiring)

Selección final en D6 con base en cuál produce el demo más impactante.

---

## 6. ÉXITO = QUÉ SE VE EN EL DEMO

El demo de 2 minutos debe mostrar:

1. **Hook (0:00-0:10):** Pantalla con titular real del Omnibus deal 7 mayo 2026 + voiceover sobre el problema.
2. **Problem (0:10-0:30):** Números reales: 27K empresas, €20M multas, dos deadlines vivos.
3. **Live demo (0:30-1:30):**
   - Pegar URL del repo de prueba
   - Ver los 6 agentes activarse en tiempo real
   - Compliance Score aparece (ej: 42/100)
   - PDF Anexo IV descargable
   - Snippets de transparencia en 4 idiomas
   - Plan de remediación priorizado
4. **Stack (1:30-1:50):** Screenshots de Vultr dashboard + AI Studio + arquitectura.
5. **Close (1:50-2:00):** URL pública + GitHub + CTA.

---

## 7. NORTE ESTRATÉGICO (Recordatorio)

Cuando haya duda en cualquier decisión técnica, pregunta:

> *"¿Esto nos acerca o nos aleja de ganar Vultr Best + Gemini Best?"*

Si nos acerca → adelante.
Si nos aleja → descartar.
Si es neutral → priorizar simplicidad.
