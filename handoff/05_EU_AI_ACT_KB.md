# 📜 EU AI ACT KNOWLEDGE BASE

> Reference content for the Conforma-AI agents. Sourced from Regulation (EU) 2024/1689 (the EU AI Act), as published in the Official Journal on 12 July 2024, and updated to reflect the Digital Omnibus deal of 7 May 2026.
>
> **Authoritative source for verbatim text:** https://eur-lex.europa.eu/eli/reg/2024/1689/oj
>
> **Implementation timeline:** https://artificialintelligenceact.eu/implementation-timeline/
>
> This file is structured for ingestion as Python constants in `backend/app/knowledge/eu_ai_act_kb.py`. Codex should convert each section below into Python data structures (dicts, lists, or dataclasses) and provide accessor functions for the agents.

---

## 1. RECENT REGULATORY CONTEXT (CRITICAL — USE IN AGENT REASONING)

### 1.1 The Digital Omnibus deal of 7 May 2026
On 7 May 2026, the European Parliament, Council, and Commission reached agreement on the Digital Omnibus package, which amends the AI Act with the following effects on compliance deadlines:

| Provision | Original deadline | Amended deadline |
|---|---|---|
| Annex III High-Risk systems | 2 August 2026 | **2 December 2027** |
| Annex I product-embedded High-Risk | 2 August 2027 | **2 August 2028** |
| Article 50 transparency obligations | 2 August 2026 | **2 December 2026** |
| Nudifier ban (Article 5 expansion) | new | **2 December 2026** |
| AI regulatory sandboxes (Member States) | 2 August 2026 | **2 August 2027** |
| Machinery products under AI Act | covered | **EXEMPTED** from direct AI Act applicability |

**Implication for agent reasoning:** When the Classifier mentions a deadline for HIGH_RISK Annex III systems, it must say "2 December 2027 (postponed from 2 August 2026 by the Digital Omnibus deal of 7 May 2026)". When mentioning Article 50, deadline is **2 December 2026** (a 7-month runway from today).

### 1.2 What did NOT change
- The substantive obligations of the Act (risk classes, documentation requirements, oversight requirements, etc.)
- Penalties (still up to €35M or 7% global turnover for prohibited practices, €15M or 3% for non-compliance with most obligations)
- The risk-based approach
- Provider, deployer, importer, distributor responsibilities

---

## 2. THE FOUR RISK CLASSES

### 2.1 UNACCEPTABLE RISK (Article 5 — Prohibited Practices)

Already enforceable since **2 February 2025**.

**Prohibited practices:**

| Subsection | Practice |
|---|---|
| 5(1)(a) | Subliminal techniques causing physical/psychological harm |
| 5(1)(b) | Exploitation of vulnerabilities (age, disability, socioeconomic) |
| 5(1)(c) | Social scoring by public authorities (general purpose) |
| 5(1)(d) | Predictive policing based solely on profiling |
| 5(1)(e) | Untargeted scraping for facial recognition databases |
| 5(1)(f) | Emotion inference in workplaces or educational institutions (except medical/safety) |
| 5(1)(g) | Biometric categorization inferring sensitive attributes (race, political views, sexual orientation, religion) |
| 5(1)(h) | Real-time remote biometric identification in publicly accessible spaces for law enforcement (narrow exceptions only) |
| 5(1)(i) | *(Added by Omnibus deal)* Nudifier applications — AI generating non-consensual sexually explicit imagery |

**Penalty:** up to €35M or 7% of global annual turnover.

### 2.2 HIGH RISK (Article 6 + Annex III)

Two ways to be classified HIGH_RISK:

**Path A — Annex I products (regulated products with AI safety components)**
Examples: medical devices, machinery (EXEMPTED per Omnibus), toys, lifts, vehicles, aviation.
Deadline: **2 August 2028**.

**Path B — Annex III categories (stand-alone high-risk uses)**
Deadline: **2 December 2027**.

#### Annex III categories (full list with examples):

**(1) Biometric identification and categorization of natural persons:**
- Remote biometric identification systems (except those falling under Article 5 prohibition)
- Biometric categorization for sensitive attributes
- Emotion recognition (where not prohibited under Article 5)

**(2) Critical infrastructure:**
- AI systems for safety management of road traffic
- AI in supply of water, gas, heating, electricity
- Air traffic control safety
- Rail safety

