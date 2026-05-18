"use client";

import {
  AlertTriangle,
  ArrowRight,
  BellRing,
  CheckCircle2,
  Eye,
  FileSearch,
  LoaderCircle,
  Radar,
  Scale,
  SearchCode,
  Shield,
  Sparkles,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  createDemoHighRiskSystem,
  generateCompliancePack,
  generateDocumentation,
  getApiBaseUrl,
  getHealth,
  listAuditArtifacts,
  runAudit,
} from "@/lib/api";
import type {
  AgentPipelineItem,
  ArtifactSummary,
  AuditProgressStage,
  CompliancePackResponse,
  DisclosureResponse,
  AuditResponse,
  DemoHighRiskSystemResponse,
  DocumentationResponse,
  GapSeverity,
  HealthResponse,
  RiskClass,
  SampleRepo,
} from "@/lib/types";

const sampleRepos: SampleRepo[] = [
  {
    label: "Resume Screening - Recruitment AI",
    repoUrl: "https://github.com/anukalp-mishra/Resume-Screening",
    maxFiles: 80,
    note: "High-risk recruitment screening and CV ranking sample",
  },
  {
    label: "karpathy/llm.c",
    repoUrl: "https://github.com/karpathy/llm.c",
    maxFiles: 50,
    note: "Compact LLM training and inference repo",
  },
  {
    label: "rasahq/rasa",
    repoUrl: "https://github.com/rasahq/rasa",
    maxFiles: 80,
    note: "Conversational AI stack with multiple candidate systems",
  },
  {
    label: "microsoft/recommenders",
    repoUrl: "https://github.com/microsoft/recommenders",
    maxFiles: 120,
    note: "Large recommendation-system portfolio",
  },
];

const demoHighRiskSeed = {
  name: "bank_cv_ranking_system",
  description:
    "AI system that ranks CVs for recruitment in a bank using education, employment history, skills and interview notes.",
  riskClass: "HIGH_RISK" as const,
  primaryArticle: "Annex III Section 4(a)",
  sourceFiles: ["src/recruitment/ranker.py", "README.md"],
  detectionSignals: [
    "README mentions candidate ranking",
    "ranker.py evaluates applicants for recruiter review",
  ],
};

const auditStages: AuditProgressStage[] = [
  {
    key: "initializing",
    label: "Initializing audit",
    detail: "Bootstrapping the audit session and validating the repository target.",
    buttonLabel: "Running audit...",
    progressStart: 0,
    progressEnd: 20,
  },
  {
    key: "scanning",
    label: "Cloning and scanning repository",
    detail: "Scanner is shallow-cloning the repo and pre-filtering candidate evidence.",
    buttonLabel: "Scanning repository...",
    progressStart: 20,
    progressEnd: 45,
  },
  {
    key: "detecting",
    label: "Detecting AI systems",
    detail: "Scanner is extracting evidence snippets and assembling system candidates.",
    buttonLabel: "Detecting AI systems...",
    progressStart: 45,
    progressEnd: 70,
  },
  {
    key: "classifying",
    label: "Classifying EU AI Act risk",
    detail: "Classifier is mapping findings to Article 5, Annex III, and Article 50.",
    buttonLabel: "Classifying systems...",
    progressStart: 70,
    progressEnd: 90,
  },
  {
    key: "building",
    label: "Building Audit Console",
    detail: "Consolidating the synchronous response and staging the console view.",
    buttonLabel: "Building Audit Console...",
    progressStart: 90,
    progressEnd: 100,
  },
];

const auditStageDurationsMs = [900, 1800, 2200, 2200, 1400];

const riskTone: Record<RiskClass, string> = {
  UNACCEPTABLE: "bg-rose-500/15 text-rose-100 ring-1 ring-rose-400/40",
  HIGH_RISK: "bg-amber-500/15 text-amber-100 ring-1 ring-amber-300/40",
  LIMITED_RISK: "bg-sky-500/15 text-sky-100 ring-1 ring-sky-300/40",
  MINIMAL_RISK: "bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-300/40",
};

const riskIndexTone = (value: number): string => {
  if (value >= 85) return "text-rose-200";
  if (value >= 65) return "text-amber-200";
  if (value >= 35) return "text-sky-200";
  return "text-emerald-200";
};

const complianceScoreTone = (value: number): string => {
  if (value >= 85) return "text-emerald-200";
  if (value >= 65) return "text-sky-200";
  if (value >= 40) return "text-amber-200";
  return "text-rose-200";
};

const complianceScoreBand = (value: number): string => {
  if (value >= 85) return "Strong";
  if (value >= 65) return "On track";
  if (value >= 40) return "At risk";
  return "Critical";
};

const gapSeverityTone: Record<GapSeverity, string> = {
  CRITICAL: "bg-rose-500/15 text-rose-100 ring-1 ring-rose-400/35",
  HIGH: "bg-amber-500/15 text-amber-100 ring-1 ring-amber-300/35",
  MEDIUM: "bg-sky-500/15 text-sky-100 ring-1 ring-sky-300/35",
  LOW: "bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-300/35",
};

