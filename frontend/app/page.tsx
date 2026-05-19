"use client";

import { startTransition, useDeferredValue, useEffect, useRef, useState, useTransition } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Eye,
  FileBadge2,
  FileDown,
  FileSearch2,
  FolderKanban,
  GanttChartSquare,
  GitBranch,
  Languages,
  LoaderCircle,
  Radar,
  ScanSearch,
  ShieldAlert,
  ShieldCheck,
  Siren,
  Sparkles,
} from "lucide-react";

import {
  generateCompliancePack,
  generateDocumentation,
  getApiBaseUrl,
  getAuditStreamUrl,
  getEvidenceVault,
  getExecutiveSummary,
  getHealth,
  listAuditArtifacts,
  normalizeAiActText,
  normalizeAuditStreamEvent,
  normalizeOrchestratedAuditCompletedResponse,
  startOrchestratedAudit,
} from "@/lib/api";
import type {
  AgentKey,
  AgentPipelineItem,
  AgentPipelineState,
  ArtifactSummary,
  AuditArtifactsResponse,
  AuditStreamEvent,
  AuditStreamEventName,
  ComplianceGap,
  CompliancePackResponse,
  DisclosureResponse,
  DocumentationRequest,
  EvidenceVaultResponse,
  EvidenceVaultSystem,
  ExecutiveSummaryResponse,
  HealthResponse,
  MonitorAlert,
  MonitorResponse,
  OrchestratedAuditCompletedResponse,
  ReadinessLevel,
  RiskClass,
  SampleRepo,
} from "@/lib/types";

const SAMPLE_REPOS: SampleRepo[] = [
  {
    label: "Resume Screening",
    repoUrl: "https://github.com/anukalp-mishra/Resume-Screening",
    maxFiles: 80,
    note: "Recruitment AI · Annex III Section 4(a)",
  },
  {
    label: "karpathy/llm.c",
    repoUrl: "https://github.com/karpathy/llm.c",
    maxFiles: 50,
    note: "Generative AI · Article 50(2)",
  },
  {
    label: "rasahq/rasa",
    repoUrl: "https://github.com/rasahq/rasa",
    maxFiles: 100,
    note: "Conversational AI inventory",
  },
];

const PIPELINE_BLUEPRINT: Array<{
  key: AgentKey;
  name: string;
  model: string;
  blurb: string;
  branch: "core" | "parallel" | "post";
}> = [
  {
    key: "scanner",
    name: "Scanner",
    model: "Gemini + heuristics",
    blurb: "Clones the repo, extracts evidence, and inventories candidate AI systems.",
    branch: "core",
  },
  {
    key: "classifier",
    name: "Classifier",
    model: "Gemini Pro + legal guardrails",
    blurb: "Maps each system to Annex III, Article 50, Article 5, or minimal risk.",
    branch: "core",
  },
  {
    key: "documentation",
    name: "Documentation",
    model: "Gemini Pro + Annex IV PDF",
    blurb: "Builds Annex IV technical documentation when high-risk obligations apply.",
    branch: "parallel",
  },
  {
    key: "disclosure",
    name: "Disclosure",
    model: "Gemini Flash + Article 50",
    blurb: "Generates multilingual transparency notices for user-facing or synthetic AI.",
    branch: "parallel",
  },
  {
    key: "gap_auditor",
    name: "Gap Auditor",
    model: "Deterministic scoring engine",
    blurb: "Calculates compliance score, fine exposure, and remediation priorities.",
    branch: "post",
  },
  {
    key: "monitor",
    name: "Monitor",
    model: "Deadline intelligence",
    blurb: "Tracks obligations, missing controls, and regulatory timing after the audit.",
    branch: "post",
  },
];

const PROGRESS_BY_EVENT: Record<AuditStreamEventName, number> = {
  audit_started: 4,
  scanner_started: 12,
  scanner_completed: 24,
  classifier_started: 36,
  classifier_completed: 50,
  documentation_started: 58,
  documentation_completed: 68,
  disclosure_started: 74,
  disclosure_completed: 82,
  gap_auditor_started: 88,
  gap_auditor_completed: 93,
  monitor_started: 96,
  monitor_completed: 99,
  audit_completed: 100,
  audit_failed: 100,
};

const LANGUAGE_LABELS: Array<{ key: keyof NonNullable<DisclosureResponse["notices"]>; label: string }> = [
  { key: "en", label: "English" },
  { key: "it", label: "Italiano" },
  { key: "es", label: "Español" },
  { key: "fr", label: "Français" },
  { key: "de", label: "Deutsch" },
];

function formatEuros(value: number | null | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "€0";
  }

  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDateLabel(value: string | null | undefined): string {
  if (!value) {
    return "No mandatory deadline";
  }

  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [year, month, day] = value.split("-").map((part) => Number(part));
    const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return `${String(day).padStart(2, "0")} ${monthLabels[Math.max(0, month - 1)]} ${year}`;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return normalizeAiActText(value);
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(parsed);
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Pending";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return normalizeAiActText(value);
  }

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function riskTone(risk: RiskClass): string {
  switch (risk) {
    case "UNACCEPTABLE":
      return "border-rose-400/40 bg-rose-500/12 text-rose-100";
    case "HIGH_RISK":
      return "border-amber-400/40 bg-amber-500/12 text-amber-100";
    case "LIMITED_RISK":
      return "border-sky-400/40 bg-sky-500/12 text-sky-100";
    case "MINIMAL_RISK":
    default:
      return "border-emerald-400/35 bg-emerald-500/12 text-emerald-100";
  }
}

function gapTone(severity: ComplianceGap["severity"]): string {
  switch (severity) {
    case "CRITICAL":
      return "border-rose-400/40 bg-rose-500/10 text-rose-100";
    case "HIGH":
      return "border-orange-400/40 bg-orange-500/10 text-orange-100";
    case "MEDIUM":
      return "border-amber-400/35 bg-amber-500/10 text-amber-100";
    case "LOW":
    default:
      return "border-sky-400/35 bg-sky-500/10 text-sky-100";
  }
}

