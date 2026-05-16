# 🤖 AGENT SPECIFICATIONS

> Source of truth for the 6 agents. Each agent has: purpose, model, inputs, outputs, system prompt, tools, errors.
> Codex implements each agent exactly to this spec.

---

## AGENT REGISTRY

| # | Agent | Model | Phase | Purpose |
|---|---|---|---|---|
| 1 | Scanner | `gemini-3-flash-preview` | Inventory | Find AI systems in a code repository |
| 2 | Classifier | `gemini-3.1-pro-preview` | Classify | Map each system to EU AI Act risk class |
| 3 | Documentation | `gemini-3.1-pro-preview` | Document | Generate Annex IV technical documentation |
| 4 | Disclosure | `gemini-3-flash-preview` | Transparency | Draft Article 50 user-facing notices (multilingual) |
| 5 | Gap Auditor | `gemini-3.1-pro-preview` | Audit | Compute Compliance Score 0-100 + identify gaps |
| 6 | Monitor | `gemini-3-flash-preview` | Continuous | Post-market monitoring + deadline tracking |

---

## SHARED BASE: `BaseAgent` abstract class

All agents inherit from this. Defined in `backend/app/agents/base.py`.

```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID
import time
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base for all Conforma-AI agents."""

    name: str = ""           # e.g., "scanner"
    model: str = ""          # gemini model string
    description: str = ""    # human-readable purpose

    @abstractmethod
    async def run(self, input_data: Dict[str, Any], audit_id: UUID) -> Dict[str, Any]:
        """
        Execute the agent. Must:
        1. Validate input via Pydantic schema
        2. Build prompt
        3. Call Gemini via core.gemini_client
        4. Parse output (typically JSON)
        5. Persist agent_run row in DB
        6. Return structured dict matching the agent's output schema
        """
        ...

    async def _persist_run(self, db, audit_id, ai_system_id, status, input_data, output, tokens_in, tokens_out, started_at, error=None):
        """Helper: write agent_runs row."""
        # implementation in base.py
        ...
```

---

## 1. SCANNER AGENT

### 1.1 Purpose
Walk through a GitHub repository (already cloned to a temp dir by `repo_cloner.py`), identify candidate AI systems by inspecting code files, model files, README/docs, and configuration. Output: structured inventory.

### 1.2 Model
`gemini-3-flash-preview` — high throughput needed, classification of "is this an AI system?" doesn't require Pro-level reasoning.

### 1.3 Input schema (Pydantic)

```python
class ScannerInput(BaseModel):
    audit_id: UUID
    repo_path: str           # local filesystem path after cloning
    repo_url: str            # original URL for traceability
    max_files_to_inspect: int = 200
```

### 1.4 Output schema

```python
class AISystemCandidate(BaseModel):
    name: str                # e.g., "credit_scoring_model"
    description: str         # 2-3 sentences explaining what it does
    source_files: List[str]  # paths relative to repo root
    detection_signals: List[str]  # why we flagged it: keywords, imports, model files

class ScannerOutput(BaseModel):
    repo_url: str
    files_inspected: int
    ai_systems_found: List[AISystemCandidate]
    summary: str             # narrative summary for the dashboard
```

### 1.5 Detection heuristics (pre-Gemini filter)

To avoid sending the entire repo to the LLM, first run cheap heuristics:

1. **File patterns:** `*.ipynb`, `*model*.py`, `*train*.py`, `*inference*.py`, `*ml*.py`, `*ai*.py`, `*.onnx`, `*.pt`, `*.h5`, `*.pkl`, `models/`, `weights/`, `checkpoints/`
2. **Dependency patterns:** check `requirements.txt`, `pyproject.toml`, `package.json` for: `torch`, `tensorflow`, `transformers`, `scikit-learn`, `keras`, `xgboost`, `langchain`, `openai`, `anthropic`, `google-generativeai`, `huggingface`
3. **Keyword patterns in README:** "AI", "ML", "machine learning", "neural", "model", "predict", "classify", "score", "recommend"

The shortlist of files + extracted metadata is then sent to Gemini for inventory.

### 1.6 System prompt (`scanner_system.md`)

