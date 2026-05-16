"use client";

import { AlertTriangle, ArrowRight, CheckCircle2, Shield, Sparkles } from "lucide-react";
import { useEffect, useState, useTransition } from "react";

import { classifySystem, getHealth } from "@/lib/api";
import type {
  AgentRoadmapItem,
  ClassifierResponse,
  HealthResponse,
  RiskClass
} from "@/lib/types";

const smokeCases = [
  "Bank CV ranking",
  "Password reset chatbot",
  "Real-time facial recognition shoplifter",
  "Email spam filter"
] as const;

const agentRoadmap: AgentRoadmapItem[] = [
  { name: "Scanner", model: "gemini-3-flash-preview", status: "D2", purpose: "Inventory AI systems across a repository." },
  { name: "Classifier", model: "gemini-3.1-pro-preview", status: "Live in D1", purpose: "Map each system to an EU AI Act risk class." },
  { name: "Documentation", model: "gemini-3.1-pro-preview", status: "D4", purpose: "Generate Annex IV documentation for high-risk systems." },
  { name: "Disclosure", model: "gemini-3-flash-preview", status: "D4", purpose: "Draft Article 50 transparency notices." },
  { name: "Gap Auditor", model: "gemini-3.1-pro-preview", status: "D4", purpose: "Compute score, gaps, and remediation priorities." },
  { name: "Monitor", model: "gemini-3-flash-preview", status: "D5", purpose: "Track deadline exposure and post-audit alerts." }
];

const riskTone: Record<RiskClass, string> = {
  UNACCEPTABLE: "bg-rose-500/15 text-rose-200 ring-1 ring-rose-400/30",
  HIGH_RISK: "bg-amber-500/15 text-amber-100 ring-1 ring-amber-300/30",
  LIMITED_RISK: "bg-sky-500/15 text-sky-100 ring-1 ring-sky-300/30",
  MINIMAL_RISK: "bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-300/30"
};