**(3) Education and vocational training:**
- (a) Determining access or admission to educational institutions
- (b) Evaluating learning outcomes (admissions, exams)
- (c) Assessing appropriate level of education
- (d) Monitoring and detecting prohibited behavior during tests

**(4) Employment, workers management, access to self-employment:**
- (a) Recruitment (CV ranking, scoring of job applications, candidate filtering)
- (b) Decisions on promotion, termination, task allocation, performance evaluation
- Workplace monitoring (where it influences employment decisions)

**(5) Access to and enjoyment of essential private and public services:**
- (a) Determining eligibility for public assistance benefits
- (b) Creditworthiness scoring or credit scoring (except for fraud detection)
- (c) Risk assessment and pricing in life and health insurance
- (d) Emergency calls evaluation and dispatching (triage)

**(6) Law enforcement:**
- (a) Risk assessment of natural persons (recidivism, victim identification)
- (b) Polygraphs and similar tools
- (c) Reliability of evidence
- (d) Profiling for criminal investigations

**(7) Migration, asylum, border control:**
- (a) Polygraphs and similar tools at borders
- (b) Risk assessment of natural persons crossing borders
- (c) Examination of asylum/visa/residence permit applications
- (d) Detection of irregular migration

**(8) Administration of justice and democratic processes:**
- (a) AI assisting judicial authorities in researching/interpreting facts and law
- (b) AI influencing election outcomes or voter behavior (added during negotiations)

#### Obligations for HIGH_RISK systems (Chapter III):

| Article | Obligation |
|---|---|
| 9 | Risk management system |
| 10 | Data and data governance |
| 11 | Technical documentation (Annex IV — see Section 4 below) |
| 12 | Record-keeping (automatic logging) |
| 13 | Transparency and provision of information to deployers |
| 14 | Human oversight |
| 15 | Accuracy, robustness, cybersecurity |
| 16 | Obligations of providers (CE marking, registration, quality management, etc.) |
| 26 | Obligations of deployers |
| 47-48 | EU declaration of conformity, CE marking |
| 49 | Registration in EU database |
| 72 | Post-market monitoring |
| 73 | Reporting of serious incidents |

### 2.3 LIMITED RISK (Article 50 — Transparency Obligations)

Deadline: **2 December 2026** (7 months from today as of 13 May 2026).

#### Article 50 subsections:

**50(1) — Chatbots / direct interaction systems:**
> Providers shall ensure that AI systems intended to interact directly with natural persons are designed and developed in such a way that the natural persons concerned are informed that they are interacting with an AI system, unless this is obvious from the point of view of a natural person who is reasonably well-informed, observant and circumspect.

Exceptions: detection/prevention/investigation of criminal offences by authorities.

**50(2) — AI-generated content (synthetic):**
> Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or text content, shall ensure that the outputs of the AI system are marked in a machine-readable format and detectable as artificially generated or manipulated.

Required: technical watermarks, metadata, or equivalent that's robust to common modifications.

**50(3) — Emotion recognition / biometric categorization:**
> Deployers of an emotion recognition system or a biometric categorisation system shall inform the natural persons exposed thereto of the operation of the system and shall process the personal data in accordance with Regulation (EU) 2016/679 [GDPR], Regulation (EU) 2018/1725 and Directive (EU) 2016/680, as applicable.

**50(4) — Deep fakes:**
> Deployers of an AI system that generates or manipulates image, audio or video content constituting a deep fake shall disclose that the content has been artificially generated or manipulated.

Exception: artistic, creative, satirical, or fictional uses with safeguards.

#### Disclosure characteristics required:
- Clear and distinguishable manner
- At latest at the time of first interaction or exposure
- Accessible to persons with disabilities
- Comply with relevant accessibility standards

**Penalty:** up to €15M or 3% of global annual turnover.

### 2.4 MINIMAL RISK (Default)

No mandatory obligations under the Act. Most AI systems fall here.

Examples:
- Spam filters
- AI in video games
- Inventory management AI
- Recommender systems for entertainment (with caveats — see GPAI rules)
- Predictive maintenance for non-critical equipment

Voluntary codes of conduct encouraged (Article 95).

---

## 3. ARTICLE 50 IMPLEMENTATION GUIDANCE (for Disclosure Agent)

### 3.1 Disclosure placement standards by system type