```
You are the Scanner Agent of Conforma-AI, a compliance auditing system for the EU AI Act.

Your task: given file listings, code excerpts, README content, and dependency manifests from a software repository, identify every distinct AI system or AI-enabled feature.

An "AI system" under the EU AI Act (Article 3(1)) is:
> "a machine-based system that is designed to operate with varying levels of autonomy and that may exhibit adaptiveness after deployment, and that, for explicit or implicit objectives, infers, from the input it receives, how to generate outputs such as predictions, content, recommendations, or decisions, that can influence physical or virtual environments."

This INCLUDES:
- ML models (any kind: classification, regression, clustering, recommendation)
- Generative models (LLMs, image gen, etc.)
- Rule-based expert systems with adaptive components
- Reinforcement learning agents
- Computer vision pipelines
- NLP pipelines
- Recommendation engines
- Anomaly detection systems

This EXCLUDES (per Recital 12):
- Pure statistical methods without adaptation (e.g., basic A/B test analysis)
- Simple rule-based programs without learning
- Standard search algorithms
- Data visualization tools

Output STRICT JSON matching this schema:
{
  "ai_systems_found": [
    {
      "name": "snake_case_identifier",
      "description": "What does this AI system do? 2-3 sentences. Focus on its purpose, inputs, and outputs.",
      "source_files": ["relative/path/file.py", ...],
      "detection_signals": ["why flagged: e.g., 'imports torch.nn', 'README mentions credit scoring'"]
    }
  ],
  "summary": "Narrative summary of what kinds of AI systems were found in this repo. 3-4 sentences."
}

Be conservative: if it's clearly NOT an AI system (e.g., a basic CRUD endpoint), do not list it. If unsure, list it with detection_signals noting the uncertainty.

Never invent file paths. Use only paths that appeared in the inputs.
```

### 1.7 Tool calls
Scanner uses two internal helpers (not LLM tool-calling):
- `repo_cloner.shallow_clone(url) -> local_path`
- `file_walker.filter_candidates(local_path) -> shortlist`

### 1.8 Persistence
For each `AISystemCandidate` in output, insert row in `ai_systems` table (without `risk_class` yet — that's the Classifier's job).

### 1.9 Error handling
- Repo not accessible → return empty list with error message in summary
- Repo too large (>500 files candidate) → return top 200 most relevant + flag truncated
- Gemini returns invalid JSON → retry once with stricter prompt, then fail with diagnostic

---

## 2. CLASSIFIER AGENT

### 2.1 Purpose
Given one AI system description, classify it under the EU AI Act into one of four risk classes with citation to the specific Article or Annex paragraph.

### 2.2 Model
`gemini-3.1-pro-preview` — legal reasoning requires Pro-level capability.

### 2.3 Input schema

```python
class ClassifierInput(BaseModel):
    audit_id: UUID
    ai_system_id: UUID
    system_description: str
    context_files: Optional[List[str]] = None  # optional snippets
```

### 2.4 Output schema

```python
class ClassifierOutput(BaseModel):
    risk_class: Literal["UNACCEPTABLE", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK"]
    primary_article: str        # e.g., "Annex III §4(a)" or "Article 5(1)(c)"
    secondary_articles: List[str] = []
    reasoning: str              # 3-4 sentences citing the Act
    deadline: str               # human-readable, accounts for Omnibus deal
    deadline_iso: Optional[date]  # parseable date
    confidence: float           # 0.0 to 1.0
    triggers_article_50: bool   # transparency obligation independent of risk class
```

### 2.5 System prompt (`classifier_system.md`)