function monitorTone(severity: MonitorAlert["severity"]): string {
  switch (severity) {
    case "CRITICAL":
      return "border-rose-400/40 bg-rose-500/12 text-rose-100";
    case "WARNING":
      return "border-amber-400/40 bg-amber-500/12 text-amber-100";
    case "INFO":
    default:
      return "border-sky-400/35 bg-sky-500/12 text-sky-100";
  }
}

function readinessTone(level: ReadinessLevel): string {
  switch (level) {
    case "ENTERPRISE_READY":
      return "border-emerald-400/40 bg-emerald-500/12 text-emerald-100";
    case "HIGH":
      return "border-sky-400/40 bg-sky-500/12 text-sky-100";
    case "MEDIUM":
      return "border-amber-400/40 bg-amber-500/12 text-amber-100";
    case "LOW":
    default:
      return "border-rose-400/40 bg-rose-500/12 text-rose-100";
  }
}

function agentStateTone(state: AgentPipelineState): string {
  switch (state) {
    case "complete":
      return "border-emerald-400/30 bg-emerald-500/10";
    case "active":
      return "agent-card-live border-sky-400/40 bg-sky-500/10";
    case "failed":
      return "border-rose-400/35 bg-rose-500/10";
    case "queued":
      return "border-fuchsia-400/25 bg-fuchsia-500/8";
    case "idle":
    default:
      return "border-white/10 bg-white/[0.03]";
  }
}

function computePipeline(events: AuditStreamEvent[], isRunning: boolean): AgentPipelineItem[] {
  const lastByEvent: Partial<Record<AuditStreamEventName, AuditStreamEvent>> = {};
  for (const event of events) {
    const eventName = event.payload.event as AuditStreamEventName | undefined;
    if (eventName) {
      lastByEvent[eventName] = event;
    }
  }

  return PIPELINE_BLUEPRINT.map((item) => {
    const started = lastByEvent[`${item.key}_started` as AuditStreamEventName];
    const completed = lastByEvent[`${item.key}_completed` as AuditStreamEventName];
    const failed = events.find(
      (event) => event.status === "failed" && event.agent === item.key,
    );

    let state: AgentPipelineState = "idle";
    if (failed) {
      state = "failed";
    } else if (completed) {
      state = "complete";
    } else if (started) {
      state = "active";
    } else if (isRunning) {
      state = item.branch === "parallel" || item.branch === "post" ? "queued" : "idle";
    }

    let cue = item.blurb;
    if (completed?.payload && typeof completed.payload === "object") {
      if (item.key === "documentation") {
        const count = Number(completed.payload.generated_count ?? 0);
        cue = count > 0 ? `${count} Annex IV artifact${count === 1 ? "" : "s"} ready.` : "No high-risk systems required Annex IV output in this run.";
      } else if (item.key === "disclosure") {
        const count = Number(completed.payload.generated_count ?? 0);
        cue = count > 0 ? `${count} multilingual disclosure pack${count === 1 ? "" : "s"} ready.` : "No Article 50 disclosures were required in this run.";
      } else if (item.key === "gap_auditor") {
        cue = `Compliance score ${completed.payload.compliance_score ?? "available"} with ${completed.payload.gaps_count ?? 0} tracked gaps.`;
      } else if (item.key === "monitor") {
        cue = `${completed.payload.alerts_count ?? 0} monitoring alert${completed.payload.alerts_count === 1 ? "" : "s"} published.`;
      }
    }

    return {
      key: item.key,
      name: item.name,
      model: item.model,
      blurb: item.blurb,
      state,
      cue,
      branch: item.branch,
    };
  });
}

function countGapsBySeverity(gaps: ComplianceGap[]): Record<ComplianceGap["severity"], number> {
  return gaps.reduce(
    (accumulator, gap) => {
      accumulator[gap.severity] += 1;
      return accumulator;
    },
    { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 },
  );
}

function formatArtifactLabel(artifact: ArtifactSummary): string {
  if (artifact.kind === "annex_iv_pdf") {
    return "Annex IV PDF";
  }

  if (artifact.kind === "article_50_notice_json") {
    return "Article 50 notice JSON";
  }

  return artifact.file_name;
}