export default function HomePage() {
  const [description, setDescription] = useState<string>(smokeCases[0]);
  const [result, setResult] = useState<ClassifierResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    void (async () => {
      try {
        const payload = await getHealth();
        setHealth(payload);
        setBackendError(null);
      } catch (error) {
        setBackendError(error instanceof Error ? error.message : "Backend unavailable.");
      }
    })();
  }, []);

  const submit = () => {
    setRequestError(null);
    startTransition(() => {
      void (async () => {
        try {
          const payload = await classifySystem({ system_description: description });
          setResult(payload);
        } catch (error) {
          setRequestError(error instanceof Error ? error.message : "Classification failed.");
        }
      })();
    });
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(31,102,255,0.22),_transparent_42%),linear-gradient(180deg,_#071427_0%,_#091a32_52%,_#050d1a_100%)] text-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 py-8 lg:px-10">
        <header className="rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-panel backdrop-blur">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-100">
                <Shield className="h-3.5 w-3.5" />
                AI Agent Olympics · D1 Local Baseline
              </div>
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-conforma-white md:text-6xl">
                EU AI Act classification with a six-agent roadmap behind it.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300 md:text-lg">
                Conforma-AI is building an enterprise compliance operating system for the EU AI Act.
                D1 runs the Classifier agent locally, while the UI already frames the full six-agent
                workflow planned through D5.
              </p>
            </div>

            <div className="grid min-w-[280px] gap-3 rounded-3xl border border-white/10 bg-slate-950/35 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">Backend status</span>
                {health ? (
                  <span className="inline-flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-200">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {health.status}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-2 rounded-full bg-amber-500/15 px-3 py-1 text-xs font-medium text-amber-200">
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
                  <dd className="font-mono text-slate-100">localhost:8000</dd>
                </div>
              </dl>
            </div>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <article className="rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-panel backdrop-blur">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.18em] text-sky-200">Classifier Demo</p>
                <h2 className="mt-2 text-2xl font-semibold text-conforma-white">Run the D1 smoke path</h2>
              </div>
              <Sparkles className="h-6 w-6 text-sky-300" />
            </div>

            <label htmlFor="system-description" className="mt-6 block text-sm font-medium text-slate-200">
              AI system description
            </label>
            <textarea
              id="system-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={5}
              className="mt-3 w-full rounded-3xl border border-white/10 bg-slate-950/50 px-4 py-4 text-base text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-sky-400/60 focus:ring-2 focus:ring-sky-400/20"
              placeholder="Describe the AI system you want to classify."
            />

            <div className="mt-4 flex flex-wrap gap-2">
              {smokeCases.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setDescription(item)}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition hover:border-sky-300/50 hover:bg-sky-400/10 hover:text-white"
                >
                  {item}
                </button>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={submit}
                disabled={isPending}
                className="inline-flex items-center gap-2 rounded-full bg-conforma-blue px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isPending ? "Classifying..." : "Classify system"}
                <ArrowRight className="h-4 w-4" />
              </button>
              <p className="text-sm text-slate-400">
                Gemini is used when available. The UI surfaces deterministic fallback mode explicitly.
              </p>
            </div>

            {requestError ? (
              <div className="mt-5 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {requestError}
              </div>
            ) : null}

            {backendError ? (
              <div className="mt-5 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                Backend health check failed: {backendError}
              </div>
            ) : null}
          </article>

          <aside className="rounded-[28px] border border-white/10 bg-slate-950/40 p-6 shadow-panel backdrop-blur">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-sky-200">Current output</p>
            {!result ? (
              <div className="mt-5 rounded-3xl border border-dashed border-white/10 bg-white/[0.03] p-6 text-sm leading-7 text-slate-400">
                Submit one of the smoke cases or your own system description to inspect the D1 classifier response.
              </div>
            ) : (
              <div className="mt-5 grid gap-4">
                {result.mode === "fallback" ? (
                  <div className="rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                    Fallback mode is active. Gemini was unavailable or returned an invalid response, so Conforma-AI used the deterministic local classifier.
                  </div>
                ) : (
                  <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                    Gemini mode is active. The result was generated through the centralized Gemini client.
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <span className={`rounded-full px-3 py-1 text-sm font-semibold ${riskTone[result.risk_class]}`}>
                    {result.risk_class.replace("_", " ")}
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-xs text-slate-200">
                    confidence {Math.round(result.confidence * 100)}%
                  </span>
                </div>

                <dl className="grid gap-3 rounded-3xl border border-white/10 bg-white/[0.03] p-5 text-sm">
                  <div>
                    <dt className="text-slate-400">Primary article</dt>
                    <dd className="mt-1 font-medium text-slate-100">{result.primary_article}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Secondary articles</dt>
                    <dd className="mt-1 text-slate-100">
                      {result.secondary_articles.length > 0 ? result.secondary_articles.join(", ") : "None"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Deadline</dt>
                    <dd className="mt-1 text-slate-100">{result.deadline}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Deadline ISO</dt>
                    <dd className="mt-1 font-mono text-slate-100">{result.deadline_iso ?? "None"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Article 50 trigger</dt>
                    <dd className="mt-1 text-slate-100">{result.triggers_article_50 ? "Yes" : "No"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Reasoning</dt>
                    <dd className="mt-1 leading-7 text-slate-200">{result.reasoning}</dd>
                  </div>
                </dl>
              </div>
            )}
          </aside>
        </section>

        <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-panel backdrop-blur">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-sky-200">Six-agent vision</p>
              <h2 className="mt-2 text-2xl font-semibold text-conforma-white">The product direction stays multi-agent</h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-slate-400">
              D1 only runs the Classifier end-to-end, but the architecture and presentation stay aligned with the six-agent compliance workflow required by the handoff.
            </p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {agentRoadmap.map((agent) => (
              <article
                key={agent.name}
                className="rounded-3xl border border-white/10 bg-slate-950/35 p-5 transition hover:border-sky-400/30 hover:bg-slate-950/55"
              >
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-lg font-semibold text-conforma-white">{agent.name}</h3>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      agent.status === "Live in D1"
                        ? "bg-emerald-500/15 text-emerald-200"
                        : "bg-sky-500/15 text-sky-200"
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{agent.purpose}</p>
                <p className="mt-4 font-mono text-xs text-slate-400">{agent.model}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