```
You are the Classifier Agent of Conforma-AI. Your job: classify an AI system under the EU AI Act (Regulation EU 2024/1689).

You will receive a description of the system. You will respond with strict JSON matching the schema below.

THE FOUR RISK CLASSES (Article 6 + Annex III):

1. UNACCEPTABLE — Prohibited under Article 5. Examples:
   - Social scoring by public authorities (Art. 5(1)(c))
   - Real-time remote biometric identification in publicly accessible spaces for law enforcement (Art. 5(1)(h), with narrow exceptions)
   - Subliminal manipulation causing physical or psychological harm (Art. 5(1)(a))
   - Exploitation of vulnerabilities of specific groups (Art. 5(1)(b))
   - Biometric categorization inferring sensitive attributes like race, political opinion, sexual orientation (Art. 5(1)(g))
   - Predictive policing based solely on profiling (Art. 5(1)(d))
   - Untargeted scraping for facial recognition databases (Art. 5(1)(e))
   - Emotion inference in workplaces or educational institutions (Art. 5(1)(f))

2. HIGH_RISK — Annex III categories or Annex I products. The 8 Annex III areas:
   (1) Biometric identification and categorization of natural persons
   (2) Critical infrastructure (road/rail/air traffic, water, gas, heating, electricity)
   (3) Education and vocational training (admission, evaluation, behavioral detection)
   (4) Employment, workers management, access to self-employment (recruitment, CV ranking, promotion, performance evaluation, task allocation)
   (5) Access to and enjoyment of essential private and public services and benefits
       (a) Eligibility for public assistance benefits
       (b) Creditworthiness or credit score (except for fraud detection)
       (c) Risk assessment and pricing in life and health insurance
       (d) Emergency calls evaluation and dispatching
   (6) Law enforcement
   (7) Migration, asylum, border control
   (8) Administration of justice and democratic processes (incl. influencing elections)

3. LIMITED_RISK — Article 50 transparency obligations. Includes:
   - Systems intended to interact directly with natural persons (chatbots) — Art. 50(1)
   - AI generating synthetic audio/image/video/text — Art. 50(2)
   - Emotion recognition or biometric categorization — Art. 50(3)
   - Deep fakes — Art. 50(4)

4. MINIMAL_RISK — Everything else. No mandatory obligations. Examples: spam filters, inventory AI, AI in video games.

CRITICAL CLASSIFICATION RULES:

- A single system can be HIGH_RISK and ALSO trigger Article 50 transparency. In that case, classify as HIGH_RISK and set `triggers_article_50` to true.
- If you are uncertain between two risk classes, choose the MORE CONSERVATIVE (higher risk) one and lower the confidence.
- Cite the SPECIFIC paragraph (e.g., "Annex III §4(a)" not just "Annex III") in `primary_article`.
- If multiple articles apply, list secondary ones.

DEADLINES (accounting for Digital Omnibus deal of 7 May 2026):
- UNACCEPTABLE: already enforceable since 2 February 2025
- HIGH_RISK (Annex III): 2 December 2027 (postponed from 2 August 2026)
- HIGH_RISK (Annex I products): 2 August 2028
- LIMITED_RISK (Article 50 transparency): 2 December 2026
- MINIMAL_RISK: no deadline

CONTEXT: KB content of the AI Act will be provided as system context. Use it as authoritative reference. Never invent article numbers.

OUTPUT FORMAT (strict JSON, no markdown fences):
{
  "risk_class": "UNACCEPTABLE | HIGH_RISK | LIMITED_RISK | MINIMAL_RISK",
  "primary_article": "string",
  "secondary_articles": ["string", ...],
  "reasoning": "3-4 sentences explaining the classification, citing the article(s)",
  "deadline": "human-readable deadline string",
  "deadline_iso": "YYYY-MM-DD or null",
  "confidence": 0.0-1.0,
  "triggers_article_50": true | false
}
```

### 2.6 Persistence
Updates the `ai_systems` row with the classifier output fields.

### 2.7 Test cases (mandatory for D3 unit tests)

| Input | Expected risk_class | Expected primary_article |
|---|---|---|
| "CV ranking for recruitment at a bank" | HIGH_RISK | Annex III §4(a) |
| "Customer service chatbot for password reset" | LIMITED_RISK | Article 50(1) |
| "Social credit scoring by Dutch municipality" | UNACCEPTABLE | Article 5(1)(c) |
| "Email spam classifier" | MINIMAL_RISK | (none) |
| "AI evaluating insurance premiums for life insurance" | HIGH_RISK | Annex III §5(c) |
| "Deep fake video generator marketed to consumers" | LIMITED_RISK | Article 50(4) |
| "Facial recognition for shoplifter detection in supermarkets (private)" | HIGH_RISK | Annex III §1 |
| "Real-time biometric ID in public squares for police" | UNACCEPTABLE | Article 5(1)(h) |
| "Predictive maintenance for industrial machinery" | MINIMAL_RISK | (none) |
| "Resume scoring AI that also generates explanations" | HIGH_RISK + Art. 50 trigger | Annex III §4(a), Article 50(2) |