function formatEuros(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

function getSimulatedProgress(elapsedMs: number): number {
  let remainingMs = elapsedMs;

  for (const [index, stage] of auditStages.entries()) {
    const durationMs = auditStageDurationsMs[index];
    const stageEnd = index === auditStages.length - 1 ? 97 : stage.progressEnd;

    if (remainingMs <= durationMs) {
      const progressRatio = Math.min(remainingMs / durationMs, 1);
      return stage.progressStart + (stageEnd - stage.progressStart) * progressRatio;
    }

    remainingMs -= durationMs;
  }

  return 97;
}

function getStageIndex(progress: number): number {
  if (progress >= 90) return 4;
  if (progress >= 70) return 3;
  if (progress >= 45) return 2;
  if (progress >= 20) return 1;
  return 0;
}

function buildPipeline(
  audit: AuditResponse | null,
  isAuditRunning: boolean,
  stageIndex: number,
  documentationReady: boolean,
  isDocumentationRunning: boolean,
  compliancePackReady: boolean,
  isCompliancePackRunning: boolean,
  hasDisclosureSystems: boolean,
): AgentPipelineItem[] {
  const scannerState = audit
    ? "complete"
    : isAuditRunning
      ? stageIndex <= 2
        ? "active"
        : "complete"
      : "idle";
  const classifierState = audit
    ? "complete"
    : isAuditRunning
      ? stageIndex >= 3
        ? "active"
        : "idle"
      : "idle";
  const documentationState = documentationReady
    ? "complete"
    : isDocumentationRunning
      ? "active"
      : audit
        ? "idle"
        : "queued";
  const disclosureState = compliancePackReady && hasDisclosureSystems
    ? "complete"
    : isCompliancePackRunning && hasDisclosureSystems
      ? "active"
      : audit
        ? "idle"
        : "queued";
  const gapAuditorState = compliancePackReady
    ? "complete"
    : isCompliancePackRunning
      ? "active"
      : audit
        ? "idle"
        : "queued";

  return [
    {
      name: "Scanner",
      model: "gemini-3-flash-preview",
      blurb: "Clone the repo, shortlist evidence, and inventory candidate AI systems.",
      state: scannerState,
      cue:
        scannerState === "active"
          ? "Live in D4B"
          : scannerState === "complete"
            ? "Completed"
            : "Ready",
    },
    {
      name: "Classifier",
      model: "gemini-3.1-pro-preview",
      blurb: "Map each detected system to Article 5, Annex III, or Article 50 obligations.",
      state: classifierState,
      cue:
        classifierState === "active"
          ? "Live in D4B"
          : classifierState === "complete"
            ? "Completed"
            : "Queued after scan",
    },
    {
      name: "Documentation",
      model: "gemini-3.1-pro-preview",
      blurb: "Generate Annex IV technical documentation and PDF artifacts for high-risk systems.",
      state: documentationState,
      cue:
        documentationState === "complete"
          ? "Artifact ready"
          : documentationState === "active"
            ? "Generating"
            : "Live on demand",
    },
    {
      name: "Disclosure",
      model: "gemini-3-flash-preview",
      blurb: "Generate multilingual Article 50 notices and placement guidance for exposed users.",
      state: disclosureState,
      cue:
        disclosureState === "complete"
          ? "Pack ready"
          : disclosureState === "active"
            ? "Generating"
            : "Ready in pack",
    },
    {
      name: "Gap Auditor",
      model: "gemini-3.1-pro-preview",
      blurb: "Compute compliance score, fine exposure, and prioritized remediation gaps.",
      state: gapAuditorState,
      cue:
        gapAuditorState === "complete"
          ? "Completed"
          : gapAuditorState === "active"
            ? "Scoring"
            : "Ready in pack",
    },
    {
      name: "Monitor",
      model: "gemini-3-flash-preview",
      blurb: "Deadline alerts and post-audit monitoring complete the loop later.",
      state: "queued",
      cue: "Queued for D4",
    },
  ];
}

function stateTone(state: AgentPipelineItem["state"]): string {
  switch (state) {
    case "complete":
      return "border-emerald-400/30 bg-emerald-500/10";
    case "active":
      return "agent-card-live border-sky-400/35 bg-sky-500/10";
    case "queued":
      return "border-white/10 bg-slate-950/50";
    default:
      return "border-white/10 bg-slate-950/35";
  }
}

function stateBadgeTone(state: AgentPipelineItem["state"]): string {
  switch (state) {
    case "complete":
      return "bg-emerald-500/15 text-emerald-100";
    case "active":
      return "bg-sky-500/15 text-sky-100";
    case "queued":
      return "bg-white/5 text-slate-300";
    default:
      return "bg-white/5 text-slate-300";
  }
}

function stateLabel(state: AgentPipelineItem["state"]): string {
  switch (state) {
    case "complete":
      return "Complete";
    case "active":
      return "Active";
    case "queued":
      return "Queued for D4";
    default:
      return "Ready";
  }
}

export default function HomePage() {
  const isDevelopment = process.env.NODE_ENV === "development";
  const [repoUrl, setRepoUrl] = useState<string>(sampleRepos[0].repoUrl);
  const [maxFiles, setMaxFiles] = useState<number>(sampleRepos[0].maxFiles);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isAuditRunning, setIsAuditRunning] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [stageIndex, setStageIndex] = useState<number>(0);
  const [annexIvArtifactMap, setAnnexIvArtifactMap] = useState<Record<string, ArtifactSummary>>({});
  const [documentationMap, setDocumentationMap] = useState<Record<string, DocumentationResponse>>({});
  const [documentationErrors, setDocumentationErrors] = useState<Record<string, string>>({});
  const [documentationLoadingId, setDocumentationLoadingId] = useState<string | null>(null);
  const [compliancePack, setCompliancePack] = useState<CompliancePackResponse | null>(null);
  const [compliancePackError, setCompliancePackError] = useState<string | null>(null);
  const [isCompliancePackRunning, setIsCompliancePackRunning] = useState<boolean>(false);
  const [demoSystem, setDemoSystem] = useState<DemoHighRiskSystemResponse | null>(null);
  const [isCreatingDemo, setIsCreatingDemo] = useState<boolean>(false);
  const [demoError, setDemoError] = useState<string | null>(null);
  const resultsRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const payload = await getHealth();
        setHealth(payload);
        setBackendError(null);
      } catch (error) {
        setBackendError(
          error instanceof Error
            ? error.message
            : "The backend is unavailable. Start the API at localhost:8000 and refresh.",
        );
      }
    })();
  }, []);

  useEffect(() => {
    if (!isAuditRunning) {
      return undefined;
    }

    const startedAt = Date.now();
    const intervalId = window.setInterval(() => {
      const elapsedMs = Date.now() - startedAt;
      const simulatedProgress = getSimulatedProgress(elapsedMs);
      setProgress((currentProgress) => {
        const nextProgress = Math.max(currentProgress, simulatedProgress);
        return Math.min(nextProgress, 97);
      });
    }, 120);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [isAuditRunning]);

  useEffect(() => {
    setStageIndex(getStageIndex(progress));
  }, [progress]);

  useEffect(() => {
    if (!audit || isAuditRunning) {
      return;
    }

    resultsRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [audit, isAuditRunning]);

  useEffect(() => {
    if (!audit) {
      return;
    }

    void (async () => {
      try {
        const payload = await listAuditArtifacts(audit.audit_id);
        const nextArtifacts: Record<string, ArtifactSummary> = {};
        payload.artifacts.forEach((artifact) => {
          if (artifact.ai_system_id && artifact.kind === "annex_iv_pdf") {
            nextArtifacts[artifact.ai_system_id] = artifact;
          }
        });
        setAnnexIvArtifactMap((currentArtifacts) => ({ ...currentArtifacts, ...nextArtifacts }));
      } catch {
        return;
      }
    })();
  }, [audit]);

  const documentationReady = useMemo(
    () =>
      Object.keys(annexIvArtifactMap).length > 0 ||
      Object.values(documentationMap).some(
        (response) => response.required && response.status === "generated",
      ),
    [annexIvArtifactMap, documentationMap],
  );
  const hasDisclosureSystems = useMemo(
    () => audit?.systems.some((system) => system.triggers_article_50) ?? false,
    [audit],
  );
  const pipeline = useMemo(
    () =>
      buildPipeline(
        audit,
        isAuditRunning,
        stageIndex,
        documentationReady,
        documentationLoadingId !== null,
        compliancePack !== null,
        isCompliancePackRunning,
        hasDisclosureSystems,
      ),
    [
      audit,
      compliancePack,
      documentationLoadingId,
      documentationReady,
      hasDisclosureSystems,
      isAuditRunning,
      isCompliancePackRunning,
      stageIndex,
    ],
  );
  const currentStage = auditStages[stageIndex] ?? auditStages[0];
  const disclosureMap = useMemo(() => {
    const nextMap: Record<string, DisclosureResponse> = {};
    compliancePack?.disclosures.forEach((disclosure) => {
      nextMap[disclosure.ai_system_id] = disclosure;
    });
    return nextMap;
  }, [compliancePack]);
  const complianceGapCounts = useMemo(() => {
    const counts: Record<GapSeverity, number> = {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0,
    };
    compliancePack?.gaps.forEach((gap) => {
      counts[gap.severity] += 1;
    });
    return counts;
  }, [compliancePack]);

  const refreshArtifacts = async (auditId: string) => {
    try {
      const payload = await listAuditArtifacts(auditId);
      const nextArtifacts: Record<string, ArtifactSummary> = {};
      payload.artifacts.forEach((artifact) => {
        if (artifact.ai_system_id && artifact.kind === "annex_iv_pdf") {
          nextArtifacts[artifact.ai_system_id] = artifact;
        }
      });
      setAnnexIvArtifactMap((currentArtifacts) => ({ ...currentArtifacts, ...nextArtifacts }));
    } catch {
      return;
    }
  };

  const runDocumentationForSystem = async (options: {
    auditId: string;
    aiSystemId: string;
    systemName: string;
    systemDescription: string;
    riskClass: RiskClass;
    primaryArticle: string;
    sourceFiles: string[];
    detectionSignals: string[];
    repoUrl?: string;
  }) => {
    setDocumentationLoadingId(options.aiSystemId);
    setDocumentationErrors((currentErrors) => {
      const nextErrors = { ...currentErrors };
      delete nextErrors[options.aiSystemId];
      return nextErrors;
    });

    try {
      const response = await generateDocumentation({
        audit_id: options.auditId,
        ai_system_id: options.aiSystemId,
        system_description: options.systemDescription,
        risk_class: options.riskClass,
        primary_article: options.primaryArticle,
        source_code_snippets: [
          ...options.sourceFiles.map((sourceFile) => `Referenced source file: ${sourceFile}`),
          ...options.detectionSignals.map((signal) => `Evidence trail: ${signal}`),
        ].slice(0, 10),
        repo_metadata: {
          repo_url: options.repoUrl ?? "demo://high-risk-system",
          source_files: options.sourceFiles,
          detection_signals: options.detectionSignals,
          system_name: options.systemName,
        },
      });

      setDocumentationMap((currentResponses) => ({
        ...currentResponses,
        [options.aiSystemId]: response,
      }));
      if (response.artifact) {
        setAnnexIvArtifactMap((currentArtifacts) => ({
          ...currentArtifacts,
          [options.aiSystemId]: response.artifact!,
        }));
      }
      await refreshArtifacts(options.auditId);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Annex IV generation failed. Verify that the backend and PDF stack are available.";
      setDocumentationErrors((currentErrors) => ({
        ...currentErrors,
        [options.aiSystemId]: message,
      }));
    } finally {
      setDocumentationLoadingId(null);
    }
  };

  const generateDemoDocumentation = async () => {
    if (!demoSystem) {
      return;
    }

    await runDocumentationForSystem({
      auditId: demoSystem.audit_id,
      aiSystemId: demoSystem.ai_system_id,
      systemName: demoHighRiskSeed.name,
      systemDescription: demoHighRiskSeed.description,
      riskClass: demoHighRiskSeed.riskClass,
      primaryArticle: demoHighRiskSeed.primaryArticle,
      sourceFiles: demoHighRiskSeed.sourceFiles,
      detectionSignals: demoHighRiskSeed.detectionSignals,
      repoUrl: "https://github.com/demo/bank-cv-ranking-system",
    });
  };

  const createDemoSystem = async () => {
    setDemoError(null);
    setIsCreatingDemo(true);

    try {
      const payload = await createDemoHighRiskSystem();
      setDemoSystem(payload);
      await refreshArtifacts(payload.audit_id);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to create the demo high-risk system. Verify that the backend is running.";
      setDemoError(message);
    } finally {
      setIsCreatingDemo(false);
    }
  };

  const applySample = (sample: SampleRepo) => {
    if (isAuditRunning || isCompliancePackRunning) {
      return;
    }

    setRepoUrl(sample.repoUrl);
    setMaxFiles(sample.maxFiles);
    setRequestError(null);
  };

  const submit = async () => {
    setRequestError(null);
    setAudit(null);
    setAnnexIvArtifactMap({});
    setDocumentationMap({});
    setDocumentationErrors({});
    setCompliancePack(null);
    setCompliancePackError(null);
    setIsAuditRunning(true);
    setProgress(6);
    setStageIndex(0);

    try {
      const payload = await runAudit({
        repo_url: repoUrl,
        max_files_to_inspect: maxFiles,
      });

      setProgress(100);
      setStageIndex(auditStages.length - 1);
      setAudit(payload);
      setBackendError(null);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Audit failed. Verify that the backend and local services are running.";
      setRequestError(message);
      setProgress(0);
      setStageIndex(0);
    } finally {
      setIsAuditRunning(false);
    }
  };

  const runCompliancePack = async () => {
    if (!audit) {
      return;
    }

    setCompliancePackError(null);
    setIsCompliancePackRunning(true);

    try {
      const payload = await generateCompliancePack(audit.audit_id);
      setCompliancePack(payload);
      await refreshArtifacts(audit.audit_id);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Compliance Pack generation failed. Verify that the backend is running and try again.";
      setCompliancePackError(message);
    } finally {
      setIsCompliancePackRunning(false);
    }
  };

  const isRunningWithoutResults = isAuditRunning && !audit;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(37,99,235,0.24),_transparent_38%),radial-gradient(circle_at_85%_15%,_rgba(14,165,233,0.16),_transparent_25%),linear-gradient(180deg,_#04111f_0%,_#07162b_45%,_#04101c_100%)] text-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-6 lg:px-8 lg:py-8">
        <header className="panel-shell overflow-hidden">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(56,189,248,0.08),transparent_28%,rgba(59,130,246,0.05)_55%,transparent)]" />
          <div className="relative grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.3em] text-sky-100">
                <Shield className="h-3.5 w-3.5" />
                Conforma-AI Audit Console
              </div>
              <p className="mt-5 text-sm font-semibold uppercase tracking-[0.32em] text-sky-200/90">
                D4B Demo Grade
              </p>
              <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-tight text-slate-50 md:text-6xl">
                Scanner, Classifier, and Annex IV documentation inside one EU AI Act console.
              </h1>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-200">
                Point the console at a public repository, inventory candidate AI systems, and map
                them to Article 5, Annex III, or Article 50 obligations with portfolio-level risk
                visibility, then generate Annex IV PDF artifacts for the high-risk systems.
              </p>
            </div>

            <div className="grid gap-4 rounded-[30px] border border-white/10 bg-slate-950/45 p-5 shadow-[0_24px_80px_rgba(2,12,27,0.45)]">
              <div className="flex items-center justify-between gap-4">
                <span className="text-sm text-slate-300">Backend status</span>
                {health ? (
                  <span className="inline-flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-100">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {health.status}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-2 rounded-full bg-amber-500/15 px-3 py-1 text-xs font-semibold text-amber-100">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    {backendError ? "offline" : "checking"}
                  </span>
                )}
              </div>
              <dl className="grid gap-2 text-sm text-slate-300">
                <div className="flex justify-between gap-4">
                  <dt>Service</dt>
                  <dd className="font-mono text-slate-100">{health?.service ?? "conforma-ai"}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt>Version</dt>
                  <dd className="font-mono text-slate-100">{health?.version ?? "0.1.0"}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt>API target</dt>
                  <dd className="font-mono text-slate-100">{getApiBaseUrl()}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt>Execution mode</dt>
                  <dd className="text-slate-100">Synchronous D4B audit flow</dd>
                </div>
              </dl>
              <p className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-slate-300">
                D4B keeps the main audit synchronous, then layers Documentation, Disclosure, and
                Gap Auditor on demand once the AI systems inventory is ready. Monitor remains the
                next visible stage in the six-agent roadmap.
              </p>
            </div>
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
          <article className="panel-shell">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-200">
                  Run Audit
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-50">
                  Inventory and classify a public AI codebase
                </h2>
              </div>
              <SearchCode className="h-6 w-6 text-sky-200" />
            </div>

            <label htmlFor="repo-url" className="mt-6 block text-sm font-medium text-slate-200">
              Repository URL
            </label>
            <input
              id="repo-url"
              type="url"
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              disabled={isAuditRunning || isCompliancePackRunning}
              className="mt-3 w-full rounded-[24px] border border-white/10 bg-slate-950/55 px-4 py-4 text-base text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-sky-400/60 focus:ring-2 focus:ring-sky-400/20 disabled:cursor-not-allowed disabled:opacity-70"
              placeholder="https://github.com/org/repo"
            />

            <div className="mt-5 grid gap-4 md:grid-cols-[0.72fr_1fr]">
              <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Scan window
                </p>
                <p className="mt-2 text-3xl font-semibold text-slate-50">{maxFiles}</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Max candidate files passed from the pre-filter into the audit path.
                </p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Sample repositories
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {sampleRepos.map((sample) => (
                    <button
                       key={sample.label}
                       type="button"
                       onClick={() => applySample(sample)}
                       disabled={isAuditRunning || isCompliancePackRunning}
                      className="rounded-full border border-white/10 bg-slate-950/45 px-3 py-2 text-sm text-slate-200 transition hover:border-sky-300/40 hover:bg-sky-500/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {sample.label}
                    </button>
                  ))}
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  Click a sample to preload its repo URL and an appropriate inspection budget.
                </p>
              </div>
            </div>

            <div className="mt-5 grid gap-2">
              {sampleRepos.map((sample) => (
                <div
                  key={`${sample.label}-note`}
                  className={`rounded-2xl border px-4 py-3 text-sm leading-6 ${
                    repoUrl === sample.repoUrl
                      ? "border-sky-400/35 bg-sky-500/10 text-sky-100"
                      : "border-white/10 bg-slate-950/30 text-slate-400"
                  }`}
                >
                  <span className="font-semibold text-slate-100">{sample.label}</span> -{" "}
                  {sample.note}
                </div>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => {
                  void submit();
                }}
                disabled={isAuditRunning || isCompliancePackRunning}
                className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isAuditRunning ? (
                  <>
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                    {currentStage.buttonLabel}
                  </>
                ) : (
                  <>
                    Run audit
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
              <p className="text-sm text-slate-400">
                The console calls <span className="font-mono text-slate-200">POST /api/v1/audits</span>.
              </p>
            </div>

            {isDevelopment ? (
              <details className="mt-5 rounded-[24px] border border-white/10 bg-slate-950/30 px-4 py-4 text-sm text-slate-300">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                      Developer sandbox
                    </p>
                    <p className="mt-1 text-sm leading-6 text-slate-300">
                      Seed a synthetic high-risk system for Annex IV testing without running a full repository audit.
                    </p>
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-300">
                    Development only
                  </span>
                </summary>

                <div className="mt-4 border-t border-white/10 pt-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        void createDemoSystem();
                      }}
                      disabled={isCreatingDemo || isAuditRunning}
                      className="inline-flex items-center gap-2 rounded-full border border-sky-400/25 bg-sky-500/10 px-4 py-2.5 text-sm font-semibold text-sky-100 transition hover:border-sky-300/45 hover:bg-sky-500/15 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isCreatingDemo ? (
                        <>
                          <LoaderCircle className="h-4 w-4 animate-spin" />
                          Creating demo system...
                        </>
                      ) : (
                        "Create demo high-risk system"
                      )}
                    </button>
                    <p className="text-sm text-slate-400">
                      Seeds a bank CV ranking system for internal D4B validation.
                    </p>
                  </div>

                  {demoSystem ? (
                    <div className="mt-4 rounded-[24px] border border-sky-400/20 bg-sky-500/10 p-4 fade-rise">
                      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-200">
                            Demo high-risk seed ready
                          </p>
                          <p className="mt-2 text-lg font-semibold text-slate-50">
                            {demoHighRiskSeed.name}
                          </p>
                          <p className="mt-2 text-sm leading-6 text-slate-300">
                            {demoHighRiskSeed.description}
                          </p>
                          <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-300">
                            <span className="rounded-full border border-white/10 bg-slate-950/35 px-3 py-1 font-mono">
                              Audit {demoSystem.audit_id}
                            </span>
                            <span className="rounded-full border border-white/10 bg-slate-950/35 px-3 py-1 font-mono">
                              System {demoSystem.ai_system_id}
                            </span>
                          </div>
                        </div>
                        <div className="flex flex-col items-start gap-3 xl:items-end">
                          <button
                            type="button"
                            onClick={() => {
                              void generateDemoDocumentation();
                            }}
                            disabled={documentationLoadingId === demoSystem.ai_system_id}
                            className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            {documentationLoadingId === demoSystem.ai_system_id ? (
                              <>
                                <LoaderCircle className="h-4 w-4 animate-spin" />
                                Generating Annex IV...
                              </>
                            ) : (
                              "Generate Annex IV PDF"
                            )}
                          </button>
                          {annexIvArtifactMap[demoSystem.ai_system_id] ? (
                            <a
                              href={annexIvArtifactMap[demoSystem.ai_system_id].download_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sm font-semibold text-sky-100 underline decoration-sky-300/50 underline-offset-4"
                            >
                              Download generated Annex IV PDF
                            </a>
                          ) : null}
                        </div>
                      </div>
                      {documentationMap[demoSystem.ai_system_id]?.message ? (
                        <p className="mt-4 text-sm leading-6 text-slate-300">
                          {documentationMap[demoSystem.ai_system_id].message}
                        </p>
                      ) : null}
                      {documentationErrors[demoSystem.ai_system_id] ? (
                        <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                          {documentationErrors[demoSystem.ai_system_id]}
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  {demoError ? (
                    <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                      {demoError}
                    </div>
                  ) : null}
                </div>
              </details>
            ) : null}

            {isRunningWithoutResults ? (
              <div className="mt-5 rounded-[24px] border border-sky-400/25 bg-sky-500/10 p-4 fade-rise">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-200">
                      Audit running
                    </p>
                    <p className="mt-2 text-lg font-semibold text-slate-50">{currentStage.label}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{currentStage.detail}</p>
                  </div>
                  <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-sky-300/25 bg-slate-950/45">
                    <Sparkles className="h-5 w-5 text-sky-100" />
                  </div>
                </div>
                <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-white/8">
                  <div className="progress-shell h-full rounded-full" style={{ width: `${progress}%` }} />
                </div>
                <div className="mt-3 flex items-center justify-between gap-4 text-xs uppercase tracking-[0.18em] text-slate-400">
                  <span>Progress</span>
                  <span className="font-semibold text-sky-100">{Math.round(progress)}%</span>
                </div>
              </div>
            ) : null}

            {requestError ? (
              <div className="mt-5 rounded-[24px] border border-rose-400/30 bg-rose-500/10 p-4 fade-rise">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 rounded-2xl border border-rose-300/20 bg-rose-500/15 p-2">
                    <AlertTriangle className="h-4 w-4 text-rose-100" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-rose-100">Audit could not complete</p>
                    <p className="mt-1 text-sm leading-6 text-rose-50/90">{requestError}</p>
                  </div>
                </div>
              </div>
            ) : null}

            {backendError ? (
              <div className="mt-5 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm leading-6 text-amber-100">
                Backend connection issue: {backendError}
              </div>
            ) : null}
          </article>

          <aside className="panel-shell">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-200">
                  Agent Pipeline
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-50">
                  Six-agent roadmap, with Documentation now available on demand
                </h2>
              </div>
              <Radar className="h-6 w-6 text-sky-200" />
            </div>

            <div className="mt-6 overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                    Audit progress
                  </p>
                  <p className="mt-2 text-xl font-semibold text-slate-50">
                    {isAuditRunning
                      ? currentStage.label
                      : audit
                        ? "Audit completed"
                        : "Ready to launch"}
                  </p>
                </div>
                <div
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${
                    isAuditRunning
                      ? "cockpit-pulse border border-sky-300/25 bg-sky-500/15 text-sky-100"
                      : audit
                        ? "border border-emerald-300/25 bg-emerald-500/15 text-emerald-100"
                        : "border border-white/10 bg-white/5 text-slate-300"
                  }`}
                >
                  {isAuditRunning ? "Audit running" : audit ? "Complete" : "Idle"}
                </div>
              </div>

              <p className="mt-3 text-sm leading-6 text-slate-300">
                {isAuditRunning
                  ? currentStage.detail
                  : audit
                    ? "Scanner and Classifier completed. Documentation, Disclosure, and Gap Auditor are now available on demand for the selected audit."
                    : "Launch a repo audit to activate Scanner plus Classifier, then generate Annex IV PDFs and a compliance pack from the resulting inventory."}
              </p>

              <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/8">
                <div
                  className="progress-shell h-full rounded-full"
                  style={{ width: `${audit ? 100 : progress}%` }}
                />
              </div>

              <div className="mt-3 flex items-center justify-between gap-4 text-xs uppercase tracking-[0.18em] text-slate-400">
                <span>{isAuditRunning ? "Current stage" : audit ? "Latest run" : "Pipeline state"}</span>
                <span className="font-semibold text-slate-100">
                  {audit ? "100%" : `${Math.round(progress)}%`}
                </span>
              </div>

              <div className="mt-5 grid gap-2 md:grid-cols-5">
                {auditStages.map((stage, index) => {
                  const stageState = audit
                    ? "complete"
                    : index < stageIndex
                      ? "complete"
                      : index === stageIndex && isAuditRunning
                        ? "active"
                        : "idle";

                  return (
                    <div
                      key={stage.key}
                      className={`rounded-2xl border px-3 py-3 text-xs transition ${
                        stageState === "complete"
                          ? "border-emerald-400/25 bg-emerald-500/10 text-emerald-100"
                          : stageState === "active"
                            ? "cockpit-pulse border-sky-400/30 bg-sky-500/10 text-sky-100"
                            : "border-white/10 bg-white/[0.03] text-slate-400"
                      }`}
                    >
                      <p className="font-semibold uppercase tracking-[0.16em]">
                        {stage.progressStart}-{stage.progressEnd}%
                      </p>
                      <p className="mt-2 leading-5">{stage.label}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            <p className="mt-4 text-sm leading-6 text-slate-400">
              This D4B console keeps the core audit synchronous. LangGraph fan-out and SSE streaming arrive later.
            </p>

            <div className="mt-6 grid gap-3">
              {pipeline.map((item, index) => (
                <article
                  key={item.name}
                  className={`rounded-[26px] border p-4 transition ${stateTone(item.state)}`}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-slate-950/50 text-sm font-semibold text-slate-100">
                      {item.state === "active" ? (
                        <span className="live-dot h-2.5 w-2.5 rounded-full bg-sky-300" />
                      ) : item.state === "complete" ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-200" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-semibold text-slate-50">{item.name}</h3>
                        <span
                          className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${stateBadgeTone(item.state)}`}
                        >
                          {stateLabel(item.state)}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-300">{item.blurb}</p>
                      <div className="mt-3 flex flex-wrap items-center gap-3">
                        <p className="font-mono text-xs text-slate-400">{item.model}</p>
                        {item.cue ? (
                          <span className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                            {item.cue}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </aside>
        </section>

        <section
          ref={resultsRef}
          className={`grid gap-6 xl:grid-cols-[0.62fr_1.38fr] ${
            audit ? "fade-rise" : ""
          }`}
        >
          <article className="panel-shell">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-200">
                  Portfolio Metric
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-50">
                  Repo-level risk concentration
                </h2>
              </div>
              <Scale className="h-6 w-6 text-sky-200" />
            </div>

            {!audit && !isRunningWithoutResults ? (
              <div className="mt-6 rounded-[28px] border border-dashed border-white/10 bg-white/[0.03] p-6 text-sm leading-7 text-slate-400">
                Run an audit to compute the deterministic portfolio risk index and surface the
                detected AI systems inventory.
              </div>
            ) : null}

            {isRunningWithoutResults ? (
              <div className="mt-6 grid gap-4 fade-rise">
                <div className="relative overflow-hidden rounded-[30px] border border-sky-400/20 bg-slate-950/55 p-6">
                  <div className="absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.22),_transparent_60%)]" />
                  <div className="relative">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                      Audit running
                    </p>
                    <div className="mt-3 flex items-end gap-4">
                      <span className="text-6xl font-semibold tracking-tight text-sky-100">
                        {Math.round(progress)}
                      </span>
                      <span className="pb-2 text-lg text-slate-400">%</span>
                    </div>
                    <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/8">
                      <div
                        className="progress-shell h-full rounded-full"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5 text-sm leading-7 text-slate-300">
                  <p className="font-semibold text-slate-50">{currentStage.label}</p>
                  <p className="mt-2">{currentStage.detail}</p>
                  <p className="mt-4 text-slate-400">
                    Portfolio scoring and AI system cards will populate as soon as the synchronous
                    audit response returns.
                  </p>
                </div>
              </div>
            ) : null}

            {audit ? (
              <div className="mt-6 grid gap-4 fade-rise">
                <div className="relative overflow-hidden rounded-[30px] border border-white/10 bg-slate-950/50 p-6">
                  <div className="absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.22),_transparent_60%)]" />
                  <div className="relative">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                      Portfolio Risk Index
                    </p>
                    <div className="mt-3 flex items-end gap-4">
                      <span
                        className={`text-6xl font-semibold tracking-tight ${riskIndexTone(audit.portfolio_risk_index)}`}
                      >
                        {audit.portfolio_risk_index}
                      </span>
                      <span className="pb-2 text-lg text-slate-400">/ 100</span>
                    </div>
                    <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/8">
                      <div
                        className="h-full rounded-full bg-[linear-gradient(90deg,rgba(16,185,129,0.95)_0%,rgba(56,189,248,0.95)_42%,rgba(245,158,11,0.95)_72%,rgba(244,63,94,0.95)_100%)] transition-[width] duration-700"
                        style={{ width: `${audit.portfolio_risk_index}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5 text-sm">
                  <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
                    <div>
                      <p className="text-slate-400">Audit ID</p>
                      <p className="mt-1 font-mono text-xs text-slate-100 md:text-sm">
                        {audit.audit_id}
                      </p>
                      <p className="mt-5 leading-7 text-slate-300">{audit.summary}</p>
                    </div>
                    <div className="flex min-w-[220px] flex-col items-start gap-3 xl:items-end">
                      <div className="text-left xl:text-right">
                        <p className="text-slate-400">Status</p>
                        <p className="mt-1 font-semibold text-emerald-100">{audit.status}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          void runCompliancePack();
                        }}
                        disabled={isCompliancePackRunning}
                        className="inline-flex items-center gap-2 rounded-full border border-sky-400/25 bg-sky-500/10 px-4 py-2.5 text-sm font-semibold text-sky-100 transition hover:border-sky-300/45 hover:bg-sky-500/15 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isCompliancePackRunning ? (
                          <>
                            <LoaderCircle className="h-4 w-4 animate-spin" />
                            Generating Compliance Pack...
                          </>
                        ) : (
                          <>
                            Generate Compliance Pack
                            <ArrowRight className="h-4 w-4" />
                          </>
                        )}
                      </button>
                      {compliancePack ? (
                        <div className="rounded-2xl border border-emerald-300/20 bg-emerald-500/10 px-4 py-3 text-left text-xs leading-6 text-emerald-100 xl:text-right">
                          <p className="font-semibold uppercase tracking-[0.16em] text-emerald-100/90">
                            Latest pack
                          </p>
                          <p className="mt-1">
                            Score {compliancePack.compliance_score}/100 - {compliancePack.gaps.length} gap(s)
                          </p>
                        </div>
                      ) : (
                        <p className="max-w-[220px] text-left text-xs leading-6 text-slate-400 xl:text-right">
                          Generate the D4B pack to compute disclosure notices, compliance score,
                          and remediation priorities.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </article>

          <article className="panel-shell">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-200">
                  AI Systems Inventory
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-50">
                  Evidence-backed system cards for Scanner plus Classifier
                </h2>
              </div>
              <FileSearch className="h-6 w-6 text-sky-200" />
            </div>

            {!audit && !isRunningWithoutResults ? (
              <div className="mt-6 rounded-[28px] border border-dashed border-white/10 bg-white/[0.03] p-6 text-sm leading-7 text-slate-400">
                The inventory panel will populate with detected AI systems, evidence trails, risk
                badges, article references, confidence, and deadlines after the audit finishes.
              </div>
            ) : null}

            {isRunningWithoutResults ? (
              <div className="mt-6 grid gap-4 fade-rise">
                {[0, 1].map((placeholder) => (
                  <article
                    key={`loading-card-${placeholder}`}
                    className="rounded-[28px] border border-sky-400/20 bg-slate-950/45 p-5"
                  >
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-3">
                          <div className="h-7 w-44 rounded-full bg-white/10" />
                          <div className="cockpit-pulse rounded-full border border-sky-400/20 bg-sky-500/10 px-3 py-1 text-xs font-semibold text-sky-100">
                            {placeholder === 0 ? "Scanner active" : "Classifier queued"}
                          </div>
                        </div>
                        <div className="mt-4 grid gap-2">
                          <div className="h-4 w-full rounded-full bg-white/8" />
                          <div className="h-4 w-11/12 rounded-full bg-white/8" />
                          <div className="h-4 w-8/12 rounded-full bg-white/8" />
                        </div>
                      </div>
                      <div className="grid gap-3 rounded-[22px] border border-white/10 bg-white/[0.03] p-4 text-sm xl:min-w-[250px]">
                        <div className="h-4 w-28 rounded-full bg-white/8" />
                        <div className="h-4 w-36 rounded-full bg-white/8" />
                        <div className="h-4 w-24 rounded-full bg-white/8" />
                      </div>
                    </div>

                    <div className="mt-5 grid gap-4 lg:grid-cols-[0.78fr_1.22fr]">
                      <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
                        <div className="h-4 w-28 rounded-full bg-white/8" />
                        <div className="mt-4 flex flex-wrap gap-2">
                          <div className="h-7 w-36 rounded-full bg-sky-500/10" />
                          <div className="h-7 w-32 rounded-full bg-sky-500/10" />
                          <div className="h-7 w-40 rounded-full bg-sky-500/10" />
                        </div>
                      </div>
                      <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
                        <div className="h-4 w-40 rounded-full bg-white/8" />
                        <div className="mt-4 grid gap-2">
                          <div className="h-4 w-full rounded-full bg-white/8" />
                          <div className="h-4 w-10/12 rounded-full bg-white/8" />
                          <div className="h-4 w-7/12 rounded-full bg-white/8" />
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : null}

            {audit ? (
              <div className="mt-6 grid gap-4 fade-rise">
                {audit.systems.map((system) => {
                  const documentationResponse = documentationMap[system.id];
                  const artifact =
                    documentationResponse?.artifact ?? annexIvArtifactMap[system.id] ?? null;
                  const documentationError = documentationErrors[system.id];
                  const isDocumentationLoading = documentationLoadingId === system.id;
                  const disclosure = disclosureMap[system.id];

                  return (
                    <article
                      key={system.id}
                      className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5 shadow-[0_20px_70px_rgba(3,10,20,0.35)]"
                    >
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-3">
                          <h3 className="text-xl font-semibold text-slate-50">{system.name}</h3>
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${riskTone[system.risk_class]}`}
                          >
                            {system.risk_class.replace("_", " ")}
                          </span>
                          {system.triggers_article_50 ? (
                            <span className="rounded-full bg-sky-500/15 px-3 py-1 text-xs font-semibold text-sky-100 ring-1 ring-sky-400/30">
                              Article 50 trigger
                            </span>
                          ) : null}
                          {system.triggers_article_50 ? (
                            disclosure?.requires_disclosure ? (
                              <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-100 ring-1 ring-emerald-300/30">
                                Disclosure ready
                              </span>
                            ) : compliancePack ? (
                              <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-100 ring-1 ring-amber-300/30">
                                Disclosure pending
                              </span>
                            ) : (
                              <span className="rounded-full bg-white/[0.04] px-3 py-1 text-xs font-semibold text-slate-300 ring-1 ring-white/10">
                                Disclosure status pending
                              </span>
                            )
                          ) : null}
                        </div>
                        <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-300">
                          {system.description}
                        </p>
                        <div className="mt-4 flex flex-wrap items-center gap-3">
                          {system.risk_class === "HIGH_RISK" ? (
                            <button
                              type="button"
                              onClick={() => {
                                void runDocumentationForSystem({
                                  auditId: audit.audit_id,
                                  aiSystemId: system.id,
                                  systemName: system.name,
                                  systemDescription: system.description,
                                  riskClass: system.risk_class,
                                  primaryArticle: system.primary_article,
                                  sourceFiles: system.source_files,
                                  detectionSignals: system.detection_signals,
                                  repoUrl: audit.repo_url,
                                });
                              }}
                              disabled={isDocumentationLoading}
                              className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              {isDocumentationLoading ? (
                                <>
                                  <LoaderCircle className="h-4 w-4 animate-spin" />
                                  Generating Annex IV...
                                </>
                              ) : (
                                "Generate Annex IV PDF"
                              )}
                            </button>
                          ) : (
                            <span className="rounded-full border border-emerald-300/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-100">
                              Annex IV not required
                            </span>
                          )}

                          {artifact ? (
                            <a
                              href={artifact.download_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sm font-semibold text-sky-100 underline decoration-sky-300/50 underline-offset-4"
                            >
                              Download Annex IV PDF
                            </a>
                          ) : null}

                          {documentationResponse?.mode ? (
                            <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-300">
                              {documentationResponse.mode} mode
                            </span>
                          ) : null}
                        </div>
                        {documentationResponse?.message ? (
                          <p className="mt-3 text-sm leading-6 text-slate-400">
                            {documentationResponse.message}
                          </p>
                        ) : null}
                        {documentationError ? (
                          <div className="mt-3 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                            {documentationError}
                          </div>
                        ) : null}
                      </div>
                      <div className="grid gap-3 rounded-[22px] border border-white/10 bg-white/[0.03] p-4 text-sm xl:min-w-[250px]">
                        <div className="flex items-center justify-between gap-4">
                          <span className="text-slate-400">Confidence</span>
                          <span className="font-semibold text-slate-100">
                            {Math.round(system.confidence * 100)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                          <span className="text-slate-400">Primary article</span>
                          <span className="text-right text-slate-100">{system.primary_article}</span>
                        </div>
                        <div className="flex items-start justify-between gap-4">
                          <span className="text-slate-400">Deadline</span>
                          <span className="max-w-[160px] text-right text-slate-100">
                            {system.deadline}
                          </span>
                        </div>
                        <div className="flex items-start justify-between gap-4">
                          <span className="text-slate-400">Disclosure</span>
                          <span className="max-w-[160px] text-right text-slate-100">
                            {system.triggers_article_50
                              ? disclosure?.requires_disclosure
                                ? disclosure.article ?? "Required"
                                : compliancePack
                                  ? "Pending rollout"
                                  : "Awaiting pack"
                              : "Not required"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 grid gap-4 lg:grid-cols-[0.78fr_1.22fr]">
                      <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
                        <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">
                          <Eye className="h-4 w-4 text-sky-200" />
                          Evidence Trail
                        </div>
                        <div className="mt-4 flex flex-wrap gap-2">
                          {system.detection_signals.map((signal) => (
                            <span
                              key={signal}
                              className="rounded-full border border-sky-400/20 bg-sky-500/10 px-3 py-1 text-xs leading-5 text-sky-100"
                            >
                              {signal}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
                        <div className="grid gap-4 md:grid-cols-2">
                          <div>
                            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">
                              Source Files
                            </p>
                            <div className="mt-3 flex flex-wrap gap-2">
                              {system.source_files.map((sourceFile) => (
                                <span
                                  key={sourceFile}
                                  className="rounded-full border border-white/10 bg-slate-950/45 px-3 py-1 text-xs font-mono text-slate-200"
                                >
                                  {sourceFile}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">
                              Secondary Articles
                            </p>
                            <div className="mt-3 flex flex-wrap gap-2">
                              {system.secondary_articles.length > 0 ? (
                                system.secondary_articles.map((article) => (
                                  <span
                                    key={article}
                                    className="rounded-full border border-white/10 bg-slate-950/45 px-3 py-1 text-xs text-slate-200"
                                  >
                                    {article}
                                  </span>
                                ))
                              ) : (
                                <span className="text-sm text-slate-400">None</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="mt-5 rounded-[22px] border border-white/10 bg-slate-950/40 p-4">
                          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">
                            Classification Reasoning
                          </p>
                          <p className="mt-3 text-sm leading-7 text-slate-300">
                            {system.reasoning}
                          </p>
                        </div>
                      </div>
                    </div>
                  </article>
                  );
                })}
              </div>
            ) : null}
          </article>
        </section>

        <section className="panel-shell">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-200">
                Compliance Pack
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-50">
                Disclosure coverage, gap matrix, and compliance score
              </h2>
            </div>
            <p className="max-w-2xl text-sm leading-7 text-slate-400">
              Generate the D4B pack after the audit to compute a deterministic compliance score,
              estimate scenario-based fine exposure, and produce Article 50 notices when the
              systems inventory requires them.
            </p>
          </div>

          {!audit ? (
            <div className="mt-6 rounded-[28px] border border-dashed border-white/10 bg-white/[0.03] p-6 text-sm leading-7 text-slate-400">
              Run an audit first, then generate the compliance pack to surface disclosure status,
              severity-ranked gaps, and remediation priorities.
            </div>
          ) : null}

          {audit && isCompliancePackRunning ? (
            <div className="mt-6 grid gap-4 fade-rise lg:grid-cols-[0.74fr_1.26fr]">
              <div className="rounded-[28px] border border-sky-400/20 bg-slate-950/55 p-6">
                <div className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.18em] text-sky-100">
                  <span className="live-dot h-2.5 w-2.5 rounded-full bg-sky-300" />
                  Compliance Pack running
                </div>
                <p className="mt-4 text-4xl font-semibold tracking-tight text-slate-50">
                  Disclosure + Gap Auditor
                </p>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  Generating multilingual notices, checking Annex IV coverage, and computing the
                  deterministic compliance score.
                </p>
                <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/8">
                  <div className="progress-shell h-full rounded-full" style={{ width: "82%" }} />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {["Compliance score", "Estimated exposure", "Gap matrix", "Priority actions"].map(
                  (placeholder) => (
                    <div
                      key={placeholder}
                      className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5"
                    >
                      <div className="h-4 w-40 rounded-full bg-white/8" />
                      <div className="mt-4 h-12 w-24 rounded-full bg-sky-500/10" />
                      <div className="mt-5 grid gap-2">
                        <div className="h-4 w-full rounded-full bg-white/8" />
                        <div className="h-4 w-10/12 rounded-full bg-white/8" />
                        <div className="h-4 w-8/12 rounded-full bg-white/8" />
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          ) : null}

          {audit && compliancePackError ? (
            <div className="mt-6 rounded-[28px] border border-rose-400/30 bg-rose-500/10 p-5 text-sm leading-7 text-rose-100 fade-rise">
              {compliancePackError}
            </div>
          ) : null}

          {audit && !compliancePack && !isCompliancePackRunning && !compliancePackError ? (
            <div className="mt-6 rounded-[28px] border border-white/10 bg-white/[0.03] p-6 text-sm leading-7 text-slate-300">
              <p className="font-semibold text-slate-50">No compliance pack generated yet</p>
              <p className="mt-2">
                Use the action above to generate Article 50 notices where needed, score the audit,
                and persist a gap snapshot into Postgres.
              </p>
            </div>
          ) : null}

          {audit && compliancePack ? (
            <div className="mt-6 grid gap-6 fade-rise">
              <div className="grid gap-4 xl:grid-cols-4">
                <article className="relative overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/50 p-6">
                  <div className="absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.18),_transparent_60%)]" />
                  <div className="relative">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                      Compliance Score
                    </p>
                    <div className="mt-3 flex items-end gap-4">
                      <span
                        className={`text-6xl font-semibold tracking-tight ${complianceScoreTone(compliancePack.compliance_score)}`}
                      >
                        {compliancePack.compliance_score}
                      </span>
                      <span className="pb-2 text-lg text-slate-400">/ 100</span>
                    </div>
                    <p className="mt-3 text-sm font-medium text-slate-300">
                      {complianceScoreBand(compliancePack.compliance_score)}
                    </p>
                  </div>
                </article>

                <article className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                    Estimated Fine Exposure
                  </p>
                  <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-50">
                    {formatEuros(compliancePack.estimated_fine_exposure_eur)}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-400">
                    Scenario-based heuristic for demo purposes only, not legal advice.
                  </p>
                </article>

                <article className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                    Time-to-Compliant
                  </p>
                  <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-50">
                    {compliancePack.time_to_compliant_days}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-400">
                    Days until the earliest relevant compliance deadline in the current pack.
                  </p>
                </article>

                <article className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                    Coverage snapshot
                  </p>
                  <div className="mt-4 grid gap-3 text-sm text-slate-300">
                    <div className="flex items-center justify-between gap-4">
                      <span>Systems</span>
                      <span className="font-semibold text-slate-100">
                        {compliancePack.systems_count}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span>High-risk</span>
                      <span className="font-semibold text-slate-100">
                        {compliancePack.high_risk_count}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span>Article 50</span>
                      <span className="font-semibold text-slate-100">
                        {compliancePack.article_50_count}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span>Open gaps</span>
                      <span className="font-semibold text-slate-100">
                        {compliancePack.gaps.length}
                      </span>
                    </div>
                  </div>
                </article>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Compliance summary
                </p>
                <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-300">
                  {compliancePack.summary}
                </p>
              </div>

              <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <div className="grid gap-6">
                  <article className="rounded-[28px] border border-white/10 bg-slate-950/45 p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-sky-200">
                          Gap Matrix
                        </p>
                        <h3 className="mt-2 text-xl font-semibold text-slate-50">
                          Severity-ranked remediation backlog
                        </h3>
                      </div>
                      <Scale className="h-5 w-5 text-sky-200" />
                    </div>

                    <div className="mt-5 grid gap-3 md:grid-cols-4">
                      {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as GapSeverity[]).map((severity) => (
                        <div
                          key={severity}
                          className={`rounded-[22px] px-4 py-4 text-sm ${gapSeverityTone[severity]}`}
                        >
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em]">
                            {severity}
                          </p>
                          <p className="mt-3 text-3xl font-semibold tracking-tight">
                            {complianceGapCounts[severity]}
                          </p>
                        </div>
                      ))}
                    </div>

                    <div className="mt-5 grid gap-3">
                      {compliancePack.gaps.length > 0 ? (
                        compliancePack.gaps.map((gap, index) => (
                          <article
                            key={`${gap.title}-${index}`}
                            className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4"
                          >
                            <div className="flex flex-wrap items-center gap-3">
                              <span
                                className={`rounded-full px-3 py-1 text-xs font-semibold ${gapSeverityTone[gap.severity]}`}
                              >
                                {gap.severity}
                              </span>
                              <h4 className="text-base font-semibold text-slate-50">{gap.title}</h4>
                            </div>
                            <p className="mt-3 text-sm leading-7 text-slate-300">
                              {gap.description}
                            </p>
                            <div className="mt-4 grid gap-3 md:grid-cols-2">
                              <div className="rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-300">
                                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                                  Recommended action
                                </p>
                                <p className="mt-2 leading-6">{gap.recommended_action}</p>
                              </div>
                              <div className="rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-300">
                                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                                  Legal reference
                                </p>
                                <p className="mt-2 leading-6">{gap.legal_reference}</p>
                              </div>
                            </div>
                          </article>
                        ))
                      ) : (
                        <div className="rounded-[22px] border border-emerald-300/20 bg-emerald-500/10 p-4 text-sm leading-7 text-emerald-100">
                          No open gaps were generated for this compliance pack snapshot.
                        </div>
                      )}
                    </div>
                  </article>
                </div>

                <div className="grid gap-6">
                  <article className="rounded-[28px] border border-white/10 bg-slate-950/45 p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-sky-200">
                          Priority Actions
                        </p>
                        <h3 className="mt-2 text-xl font-semibold text-slate-50">
                          First remediation moves
                        </h3>
                      </div>
                      <Sparkles className="h-5 w-5 text-sky-200" />
                    </div>
                    <div className="mt-5 grid gap-3">
                      {compliancePack.priority_actions.length > 0 ? (
                        compliancePack.priority_actions.map((action) => (
                          <div
                            key={action}
                            className="rounded-[22px] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm leading-7 text-slate-300"
                          >
                            {action}
                          </div>
                        ))
                      ) : (
                        <div className="rounded-[22px] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm leading-7 text-slate-400">
                          Priority actions will appear here after the compliance pack is generated.
                        </div>
                      )}
                    </div>
                  </article>

                  <article className="rounded-[28px] border border-white/10 bg-slate-950/45 p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-sky-200">
                          Article 50 Notices
                        </p>
                        <h3 className="mt-2 text-xl font-semibold text-slate-50">
                          Multilingual deployer-ready disclosures
                        </h3>
                      </div>
                      <Eye className="h-5 w-5 text-sky-200" />
                    </div>

                    {compliancePack.disclosures.length === 0 ? (
                      <div className="mt-5 rounded-[22px] border border-white/10 bg-white/[0.03] p-4 text-sm leading-7 text-slate-300">
                        {compliancePack.article_50_count === 0
                          ? "No Article 50 disclosures were required for this audit."
                          : "Disclosure-ready systems were detected, but no notices were returned in this pack."}
                      </div>
                    ) : (
                      <div className="mt-5 grid gap-4">
                        {compliancePack.disclosures.map((disclosure) => (
                          <article
                            key={disclosure.ai_system_id}
                            className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4"
                          >
                            <div className="flex flex-wrap items-center gap-3">
                              <span className="rounded-full bg-sky-500/15 px-3 py-1 text-xs font-semibold text-sky-100 ring-1 ring-sky-400/30">
                                {disclosure.article ?? "Article 50"}
                              </span>
                              <span className="rounded-full border border-white/10 bg-slate-950/45 px-3 py-1 text-xs font-mono text-slate-300">
                                {disclosure.ai_system_id}
                              </span>
                            </div>
                            <div className="mt-4 grid gap-3 md:grid-cols-2">
                              {disclosure.notices ? (
                                ([
                                  ["EN", disclosure.notices.en],
                                  ["IT", disclosure.notices.it],
                                  ["ES", disclosure.notices.es],
                                  ["FR", disclosure.notices.fr],
                                  ["DE", disclosure.notices.de],
                                ] as const).map(([language, notice]) => (
                                  <div
                                    key={`${disclosure.ai_system_id}-${language}`}
                                    className="rounded-2xl border border-white/10 bg-slate-950/45 p-4"
                                  >
                                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                                      {language}
                                    </p>
                                    <p className="mt-3 text-sm leading-7 text-slate-300">
                                      {notice}
                                    </p>
                                  </div>
                                ))
                              ) : (
                                <div className="rounded-2xl border border-white/10 bg-slate-950/45 p-4 text-sm leading-7 text-slate-400 md:col-span-2">
                                  No notice body is available for this disclosure.
                                </div>
                              )}
                            </div>
                            {disclosure.placement_recommendations.length > 0 ? (
                              <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/45 p-4">
                                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                                  Placement recommendations
                                </p>
                                <div className="mt-3 grid gap-2">
                                  {disclosure.placement_recommendations.map((recommendation) => (
                                    <p
                                      key={recommendation}
                                      className="text-sm leading-7 text-slate-300"
                                    >
                                      {recommendation}
                                    </p>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                          </article>
                        ))}
                      </div>
                    )}
                  </article>
                </div>
              </div>
            </div>
          ) : null}
        </section>

        <section className="panel-shell">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-200">
                What&apos;s Next
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-50">
                The console already frames the full six-agent product
              </h2>
            </div>
            <p className="max-w-2xl text-sm leading-7 text-slate-400">
              D4B keeps the main audit path synchronous, then layers Annex IV artifacts,
              multilingual Article 50 notices, and a deterministic compliance score on top. The
              Monitor agent remains visible as the final loop that lands later.
            </p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              {
                title: "Documentation live",
                icon: FileSearch,
                body: "Annex IV structured output and PDF generation are now available directly from every high-risk system card.",
              },
              {
                title: "Disclosure live",
                icon: Eye,
                body: "Article 50 notice generation now adds multilingual deployer-facing notices and placement guidance.",
              },
              {
                title: "Gap Auditor live",
                icon: Scale,
                body: "Compliance packs now compute score, exposure, severity-ranked gaps, and priority actions.",
              },
              {
                title: "Monitor soon",
                icon: BellRing,
                body: "Deadline alerts and post-audit monitoring will complete the operating loop.",
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <article
                  key={item.title}
                  className="rounded-[26px] border border-white/10 bg-slate-950/40 p-5 transition hover:border-sky-400/25 hover:bg-slate-950/55"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-sky-500/10">
                      <Icon className="h-5 w-5 text-sky-100" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-50">{item.title}</h3>
                  </div>
                  <p className="mt-4 text-sm leading-7 text-slate-300">{item.body}</p>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </main>
  );
}