function ArtifactChip({ artifact }: { artifact: ArtifactSummary }) {
  const downloadable = artifact.kind === "annex_iv_pdf";
  const tone =
    artifact.kind === "annex_iv_pdf"
      ? "border-sky-400/35 bg-sky-500/12 text-sky-100"
      : "border-violet-400/30 bg-violet-500/12 text-violet-100";

  return (
    <div className={`rounded-2xl border px-4 py-3 ${tone}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold">{formatArtifactLabel(artifact)}</p>
          <p className="mt-1 text-xs uppercase tracking-[0.24em] text-white/55">{artifact.kind.replaceAll("_", " ")}</p>
          <p className="mt-2 text-xs text-white/45">{artifact.file_name}</p>
        </div>
        {downloadable ? (
          <a
            href={artifact.download_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded-full border border-white/15 px-3 py-1 text-xs font-semibold text-white transition hover:border-sky-300/45 hover:text-sky-100"
          >
            Download
            <FileDown className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </div>
    </div>
  );
}

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState(SAMPLE_REPOS[0].repoUrl);
  const [maxFilesToInspect, setMaxFilesToInspect] = useState(SAMPLE_REPOS[0].maxFiles);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [isAuditRunning, setIsAuditRunning] = useState(false);
  const [activeAuditId, setActiveAuditId] = useState<string | null>(null);
  const [events, setEvents] = useState<AuditStreamEvent[]>([]);
  const [orchestratedResult, setOrchestratedResult] = useState<OrchestratedAuditCompletedResponse | null>(null);
  const [compliancePack, setCompliancePack] = useState<CompliancePackResponse | null>(null);
  const [executiveSummary, setExecutiveSummary] = useState<ExecutiveSummaryResponse | null>(null);
  const [evidenceVault, setEvidenceVault] = useState<EvidenceVaultResponse | null>(null);
  const [artifacts, setArtifacts] = useState<AuditArtifactsResponse | null>(null);
  const [documentationBusySystemId, setDocumentationBusySystemId] = useState<string | null>(null);
  const [documentationMessage, setDocumentationMessage] = useState<string | null>(null);
  const [documentationError, setDocumentationError] = useState<string | null>(null);
  const [complianceBusy, setComplianceBusy] = useState(false);
  const [complianceError, setComplianceError] = useState<string | null>(null);
  const [isPending, startViewTransition] = useTransition();

  const deferredEvents = useDeferredValue(events);
  const eventSourceRef = useRef<EventSource | null>(null);
  const resultsRef = useRef<HTMLElement | null>(null);
  const streamCompletedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function checkHealth() {
      try {
        const response = await getHealth();
        if (!cancelled) {
          setHealth(response);
          setHealthError(null);
        }
      } catch (error) {
        if (!cancelled) {
          setHealthError(error instanceof Error ? error.message : "Backend health probe failed.");
        }
      }
    }

    void checkHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!orchestratedResult) {
      return;
    }

    resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [orchestratedResult]);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  async function refreshAuditViews(auditId: string) {
    const [pack, executive, evidence, listedArtifacts] = await Promise.all([
      generateCompliancePack(auditId),
      getExecutiveSummary(auditId),
      getEvidenceVault(auditId),
      listAuditArtifacts(auditId),
    ]);

    startViewTransition(() => {
      setCompliancePack(pack);
      setExecutiveSummary(executive);
      setEvidenceVault(evidence);
      setArtifacts(listedArtifacts);
    });
  }

  async function handleRunOrchestratedAudit() {
    eventSourceRef.current?.close();
    streamCompletedRef.current = false;

    setAuditError(null);
    setComplianceError(null);
    setDocumentationError(null);
    setDocumentationMessage(null);
    setOrchestratedResult(null);
    setCompliancePack(null);
    setExecutiveSummary(null);
    setEvidenceVault(null);
    setArtifacts(null);
    setEvents([]);
    setActiveAuditId(null);
    setIsAuditRunning(true);

    try {
      const startResponse = await startOrchestratedAudit({
        repo_url: repoUrl.trim(),
        max_files_to_inspect: maxFilesToInspect,
      });
      setActiveAuditId(startResponse.audit_id);

      const stream = new EventSource(getAuditStreamUrl(startResponse.stream_url));
      eventSourceRef.current = stream;

      const handledEvents = new Set<AuditStreamEventName>([
        "audit_started",
        "scanner_started",
        "scanner_completed",
        "classifier_started",
        "classifier_completed",
        "documentation_started",
        "documentation_completed",
        "disclosure_started",
        "disclosure_completed",
        "gap_auditor_started",
        "gap_auditor_completed",
        "monitor_started",
        "monitor_completed",
        "audit_completed",
        "audit_failed",
      ]);

      const bind = (eventName: AuditStreamEventName) => {
        stream.addEventListener(eventName, async (incoming) => {
          const messageEvent = incoming as MessageEvent<string>;
          const parsed = normalizeAuditStreamEvent(JSON.parse(messageEvent.data) as AuditStreamEvent);

          setEvents((current) => [...current, parsed]);

          if (eventName === "audit_completed") {
            streamCompletedRef.current = true;
            stream.close();
            const normalizedResult = normalizeOrchestratedAuditCompletedResponse(
              parsed.payload.result as OrchestratedAuditCompletedResponse,
            );
            const listedArtifacts = await listAuditArtifacts(parsed.audit_id);

            startViewTransition(() => {
              setOrchestratedResult(normalizedResult);
              setCompliancePack(normalizedResult.compliance_pack);
              setExecutiveSummary(normalizedResult.executive_summary);
              setEvidenceVault(normalizedResult.evidence_vault);
              setArtifacts(listedArtifacts);
              setAuditError(null);
            });
            setIsAuditRunning(false);
          }

          if (eventName === "audit_failed") {
            streamCompletedRef.current = true;
            stream.close();
            setIsAuditRunning(false);
            setAuditError(parsed.message);
          }
        });
      };

      handledEvents.forEach((eventName) => bind(eventName));

      stream.onerror = () => {
        if (!streamCompletedRef.current) {
          setAuditError(
            "The live audit stream disconnected before the orchestrated run finished. Check the backend logs and retry.",
          );
          setIsAuditRunning(false);
        }
        stream.close();
      };
    } catch (error) {
      setAuditError(error instanceof Error ? error.message : "Unable to start the orchestrated audit.");
      setIsAuditRunning(false);
    }
  }

  async function handleGenerateAnnexIv(systemId: string) {
    if (!activeAuditId) {
      return;
    }

    const system = orchestratedResult?.systems.find((item) => item.id === systemId);
    if (!system) {
      return;
    }

    setDocumentationBusySystemId(systemId);
    setDocumentationError(null);
    setDocumentationMessage(null);

    try {
      const payload: DocumentationRequest = {
        audit_id: activeAuditId,
        ai_system_id: system.id,
        system_description: system.description,
        risk_class: system.risk_class,
        primary_article: system.primary_article,
        source_code_snippets: [
          ...system.source_files.map((file) => `Referenced source file: ${file}`),
          ...system.detection_signals.map((signal) => `Evidence trail: ${signal}`),
        ].slice(0, 12),
        repo_metadata: {
          repo_url: repoUrl,
          source_files: system.source_files,
          detection_signals: system.detection_signals,
          system_name: system.name,
        },
      };
      const response = await generateDocumentation(payload);
      setDocumentationMessage(response.message);
      await refreshAuditViews(activeAuditId);
    } catch (error) {
      setDocumentationError(
        error instanceof Error ? error.message : "Unable to generate the Annex IV artifact.",
      );
    } finally {
      setDocumentationBusySystemId(null);
    }
  }

  async function handleGenerateCompliancePack() {
    if (!activeAuditId) {
      return;
    }

    setComplianceBusy(true);
    setComplianceError(null);

    try {
      await refreshAuditViews(activeAuditId);
    } catch (error) {
      setComplianceError(
        error instanceof Error ? error.message : "Unable to refresh the compliance pack.",
      );
    } finally {
      setComplianceBusy(false);
    }
  }

  const latestEvent = events[events.length - 1] ?? null;
  const liveProgress = latestEvent ? PROGRESS_BY_EVENT[latestEvent.payload.event as AuditStreamEventName] ?? 0 : 0;
  const pipeline = computePipeline(events, isAuditRunning);
  const gapCounts = countGapsBySeverity(compliancePack?.gaps ?? []);
  const visibleEvents = deferredEvents.slice(-10).reverse();
  const systems = orchestratedResult?.systems ?? [];

  function getEvidenceSystem(systemId: string): EvidenceVaultSystem | undefined {
    return evidenceVault?.systems.find((system) => system.id === systemId);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-[1520px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
      <section className="panel-shell fade-rise overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-300/70 to-transparent" />
        <div className="grid gap-8 xl:grid-cols-[1.35fr_0.95fr]">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-sky-300/20 bg-sky-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-sky-100">
              <Sparkles className="h-3.5 w-3.5" />
              D5 Winner Mode
            </div>
            <div className="space-y-4">
              <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                Conforma-AI
                <span className="block text-2xl font-medium text-sky-100/90 sm:text-3xl">
                  Autonomous EU AI Act control room for real repositories.
                </span>
              </h1>
              <p className="max-w-3xl text-base leading-8 text-slate-200/80 sm:text-lg">
                Scanner, Classifier, Documentation, Disclosure, Gap Auditor, and Monitor now work as one
                orchestrated compliance officer. Stream the audit live, inspect the legal evidence trail,
                and hand your board a readiness narrative with deadlines, fine exposure, and concrete actions.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-white/45">Live backend</p>
                <p className="mt-3 flex items-center gap-2 text-lg font-semibold text-white">
                  <span className={`h-2.5 w-2.5 rounded-full ${health ? "live-dot bg-emerald-300" : "bg-rose-300"}`} />
                  {health ? `${health.service} ${health.version}` : "Connectivity degraded"}
                </p>
                <p className="mt-2 text-sm text-slate-300/75">
                  {healthError ? healthError : `Streaming from ${getApiBaseUrl()} with synchronous fallback endpoints preserved.`}
                </p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-white/45">Realtime transport</p>
                <p className="mt-3 flex items-center gap-2 text-lg font-semibold text-white">
                  <Radar className="h-5 w-5 text-sky-200" />
                  SSE pipeline
                </p>
                <p className="mt-2 text-sm text-slate-300/75">
                  Honest agent events from audit start to executive summary, without removing the legacy sync path.
                </p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-white/45">Legal surface</p>
                <p className="mt-3 flex items-center gap-2 text-lg font-semibold text-white">
                  <ShieldCheck className="h-5 w-5 text-emerald-200" />
                  Annex III + Article 50
                </p>
                <p className="mt-2 text-sm text-slate-300/75">
                  Annex IV PDFs, multilingual disclosures, compliance score, deadline intelligence, and evidence vault.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[30px] border border-white/10 bg-slate-950/45 p-5 shadow-[0_24px_80px_rgba(2,10,24,0.45)] backdrop-blur">
            <div className="flex items-center gap-3 text-white">
              <GitBranch className="h-5 w-5 text-sky-200" />
              <div>
                <p className="text-lg font-semibold">Launch an orchestrated audit</p>
                <p className="text-sm text-slate-300/75">Pick a public repo, stream the six-agent chain, then review the control stack.</p>
              </div>
            </div>
            <div className="mt-5 space-y-4">
              <label className="block">
                <span className="text-xs font-semibold uppercase tracking-[0.26em] text-white/45">Repository URL</span>
                <input
                  value={repoUrl}
                  onChange={(event) => setRepoUrl(event.currentTarget.value)}
                  placeholder="https://github.com/org/repo"
                  className="mt-2 w-full rounded-2xl border border-white/10 bg-black/25 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-300/40 focus:ring-2 focus:ring-sky-400/20"
                />
              </label>
              <label className="block">
                <span className="text-xs font-semibold uppercase tracking-[0.26em] text-white/45">Max files to inspect</span>
                <input
                  type="number"
                  min={20}
                  max={400}
                  value={maxFilesToInspect}
                  onChange={(event) => setMaxFilesToInspect(event.currentTarget.valueAsNumber || 50)}
                  className="mt-2 w-full rounded-2xl border border-white/10 bg-black/25 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-300/40 focus:ring-2 focus:ring-sky-400/20"
                />
              </label>

              <div className="grid gap-2">
                <p className="text-xs font-semibold uppercase tracking-[0.26em] text-white/45">Sample public repos</p>
                <div className="grid gap-2 sm:grid-cols-3">
                  {SAMPLE_REPOS.map((sample) => (
                    <button
                      key={sample.repoUrl}
                      type="button"
                      onClick={() => {
                        setRepoUrl(sample.repoUrl);
                        setMaxFilesToInspect(sample.maxFiles);
                      }}
                      className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-3 text-left transition hover:border-sky-300/30 hover:bg-sky-400/10"
                    >
                      <p className="text-sm font-semibold text-white">{sample.label}</p>
                      <p className="mt-1 text-xs text-slate-300/70">{sample.note}</p>
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={() => void handleRunOrchestratedAudit()}
                disabled={isAuditRunning || !repoUrl.trim()}
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(120deg,#2563eb_0%,#0ea5e9_55%,#38bdf8_100%)] px-5 py-3 text-sm font-semibold text-white shadow-[0_14px_40px_rgba(37,99,235,0.35)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isAuditRunning ? <LoaderCircle className="h-4.5 w-4.5 animate-spin" /> : <ScanSearch className="h-4.5 w-4.5" />}
                {isAuditRunning ? "Running orchestrated audit..." : "Run Orchestrated Audit"}
              </button>
              <p className="text-xs leading-6 text-slate-300/65">
                The orchestrator streams Scanner, Classifier, Documentation, Disclosure, Gap Auditor, and Monitor in one pass. Legacy synchronous endpoints remain available as fallback for demo resilience.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="panel-shell fade-rise">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Agent pipeline</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Realtime orchestration</h2>
              <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-300/75">
                Scanner and Classifier drive the core inventory. Documentation and Disclosure branch off when the legal triggers apply. Gap Auditor and Monitor close the loop with operational guidance.
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-slate-200/80">
              <p className="text-xs uppercase tracking-[0.24em] text-white/45">Live stage</p>
              <p className="mt-2 font-semibold text-white">{latestEvent?.message ?? "Waiting for the next orchestrated audit."}</p>
            </div>
          </div>

          <div className="mt-6">
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.24em] text-white/50">
              <span>Pipeline progress</span>
              <span>{liveProgress}%</span>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full border border-white/10 bg-white/5">
              <div
                className={`progress-shell h-full rounded-full transition-[width] duration-700 ${isAuditRunning ? "cockpit-pulse" : ""}`}
                style={{ width: `${Math.max(liveProgress, orchestratedResult ? 100 : 0)}%` }}
              />
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {pipeline.map((agent) => (
              <article
                key={agent.key}
                className={`rounded-[28px] border p-5 transition ${agentStateTone(agent.state)}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="inline-flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${agent.state === "active" ? "live-dot bg-sky-300" : agent.state === "complete" ? "bg-emerald-300" : agent.state === "failed" ? "bg-rose-300" : agent.state === "queued" ? "bg-fuchsia-300" : "bg-white/25"}`} />
                    <p className="text-sm font-semibold text-white">{agent.name}</p>
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/55">
                    {agent.branch}
                  </span>
                </div>
                <p className="mt-3 text-xs uppercase tracking-[0.24em] text-sky-100/65">{agent.model}</p>
                <p className="mt-3 text-sm leading-7 text-slate-200/75">{agent.cue}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="panel-shell fade-rise">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-sky-200" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Event stream</p>
              <h2 className="mt-1 text-2xl font-semibold text-white">Agent activity log</h2>
            </div>
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-300/75">
            Real SSE events from the backend. No fake completions. If the stream fails, the console keeps the last known trace for inspection.
          </p>

          <div className="mt-5 space-y-3">
            {visibleEvents.length ? (
              visibleEvents.map((event) => (
                <div key={`${event.timestamp}-${event.agent}-${event.status}`} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`h-2.5 w-2.5 rounded-full ${event.status === "completed" ? "bg-emerald-300" : event.status === "failed" ? "bg-rose-300" : "live-dot bg-sky-300"}`} />
                      <p className="text-sm font-semibold text-white">{event.agent}</p>
                    </div>
                    <span className="text-[11px] uppercase tracking-[0.24em] text-white/45">{formatDateTime(event.timestamp)}</span>
                  </div>
                  <p className="mt-2 text-sm leading-7 text-slate-200/80">{event.message}</p>
                </div>
              ))
            ) : (
              <div className="rounded-[28px] border border-dashed border-white/15 bg-black/20 p-6 text-sm leading-7 text-slate-300/72">
                Launch an orchestrated audit to watch the six-agent trace in real time. This panel will list every honest SSE event, from repo cloning through executive summary publication.
              </div>
            )}
          </div>

          {(auditError || complianceError || documentationError) ? (
            <div className="mt-5 rounded-[26px] border border-rose-400/30 bg-rose-500/10 p-4 text-sm leading-7 text-rose-50">
              <div className="flex items-center gap-2 font-semibold">
                <AlertTriangle className="h-4.5 w-4.5" />
                Control-room exception
              </div>
              <p className="mt-2">{auditError ?? complianceError ?? documentationError}</p>
            </div>
          ) : null}

          {documentationMessage ? (
            <div className="mt-5 rounded-[26px] border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm leading-7 text-emerald-50">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="h-4.5 w-4.5" />
                Artifact update
              </div>
              <p className="mt-2">{documentationMessage}</p>
            </div>
          ) : null}
        </div>
      </section>

      <section ref={resultsRef} className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="panel-shell fade-rise">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Control metrics</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Board-facing snapshot</h2>
            </div>
            <button
              type="button"
              onClick={() => void handleGenerateCompliancePack()}
              disabled={!activeAuditId || complianceBusy || isAuditRunning}
              className="inline-flex items-center gap-2 rounded-2xl border border-sky-300/25 bg-sky-500/12 px-4 py-2 text-sm font-semibold text-sky-100 transition hover:border-sky-200/45 hover:bg-sky-500/18 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {complianceBusy ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ShieldAlert className="h-4 w-4" />}
              {complianceBusy ? "Refreshing compliance pack..." : "Generate Compliance Pack"}
            </button>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-white/45">Audit ID</p>
              <p className="mt-3 break-all text-sm font-semibold text-white">{activeAuditId ?? "Pending audit launch"}</p>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-white/45">Portfolio Risk Index</p>
              <p className="mt-3 text-4xl font-semibold text-white">{orchestratedResult?.portfolio_risk_index ?? "--"}</p>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-white/45">Compliance Score</p>
              <p className="mt-3 text-4xl font-semibold text-white">{compliancePack?.compliance_score ?? "--"}</p>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-white/45">Estimated Fine Exposure</p>
              <p className="mt-3 text-3xl font-semibold text-white">{formatEuros(compliancePack?.estimated_fine_exposure_eur)}</p>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-white/45">Time to Compliant</p>
              <p className="mt-3 text-3xl font-semibold text-white">
                {compliancePack ? `${compliancePack.time_to_compliant_days} days` : "--"}
              </p>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-white/45">Readiness Level</p>
              <div className={`mt-3 inline-flex rounded-full border px-3 py-1 text-sm font-semibold ${readinessTone(executiveSummary?.readiness_level ?? "LOW")}`}>
                {executiveSummary?.readiness_level ?? "Pending"}
              </div>
            </div>
          </div>
        </div>

        <div className="panel-shell fade-rise">
          <div className="flex items-center gap-3">
            <Siren className="h-5 w-5 text-sky-200" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Executive Summary</p>
              <h2 className="mt-1 text-2xl font-semibold text-white">Board-ready narrative</h2>
            </div>
          </div>
          {executiveSummary ? (
            <div className="mt-5 space-y-5">
              <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
                <p className="text-sm leading-8 text-slate-100/90">{executiveSummary.board_summary}</p>
              </div>
              <div className="rounded-[28px] border border-sky-300/20 bg-sky-500/8 p-5">
                <p className="text-xs uppercase tracking-[0.24em] text-sky-100/60">Investor-style one-liner</p>
                <p className="mt-2 text-lg font-semibold text-white">{executiveSummary.investor_style_one_liner}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-white/45">Top 5 actions</p>
                <div className="mt-3 space-y-3">
                  {executiveSummary.top_5_actions.map((action, index) => (
                    <div key={`${index + 1}-${action}`} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm leading-7 text-slate-200/80">
                      <span className="mr-2 text-sky-200">{String(index + 1).padStart(2, "0")}</span>
                      {action}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-5 rounded-[28px] border border-dashed border-white/15 bg-black/20 p-6 text-sm leading-7 text-slate-300/72">
              Launch an orchestrated audit to generate a board summary, a regulatory timeline, and an investor-style readiness signal.
            </div>
          )}
        </div>
      </section>

      <section className="panel-shell fade-rise">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">AI Systems Inventory</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Defensible system-by-system legal mapping</h2>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-slate-300/75">
            {systems.length ? `${systems.length} system${systems.length === 1 ? "" : "s"} in the current audit.` : "No systems yet."}
          </div>
        </div>

        {systems.length ? (
          <div className="mt-6 grid gap-5 xl:grid-cols-2">
            {systems.map((system) => {
              const evidenceSystem = getEvidenceSystem(system.id);
              const annexIvArtifact = evidenceSystem?.artifacts.find((artifact) => artifact.kind === "annex_iv_pdf");
              const disclosure = evidenceSystem?.disclosures[0] ?? compliancePack?.disclosures.find((item) => item.ai_system_id === system.id);
              const systemGaps = evidenceSystem?.gaps ?? [];

              return (
                <article key={system.id} className="rounded-[30px] border border-white/10 bg-black/20 p-5 shadow-[0_18px_60px_rgba(2,8,18,0.28)]">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-xl font-semibold text-white">{system.name}</h3>
                        <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] ${riskTone(system.risk_class)}`}>
                          {system.risk_class.replaceAll("_", " ")}
                        </span>
                      </div>
                      <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300/78">{system.description}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-right">
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Confidence</p>
                      <p className="mt-2 text-2xl font-semibold text-white">{Math.round(system.confidence * 100)}%</p>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Primary article</p>
                      <p className="mt-2 text-sm font-semibold text-white">{system.primary_article}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Deadline</p>
                      <p className="mt-2 text-sm font-semibold text-white">{formatDateLabel(system.deadline_iso ?? system.deadline)}</p>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-4 lg:grid-cols-2">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/45">Source files</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {system.source_files.map((file) => (
                          <span key={file} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-slate-200/75">
                            {file}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/45">Evidence trail</p>
                      <div className="mt-3 space-y-2">
                        {system.detection_signals.map((signal) => (
                          <div key={signal} className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm leading-7 text-slate-200/80">
                            {signal}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_auto]">
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Disclosure status</p>
                      <p className="mt-2 text-sm font-semibold text-white">
                        {system.triggers_article_50
                          ? disclosure?.requires_disclosure
                            ? `Article 50 notice ready · ${disclosure.article}`
                            : "Disclosure required but not yet generated."
                          : "Article 50 disclosure not required."}
                      </p>
                    </div>
                    <div className="flex flex-col items-stretch gap-2">
                      {system.risk_class === "HIGH_RISK" ? (
                        annexIvArtifact ? (
                          <a
                            href={annexIvArtifact.download_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center justify-center gap-2 rounded-2xl border border-sky-300/30 bg-sky-500/12 px-4 py-3 text-sm font-semibold text-sky-100 transition hover:border-sky-200/45 hover:bg-sky-500/18"
                          >
                            <FileDown className="h-4 w-4" />
                            Download Annex IV PDF
                          </a>
                        ) : (
                          <button
                            type="button"
                            onClick={() => void handleGenerateAnnexIv(system.id)}
                            disabled={documentationBusySystemId === system.id}
                            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(120deg,#1d4ed8_0%,#0284c7_55%,#0ea5e9_100%)] px-4 py-3 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(14,165,233,0.24)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            {documentationBusySystemId === system.id ? (
                              <LoaderCircle className="h-4 w-4 animate-spin" />
                            ) : (
                              <FileBadge2 className="h-4 w-4" />
                            )}
                            {documentationBusySystemId === system.id ? "Generating Annex IV..." : "Generate Annex IV PDF"}
                          </button>
                        )
                      ) : (
                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-center text-sm font-semibold text-slate-200/70">
                          Annex IV not required
                        </div>
                      )}
                    </div>
                  </div>

                  <details className="mt-5 rounded-[26px] border border-white/10 bg-white/[0.03] p-4">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold text-white">
                      <span className="inline-flex items-center gap-2">
                        <Eye className="h-4 w-4 text-sky-200" />
                        Why this classification?
                      </span>
                      <ChevronRight className="h-4 w-4 text-white/55" />
                    </summary>
                    <div className="mt-4 space-y-4 text-sm leading-7 text-slate-200/80">
                      <p>{system.reasoning}</p>
                      {system.secondary_articles.length ? (
                        <div>
                          <p className="text-xs uppercase tracking-[0.24em] text-white/45">Secondary references</p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {system.secondary_articles.map((reference) => (
                              <span key={reference} className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-200/75">
                                {reference}
                              </span>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  </details>

                  {systemGaps.length ? (
                    <div className="mt-5">
                      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/45">System gaps</p>
                      <div className="mt-3 space-y-2">
                        {systemGaps.map((gap) => (
                          <div key={`${gap.category}-${gap.description}`} className={`rounded-2xl border px-3 py-3 text-sm leading-7 ${gapTone(gap.severity as ComplianceGap["severity"])}`}>
                            <p className="font-semibold">{gap.category}</p>
                            <p className="mt-1 text-slate-100/80">{gap.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="mt-6 rounded-[30px] border border-dashed border-white/15 bg-black/20 p-8 text-sm leading-7 text-slate-300/72">
            Once an orchestrated audit completes, this inventory will show each detected AI system with source files, evidence trail, legal mapping, and artifact status.
          </div>
        )}
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <div className="panel-shell fade-rise">
          <div className="flex items-center gap-3">
            <GanttChartSquare className="h-5 w-5 text-sky-200" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Compliance Pack</p>
              <h2 className="mt-1 text-2xl font-semibold text-white">Score, gaps, and remediation matrix</h2>
            </div>
          </div>

          {compliancePack ? (
            <div className="mt-5 space-y-5">
              <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
                <p className="text-sm leading-8 text-slate-100/85">{compliancePack.summary}</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((severity) => (
                  <div key={severity} className={`rounded-2xl border p-4 ${gapTone(severity)}`}>
                    <p className="text-xs uppercase tracking-[0.24em]">{severity}</p>
                    <p className="mt-3 text-3xl font-semibold">{gapCounts[severity]}</p>
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                {compliancePack.gaps.map((gap, index) => (
                  <article key={`${gap.title}-${index}`} className={`rounded-[26px] border p-4 ${gapTone(gap.severity)}`}>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm font-semibold">{gap.title}</p>
                      <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em]">
                        {gap.severity}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-7 text-slate-100/82">{gap.description}</p>
                    <p className="mt-3 text-xs uppercase tracking-[0.22em] text-white/50">{gap.legal_reference}</p>
                    <p className="mt-2 text-sm leading-7 text-slate-100/78">{gap.recommended_action}</p>
                  </article>
                ))}
              </div>

              <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
                <p className="text-xs uppercase tracking-[0.24em] text-white/45">Priority actions</p>
                <div className="mt-3 space-y-2">
                  {compliancePack.priority_actions.map((action) => (
                    <div key={action} className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-3 text-sm leading-7 text-slate-100/82">
                      <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-sky-200" />
                      <span>{action}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-5 rounded-[28px] border border-dashed border-white/15 bg-black/20 p-6 text-sm leading-7 text-slate-300/72">
              The compliance pack appears here after the orchestrated audit, or you can refresh it manually for the active audit.
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="panel-shell fade-rise">
            <div className="flex items-center gap-3">
              <Languages className="h-5 w-5 text-sky-200" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Article 50 notices</p>
                <h2 className="mt-1 text-2xl font-semibold text-white">Multilingual disclosure vault</h2>
              </div>
            </div>
            {compliancePack?.disclosures.length ? (
              <div className="mt-5 space-y-4">
                {compliancePack.disclosures.map((disclosure) => {
                  const targetSystem = systems.find((system) => system.id === disclosure.ai_system_id);
                  return (
                    <article key={disclosure.ai_system_id} className="rounded-[28px] border border-white/10 bg-black/20 p-5">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-white">{targetSystem?.name ?? disclosure.ai_system_id}</p>
                          <p className="mt-1 text-xs uppercase tracking-[0.24em] text-sky-100/60">{disclosure.article}</p>
                        </div>
                        <div className="rounded-full border border-emerald-300/30 bg-emerald-500/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-100">
                          Ready
                        </div>
                      </div>
                      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                        {LANGUAGE_LABELS.map((language) => (
                          <div key={language.key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                            <p className="text-[11px] uppercase tracking-[0.24em] text-white/45">{language.label}</p>
                            <p className="mt-2 text-sm leading-7 text-slate-100/82">
                              {disclosure.notices ? disclosure.notices[language.key] : "Not generated"}
                            </p>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 space-y-2">
                        {disclosure.placement_recommendations.map((placement) => (
                          <div key={placement} className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm leading-7 text-slate-100/78">
                            {placement}
                          </div>
                        ))}
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <div className="mt-5 rounded-[28px] border border-dashed border-white/15 bg-black/20 p-6 text-sm leading-7 text-slate-300/72">
                No Article 50 systems require disclosure in the current audit. When a generative or user-facing system is detected, the multilingual notices appear here in English, Italian, Spanish, French, and German.
              </div>
            )}
          </div>

          <div className="panel-shell fade-rise">
            <div className="flex items-center gap-3">
              <Clock3 className="h-5 w-5 text-sky-200" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Regulatory timeline</p>
                <h2 className="mt-1 text-2xl font-semibold text-white">Board-facing deadlines</h2>
              </div>
            </div>
            {executiveSummary?.regulatory_timeline.length ? (
              <div className="mt-5 space-y-4">
                {executiveSummary.regulatory_timeline.map((entry) => (
                  <div key={`${entry.date}-${entry.label}`} className="rounded-[28px] border border-white/10 bg-black/20 p-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.24em] text-white/45">{formatDateLabel(entry.date)}</p>
                        <p className="mt-2 text-lg font-semibold text-white">{entry.label}</p>
                      </div>
                      <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-slate-200/70">
                        {entry.affected_systems.length} system{entry.affected_systems.length === 1 ? "" : "s"}
                      </div>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {entry.affected_systems.map((systemName) => (
                        <span key={systemName} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-200/75">
                          {systemName}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-5 rounded-[28px] border border-dashed border-white/15 bg-black/20 p-6 text-sm leading-7 text-slate-300/72">
                The regulatory timeline will highlight Article 50 and Annex III milestones after the orchestrated audit completes.
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="panel-shell fade-rise">
          <div className="flex items-center gap-3">
            <Radar className="h-5 w-5 text-sky-200" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Monitor Agent</p>
              <h2 className="mt-1 text-2xl font-semibold text-white">Deadline and control intelligence</h2>
            </div>
          </div>

          {orchestratedResult?.monitor.alerts.length ? (
            <div className="mt-5 space-y-3">
              {orchestratedResult.monitor.alerts.map((alert, index) => (
                <article key={`${alert.type}-${index}-${alert.title}`} className={`rounded-[26px] border p-4 ${monitorTone(alert.severity)}`}>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm font-semibold">{alert.title}</p>
                    <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em]">
                      {alert.severity}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-7 text-slate-100/82">{alert.description}</p>
                  <p className="mt-3 text-xs uppercase tracking-[0.22em] text-white/50">{alert.type}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-100/78">{alert.recommended_action}</p>
                  {alert.deadline_iso ? (
                    <p className="mt-3 text-xs uppercase tracking-[0.22em] text-white/55">Deadline {formatDateLabel(alert.deadline_iso)}</p>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <div className="mt-5 rounded-[28px] border border-dashed border-white/15 bg-black/20 p-6 text-sm leading-7 text-slate-300/72">
              The Monitor Agent will publish deadline approach alerts, missing-control findings, and regulatory roadmap notes after the orchestrated audit completes.
            </div>
          )}
        </div>

        <div className="panel-shell fade-rise">
          <div className="flex items-center gap-3">
            <FolderKanban className="h-5 w-5 text-sky-200" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Evidence Vault</p>
              <h2 className="mt-1 text-2xl font-semibold text-white">Traceable legal and technical evidence</h2>
            </div>
          </div>

          {evidenceVault ? (
            <div className="mt-5 space-y-5">
              {evidenceVault.systems.map((system) => (
                <article key={system.id} className="rounded-[30px] border border-white/10 bg-black/20 p-5">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <p className="text-lg font-semibold text-white">{system.name}</p>
                      <p className="mt-2 text-sm leading-7 text-slate-200/76">{system.description}</p>
                    </div>
                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] ${riskTone((system.risk_class as RiskClass | null) ?? "MINIMAL_RISK")}`}>
                      {system.risk_class?.replaceAll("_", " ") ?? "Pending"}
                    </span>
                  </div>

                  <div className="mt-5 grid gap-4 lg:grid-cols-2">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Legal mapping</p>
                      <div className="mt-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-7 text-slate-100/82">
                        <p><span className="font-semibold text-white">Primary:</span> {system.primary_article ?? "Not assigned"}</p>
                        <p className="mt-2"><span className="font-semibold text-white">Deadline:</span> {formatDateLabel(system.deadline_iso ?? system.deadline)}</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Generated artifacts</p>
                      <div className="mt-3 grid gap-3">
                        {system.artifacts.length ? (
                          system.artifacts.map((artifact) => <ArtifactChip key={artifact.artifact_id} artifact={artifact} />)
                        ) : (
                          <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.03] px-4 py-4 text-sm text-slate-300/72">
                            No artifacts recorded yet for this system.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-4 lg:grid-cols-2">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Source files</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {system.source_files.map((file) => (
                          <span key={file} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-200/75">
                            {file}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-white/45">Detection signals</p>
                      <div className="mt-3 space-y-2">
                        {system.detection_signals.map((signal) => (
                          <div key={signal} className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm leading-7 text-slate-100/80">
                            {signal}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <details className="mt-5 rounded-[26px] border border-white/10 bg-white/[0.03] p-4">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold text-white">
                      <span className="inline-flex items-center gap-2">
                        <BrainCircuit className="h-4 w-4 text-sky-200" />
                        Why this classification?
                      </span>
                      <ChevronRight className="h-4 w-4 text-white/55" />
                    </summary>
                    <div className="mt-4 space-y-4 text-sm leading-7 text-slate-100/82">
                      <p>{system.reasoning ?? "No reasoning stored."}</p>
                      {system.secondary_articles.length ? (
                        <div className="flex flex-wrap gap-2">
                          {system.secondary_articles.map((reference) => (
                            <span key={reference} className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-200/75">
                              {reference}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </details>

                  <div className="mt-5">
                    <p className="text-xs uppercase tracking-[0.24em] text-white/45">Agent run trace</p>
                    <div className="mt-3 space-y-2">
                      {system.agent_runs.map((run, index) => (
                        <div key={`${run.agent_name}-${run.started_at}-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <p className="text-sm font-semibold text-white">{run.agent_name}</p>
                            <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-200/70">
                              {run.status}
                            </span>
                          </div>
                          <p className="mt-2 text-xs uppercase tracking-[0.22em] text-white/45">
                            {run.model ? `${run.model} · ` : ""}
                            {formatDateTime(run.started_at)}
                          </p>
                          {run.error ? <p className="mt-2 text-sm text-rose-100/80">{run.error}</p> : null}
                        </div>
                      ))}
                    </div>
                  </div>
                </article>
              ))}

              {artifacts?.artifacts.length ? (
                <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
                  <p className="text-xs uppercase tracking-[0.24em] text-white/45">Audit-level artifacts</p>
                  <div className="mt-3 grid gap-3 lg:grid-cols-2">
                    {artifacts.artifacts.map((artifact) => (
                      <ArtifactChip key={artifact.artifact_id} artifact={artifact} />
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="mt-5 rounded-[28px] border border-dashed border-white/15 bg-black/20 p-6 text-sm leading-7 text-slate-300/72">
              The evidence vault assembles source files, detection signals, legal mapping, artifacts, gaps, disclosures, and agent traces into one defensible dossier.
            </div>
          )}
        </div>
      </section>

      <section className="panel-shell fade-rise">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/45">Control-room posture</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">What this demo now proves</h2>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-slate-300/72">
            D1 to D5 synchronous fallback kept intact.
          </div>
        </div>
        <div className="mt-6 grid gap-4 lg:grid-cols-4">
          {[
            {
              icon: ScanSearch,
              title: "Repo-native evidence",
              copy: "Scanner evidence survives through classification, documentation, disclosure, monitoring, and the vault.",
            },
            {
              icon: FileSearch2,
              title: "Legal traceability",
              copy: "Each system carries source files, detection signals, legal reasoning, and artifact links.",
            },
            {
              icon: Bot,
              title: "Autonomous handoffs",
              copy: "Six agents now coordinate under one orchestrator while streaming honest SSE progress.",
            },
            {
              icon: ShieldCheck,
              title: "Board-ready output",
              copy: "Compliance score, fine exposure, timeline, readiness, and action plan land in one console.",
            },
          ].map((item) => (
            <div key={item.title} className="rounded-[28px] border border-white/10 bg-black/20 p-5">
              <item.icon className="h-5 w-5 text-sky-200" />
              <p className="mt-4 text-lg font-semibold text-white">{item.title}</p>
              <p className="mt-3 text-sm leading-7 text-slate-200/76">{item.copy}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