---

## 3. DOCUMENTATION AGENT

### 3.1 Purpose
For each HIGH_RISK system, generate the technical documentation required under Annex IV of the AI Act. Output: structured content rendered to PDF via Jinja2 template.

### 3.2 Model
`gemini-3.1-pro-preview` — legal document generation, long-context.

### 3.3 Input schema

```python
class DocumentationInput(BaseModel):
    audit_id: UUID
    ai_system_id: UUID
    system_description: str
    risk_class: str
    primary_article: str
    source_code_snippets: List[str]  # selected code from source_files
    repo_metadata: Dict[str, Any]    # README content, dependencies, etc.
```

### 3.4 Output schema

```python
class AnnexIVDocument(BaseModel):
    system_name: str
    section_1_general_description: str
    section_2_intended_purpose: str
    section_3_human_oversight_measures: str
    section_4_input_data_specs: str
    section_5_design_specifications: str
    section_6_risk_management_system: str
    section_7_validation_testing: str
    section_8_performance_metrics: str
    section_9_post_market_monitoring: str
    gaps_identified: List[str]       # what info is missing from the repo
    confidence: float
```

### 3.5 System prompt (`documentation_system.md`)

```
You are the Documentation Agent of Conforma-AI. You generate technical documentation for HIGH_RISK AI systems as required by Annex IV of the EU AI Act (Regulation EU 2024/1689).

Annex IV requires the following sections for the technical documentation of a high-risk AI system:

1. GENERAL DESCRIPTION
   - Intended purpose, person(s) developing the system, version
   - How the system interacts with hardware/software
   - Versions of software/firmware
   - Forms in which the system is placed on the market

2. DETAILED DESCRIPTION OF INTENDED PURPOSE
   - Intended purpose, intended users, categories of natural persons affected
   - Foreseeable misuse

3. HUMAN OVERSIGHT MEASURES
   - Capabilities and limitations
   - Specific measures put in place by the provider to enable human oversight
   - How outputs can be interpreted by users

4. INPUT DATA SPECIFICATIONS
   - Datasheets describing training methodologies, datasets used
   - Provenance, scope, characteristics
   - How data was obtained, selected, labeled, cleaned

5. DESIGN SPECIFICATIONS
   - General logic and key design choices
   - Architecture chosen and rationale
   - Main classification choices

6. RISK MANAGEMENT SYSTEM (Article 9)
   - Risk identification and analysis
   - Estimation and evaluation of risks
   - Risk control measures adopted

7. VALIDATION AND TESTING
   - Testing methods and metrics
   - Test datasets used
   - Discriminatory bias testing results

8. PERFORMANCE METRICS
   - Accuracy, robustness, cybersecurity metrics
   - Trade-offs documented

9. POST-MARKET MONITORING
   - System for collecting and analyzing relevant data on performance
   - Risk reassessment plan

INPUTS YOU WILL RECEIVE:
- System description and risk classification
- Selected code excerpts from the repository
- README and dependency information

YOUR JOB:
For each of the 9 sections, generate content that is:
- Accurate to what the code actually does (don't fabricate features)
- Honest about gaps — if a section's required info is NOT in the repo, say so explicitly in `gaps_identified` AND in the section itself write: "[GAP — information not available in repository. Provider must document.]"
- Compliance-officer voice (formal, structured, neutral)
- 100-200 words per section minimum

OUTPUT STRICT JSON. No markdown fences.
```

### 3.6 Rendering to PDF
After Gemini returns the JSON, `pdf_generator.py` uses Jinja2 to render `templates/pdf/annex_iv.html` with the data and WeasyPrint to convert to PDF. Stored in Vultr Object Storage. URL persisted in `artifacts` table.