| System type | Recommended placement | Example wording (EN) |
|---|---|---|
| Chatbot | Header/banner before first user message | "You are chatting with an AI assistant. Responses may be inaccurate." |
| Voice assistant | Audio cue + initial spoken disclosure | "Hi, this is an AI assistant. How can I help you today?" |
| AI-generated image | Visible watermark + EXIF metadata | "AI-generated · [Service name]" |
| AI-generated text | Citation footer | "This content was generated with AI assistance." |
| AI-generated video | Visible watermark + audio disclosure | "This video contains AI-generated content." |
| Deep fake | Prominent disclosure overlay | "This is an AI-generated synthetic media." |
| Emotion recognition | Pre-use notice + consent flow | "This service uses AI to analyze emotional cues from your facial expressions." |

### 3.2 Standard disclosure snippets (templates per language)

**EN — Chatbot (50.1):**
> "You're chatting with an AI assistant, not a human. Responses are generated by [system name] and may be inaccurate."

**IT — Chatbot (50.1):**
> "Stai conversando con un assistente AI, non con una persona. Le risposte sono generate da [nome del sistema] e potrebbero essere inesatte."

**ES — Chatbot (50.1):**
> "Estás interactuando con un asistente de IA, no con una persona. Las respuestas son generadas por [nombre del sistema] y pueden ser inexactas."

**FR — Chatbot (50.1):**
> "Vous discutez avec un assistant IA, et non avec une personne. Les réponses sont générées par [nom du système] et peuvent être inexactes."

**DE — Chatbot (50.1):**
> "Sie chatten mit einem KI-Assistenten, nicht mit einem Menschen. Antworten werden von [Systemname] generiert und können ungenau sein."

(Disclosure Agent generates similar snippets for 50.2, 50.3, 50.4 use cases.)

### 3.3 Technical watermarking requirements (50.2)

Per Recital 134 and emerging guidance:
- Must be **machine-readable**
- Must be **detectable** by available technical means
- Must be **robust** against common modifications (cropping, compression, resaving)
- Standards expected: C2PA Content Credentials, SynthID, watermark protocols
- Implementation note for Codex: in code examples for the Disclosure Agent's output, reference these standards rather than inventing schemes

---

## 4. ANNEX IV — TECHNICAL DOCUMENTATION (for Documentation Agent)

### 4.1 Required sections

Annex IV requires the technical documentation for HIGH_RISK systems to contain at least:

1. **General description** of the AI system:
   - Intended purpose
   - Name(s) of provider and version
   - How AI system interacts with hardware/software (incl. AI systems and beyond)
   - Software versions and firmware
   - Forms in which AI system is placed on market
   - Description of hardware on which AI system runs
   - Photographs/illustrations showing external features

2. **Detailed description of intended purpose:**
   - Users
   - Categories of natural persons/groups affected
   - Foreseeable misuse

3. **Detailed information on monitoring, functioning, and control:**
   - Capabilities and limitations in performance
   - Foreseeable unintended outcomes and risks
   - Human oversight measures (Article 14)
   - Specifications on input data

4. **Description of risk management system (Article 9):**
   - Risk identification and analysis
   - Estimation and evaluation
   - Risk management measures adopted

5. **Description of changes** through lifecycle:
   - Version changes
   - Significant modifications definition

6. **List of harmonised standards** applied or alternative solutions adopted

7. **Copy of EU declaration of conformity**

8. **Description of post-market monitoring plan** (Article 72)

### 4.2 Annex IV template structure (for PDF generation)

```
COVER PAGE
  - System name
  - Provider name
  - Version
  - Document date
  - "Generated by Conforma-AI"

TABLE OF CONTENTS

§1 GENERAL DESCRIPTION
   1.1 Intended purpose
   1.2 Provider information
   1.3 System architecture
   1.4 Hardware/software requirements
   1.5 Market form

§2 INTENDED PURPOSE AND USERS
   2.1 Detailed intended purpose
   2.2 Intended users
   2.3 Affected natural persons
   2.4 Foreseeable misuse

§3 HUMAN OVERSIGHT MEASURES
   3.1 Capabilities and limitations
   3.2 Oversight mechanisms implemented
   3.3 Interpretation of outputs

§4 INPUT DATA SPECIFICATIONS
   4.1 Training data
   4.2 Validation data
   4.3 Test data
   4.4 Data provenance
   4.5 Quality controls

§5 DESIGN SPECIFICATIONS
   5.1 Architecture
   5.2 Key design choices
   5.3 Classification rationale

§6 RISK MANAGEMENT SYSTEM
   6.1 Identified risks
   6.2 Risk estimation
   6.3 Mitigation measures

§7 VALIDATION AND TESTING
   7.1 Test methodology
   7.2 Test datasets
   7.3 Discriminatory bias testing
   7.4 Test results

§8 PERFORMANCE METRICS
   8.1 Accuracy
   8.2 Robustness
   8.3 Cybersecurity
   8.4 Trade-offs

§9 POST-MARKET MONITORING
   9.1 Monitoring system
   9.2 Risk reassessment plan
   9.3 Incident reporting procedure

APPENDIX A — Compliance Gaps Identified
   (List of [GAP — ...] markers from each section)

APPENDIX B — References
   - Regulation EU 2024/1689
   - Source repository: [URL]
   - Audit ID: [UUID]
   - Generation timestamp: [ISO 8601]
```