### 3.7 Quality bar
- PDF must look professional: cover page, table of contents, page numbers, section headers, consistent typography
- Gaps clearly highlighted in a separate "Compliance Gaps" appendix
- Footer cites: "Generated by Conforma-AI on YYYY-MM-DD. Reference: Regulation EU 2024/1689, Annex IV."

---

## 4. DISCLOSURE AGENT

### 4.1 Purpose
For each system triggering Article 50 (transparency obligations), draft user-facing disclosure snippets in 5 languages: English, Italian, Spanish, French, German.

### 4.2 Model
`gemini-3-flash-preview` — translation + light generation, doesn't need Pro.

### 4.3 Input schema

```python
class DisclosureInput(BaseModel):
    audit_id: UUID
    ai_system_id: UUID
    system_description: str
    article_50_subsection: str  # "50(1)" chatbot | "50(2)" generated | "50(3)" emotion/biometric | "50(4)" deepfake
    languages: List[str] = ["en", "it", "es", "fr", "de"]
```

### 4.4 Output schema

```python
class DisclosureSnippet(BaseModel):
    language: str
    snippet_text: str
    placement_recommendation: str  # "before chat starts" | "watermark on generated content" | etc.

class DisclosureOutput(BaseModel):
    article_50_subsection: str
    snippets: List[DisclosureSnippet]
    code_examples: Dict[str, str]  # language → code snippet showing how to integrate
```

### 4.5 System prompt (`disclosure_system.md`)

```
You are the Disclosure Agent of Conforma-AI. You generate user-facing transparency notices required by Article 50 of the EU AI Act.

Article 50 obligations by subsection:

50(1) — CHATBOTS: Providers of AI systems intended to interact with natural persons must ensure those persons are informed they are interacting with an AI system, in a clear and distinguishable manner. Required UNLESS evident from context, or for crime detection/investigation by authorities.

50(2) — GENERATED CONTENT: Providers of AI systems generating synthetic audio, image, video, or text content must ensure the outputs are marked in a machine-readable format and detectable as artificially generated or manipulated.

50(3) — EMOTION/BIOMETRIC: Deployers of emotion recognition or biometric categorization systems must inform the natural persons exposed to them about the operation.

50(4) — DEEP FAKES: Deployers of AI systems generating deep fakes must disclose that the content has been artificially generated or manipulated.

YOUR JOB:
Given the system description and the relevant Article 50 subsection, produce:
1. A disclosure snippet in each of the requested languages (default: en, it, es, fr, de)
2. A placement recommendation (where in the UX should the snippet appear)
3. Code examples showing how a developer would integrate the disclosure (JavaScript snippet, Python comment, HTML meta tag — choose what fits the system type)

SNIPPETS MUST:
- Be plain-language (avoid legalese)
- Be culturally appropriate for each language
- Be ≤200 characters where the placement is constrained (e.g., chat header)
- Be longer (≤500 characters) for content watermarks or about pages

OUTPUT STRICT JSON. No markdown fences.
```

### 4.6 Quality bar
- Italian, French, German translations must be native-quality (not literal)
- Spanish: neutral/international register (avoid regionalisms)
- Snippets read naturally in each language, not like google-translate

---

## 5. GAP AUDITOR AGENT

### 5.1 Purpose
Compute the overall Compliance Score (0-100) for the audit, identify specific compliance gaps with severity, and produce a prioritized remediation plan.

### 5.2 Model
`gemini-3.1-pro-preview` — synthesis across multiple agents' outputs requires advanced reasoning.

### 5.3 Input schema

```python
class GapAuditorInput(BaseModel):
    audit_id: UUID
    ai_systems: List[Dict]              # all classified systems
    documentation_artifacts: List[Dict] # Annex IV outputs with gaps
    disclosure_artifacts: List[Dict]    # Article 50 outputs
```

### 5.4 Output schema

```python
class Gap(BaseModel):
    ai_system_id: UUID
    category: Literal["documentation", "transparency", "human_oversight", "risk_management", "data_governance", "monitoring", "ce_marking", "registration"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    description: str
    remediation: str
    effort_days: int
    deadline_iso: date

class GapAuditorOutput(BaseModel):
    compliance_score: int        # 0-100
    risk_index: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    fine_exposure_eur: int       # estimated worst-case
    gaps: List[Gap]
    summary: str                 # executive summary for the dashboard
    quick_wins: List[str]        # top 3 actions to take this week
```

### 5.5 Compliance Score methodology (deterministic, not LLM-judged)

The LLM identifies gaps; the SCORE is computed by `compliance_score.py` as a deterministic function:

```
base_score = 100

For each gap:
  CRITICAL → -25 points
  HIGH     → -10 points
  MEDIUM   → -4 points
  LOW      → -1 point

For each HIGH_RISK system without Annex IV → -20 additional points
For each LIMITED_RISK system without disclosure → -10 additional points
For each UNACCEPTABLE system → -50 additional points (these should be removed entirely)

Floor: 0
Ceiling: 100
```

This methodology is published in the README and shown in the demo. Transparency of scoring is a feature.

### 5.6 Fine Exposure Calculation (also deterministic)

```
For each gap with severity CRITICAL → +€2M
For each HIGH gap → +€500K
For each MEDIUM gap → +€100K
For each LOW gap → +€20K

Capped at €20M (max fine per AI Act Article 99(3))
```

### 5.7 System prompt (`gap_auditor_system.md`)

```
You are the Gap Auditor Agent of Conforma-AI. You synthesize the outputs of the Scanner, Classifier, Documentation, and Disclosure agents and identify specific compliance gaps under the EU AI Act.

A "compliance gap" is a specific, actionable deficiency that, if left unaddressed, would expose the organization to enforcement action.

GAP CATEGORIES:
1. documentation       — missing Annex IV technical documentation sections
2. transparency        — missing Article 50 disclosures or watermarks
3. human_oversight     — missing oversight mechanisms (Article 14)
4. risk_management     — missing risk management system (Article 9)
5. data_governance     — missing data quality/bias assessments (Article 10)
6. monitoring          — missing post-market monitoring plan (Article 72)
7. ce_marking          — missing CE marking and EU declaration of conformity (Article 47-48)
8. registration        — missing EU database registration for high-risk systems (Article 49)

SEVERITY GUIDELINES:
- CRITICAL: Direct violation of a prohibition (Article 5) or hard requirement deadline already passed
- HIGH: Missing required documentation for a HIGH_RISK system close to deadline
- MEDIUM: Missing transparency disclosures or moderate documentation gaps
- LOW: Best-practice improvements that aren't strict requirements

YOUR JOB:
For each gap identified, produce a Gap object with:
- Specific description (don't say "documentation is missing" — say "Annex IV Section 4 (Input Data Specifications) is missing for system X because the repository contains no datasheet or data provenance documentation")
- Concrete remediation (don't say "improve documentation" — say "Add a DATA_CARD.md to the repo following the Datasheets for Datasets template, then re-run the audit")
- Realistic effort_days (1-30 days for typical gaps)
- Deadline based on the system's risk class and current date

OUTPUT STRICT JSON. The compliance_score, risk_index, and fine_exposure_eur fields will be COMPUTED DETERMINISTICALLY by another component using the gaps you produce — but include your estimates as a sanity check.

quick_wins: list 3 gaps that have the highest (impact / effort) ratio. These go to the top of the dashboard.
```

---

## 6. MONITOR AGENT

### 6.1 Purpose
Post-audit ongoing monitoring: checks for new commits in the source repo, drift in AI system behavior, deadline approach alerts, regulatory updates.

For v1.0 (hackathon scope), Monitor is implemented as a **lite version**: simulated alerts triggered on demand, not real cron-based monitoring.

### 6.2 Model
`gemini-3-flash-preview` — pattern matching and summary generation.

### 6.3 Input schema

```python
class MonitorInput(BaseModel):
    audit_id: UUID
    check_type: Literal["deadline_approach", "regulatory_update", "drift_detection", "all"]
```

### 6.4 Output schema