---

## 5. PENALTY FRAMEWORK (Article 99)

| Violation type | Maximum penalty |
|---|---|
| Prohibited practices (Art. 5) | €35M or 7% global annual turnover |
| Non-compliance with most obligations | €15M or 3% global annual turnover |
| Supply of incorrect/incomplete information | €7.5M or 1% global annual turnover |
| SMEs and startups | Lower of the two thresholds applied |

Member States set additional penalties for breaches not covered above.

**Used by Gap Auditor for Fine Exposure Calculation.**

---

## 6. KEY DEFINITIONS (Article 3)

For agent reasoning consistency:

- **AI system:** "machine-based system designed to operate with varying levels of autonomy and that may exhibit adaptiveness after deployment, and that, for explicit or implicit objectives, infers, from the input it receives, how to generate outputs such as predictions, content, recommendations, or decisions, that can influence physical or virtual environments"

- **Provider:** entity that develops an AI system or has one developed under its name/trademark for placing on the market

- **Deployer:** entity using an AI system under its authority (formerly "user" — terminology changed during legislative process)

- **General-purpose AI model:** model trained on broad data, displays significant generality, capable of performing wide range of distinct tasks

- **High-risk AI system:** see Article 6

- **Substantial modification:** change that significantly affects compliance or changes intended purpose

---

## 7. RELATIONSHIP TO OTHER EU LAW

For agent context:

- **GDPR (Regulation 2016/679):** applies to processing of personal data within AI systems. Article 50(3) explicitly references GDPR compliance.
- **DSA (Digital Services Act):** applies to platforms; AI used in content moderation has dual obligations
- **DMA (Digital Markets Act):** applies to gatekeeper platforms; AI features may trigger DMA obligations
- **NIS2 Directive:** cybersecurity obligations for critical infrastructure overlap with Annex III §2
- **Product Liability Directive (revised 2024):** AI now explicitly covered for product liability claims

Gap Auditor should note when a finding has GDPR co-implications.

---

## 8. SOURCES (for verification by Codex and agents)

**Primary:**
- Regulation (EU) 2024/1689 — Official Journal: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- Implementation timeline (AI Act Service Desk, European Commission): https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act

**Secondary (for Omnibus context):**
- DLA Piper analysis of Omnibus deal: https://knowledge.dlapiper.com (search "Digital AI Omnibus 2026")
- Legal Nodes EU AI Act 2026 updates: https://www.legalnodes.com/article/eu-ai-act-2026-updates-compliance-requirements-and-business-risks
- Secure Privacy EU AI Act compliance: https://secureprivacy.ai/blog/eu-ai-act-2026-compliance

When an agent needs verbatim text of a specific Article or Annex paragraph, fetch from `eur-lex.europa.eu`. **Do not let agents hallucinate Article numbers or paragraph references — the system prompt explicitly forbids this and Codex must enforce JSON schema validation on agent outputs.**

---

## 9. ENGLISH-ONLY TERMINOLOGY MAP

When the Documentation Agent renders to PDF, use these exact terms (matches Official Journal English translation):

| Concept | Official term |
|---|---|
| AI system | "AI system" |
| Provider | "provider" (not "developer") |
| Deployer | "deployer" (not "user") |
| Annex (singular) | "Annex" |
| High-risk | "high-risk" (hyphenated) |
| Article (singular) | "Article" |
| Risk management system | "risk management system" |
| CE marking | "CE marking" |
| Conformity assessment | "conformity assessment" |
| Post-market monitoring | "post-market monitoring" |
| Serious incident | "serious incident" |

Italian, Spanish, French, German translations available in Official Journal — for Disclosure Agent multi-language output, use the official terminology from each language's version of the Regulation (translations published alongside).