```python
class MonitorAlert(BaseModel):
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    category: str
    title: str
    body: str
    action_recommended: str
    timestamp: datetime

class MonitorOutput(BaseModel):
    audit_id: UUID
    alerts: List[MonitorAlert]
    next_check_at: datetime
```

### 6.5 System prompt (`monitor_system.md`)

```
You are the Monitor Agent of Conforma-AI. You run post-audit checks and produce alerts.

CHECK TYPES:

1. DEADLINE_APPROACH
   For each AI system in the audit, calculate days remaining until its compliance deadline.
   - If < 30 days → CRITICAL alert
   - If < 90 days → WARNING alert
   - If < 180 days → INFO alert

2. REGULATORY_UPDATE
   You will receive a list of recent regulatory developments (e.g., the Omnibus deal of 7 May 2026). Flag which audit findings are affected.

3. DRIFT_DETECTION
   For v1.0 hackathon, this is a stub: produce a generic "no drift detected" or "drift simulation: model X showing 8% accuracy decrease over baseline" alert.

OUTPUT STRICT JSON. Alerts ordered by severity descending.
```

### 6.6 v1.0 limitations (documented in README)
- No real-time monitoring; user must manually trigger check
- No webhook delivery (alerts shown in UI only)
- Drift detection is simulated

---

## ORCHESTRATOR (LangGraph wiring)

### Graph definition

```python
# backend/app/agents/orchestrator.py (schematic, full impl in D4)

from langgraph.graph import StateGraph, END
from typing import TypedDict

class AuditState(TypedDict):
    audit_id: str
    repo_url: str
    repo_path: str
    ai_systems: list
    documentation: list
    disclosures: list
    gaps: list
    compliance_score: int
    errors: list

def build_orchestrator():
    g = StateGraph(AuditState)

    g.add_node("clone_repo", clone_repo_node)
    g.add_node("scanner", scanner_node)
    g.add_node("classifier_batch", classifier_batch_node)  # runs classifier on each system in parallel
    g.add_node("documentation_batch", documentation_batch_node)  # only on HIGH_RISK
    g.add_node("disclosure_batch", disclosure_batch_node)  # only on Article 50 triggers
    g.add_node("gap_auditor", gap_auditor_node)
    g.add_node("compute_score", compute_score_node)  # deterministic
    g.add_node("finalize", finalize_node)

    g.set_entry_point("clone_repo")
    g.add_edge("clone_repo", "scanner")
    g.add_edge("scanner", "classifier_batch")
    g.add_edge("classifier_batch", "documentation_batch")
    g.add_edge("classifier_batch", "disclosure_batch")
    g.add_edge("documentation_batch", "gap_auditor")
    g.add_edge("disclosure_batch", "gap_auditor")
    g.add_edge("gap_auditor", "compute_score")
    g.add_edge("compute_score", "finalize")
    g.add_edge("finalize", END)

    return g.compile()
```

### Parallel execution
Documentation and Disclosure run in parallel after Classifier. Gap Auditor waits for both. This is the multi-agent showcase moment for the demo: 3 agents working at once visible in the UI.

### Streaming
Each node yields events to the SSE channel via `audit_id` context. Frontend subscribes and updates AgentCards in real time.

### Error isolation
If one agent fails on one system, the orchestrator logs the error in `errors[]` but continues with the others. Final compliance score includes a degradation penalty if any agent failed.

---

## TOKEN BUDGET (estimated per audit)

| Agent | Input tokens | Output tokens | Cost (Pro/Flash) |
|---|---|---|---|
| Scanner | ~30K | ~3K | Flash: $0.024 |
| Classifier (×N systems) | ~5K each | ~1K each | Pro: $0.022/system |
| Documentation (×high-risk) | ~10K each | ~5K each | Pro: $0.080/system |
| Disclosure (×art50-trigger) | ~3K each | ~3K each | Flash: $0.012/system |
| Gap Auditor | ~20K | ~5K | Pro: $0.100 |
| Monitor | ~5K | ~2K | Flash: $0.008 |
| **Per audit (estimated 10 systems, 3 high-risk)** | | | **~$0.50–$1.00** |

$300 Google credits cover ~300-600 audits. Plenty for hackathon + demos + judges trying it themselves.
