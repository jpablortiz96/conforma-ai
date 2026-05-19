import type {
  ArtifactSummary,
  AuditArtifactsResponse,
  AuditRequest,
  AuditResponse,
  AuditStreamEvent,
  ClassifierRequest,
  ClassifierResponse,
  CompliancePackResponse,
  DisclosureResponse,
  DocumentationRequest,
  DocumentationResponse,
  EvidenceVaultAgentRun,
  EvidenceVaultGap,
  EvidenceVaultResponse,
  EvidenceVaultSystem,
  ExecutiveSummaryResponse,
  HealthResponse,
  MonitorAlert,
  MonitorResponse,
  OrchestratedAuditCompletedResponse,
  OrchestratedAuditStartResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEFAULT_TIMEOUT_MS = 15000;
const AUDIT_TIMEOUT_MS = 30000;
const DOCUMENTATION_TIMEOUT_MS = 180000;
const COMPLIANCE_PACK_TIMEOUT_MS = 180000;

export function normalizeAiActText(value: string): string {
  return value
    .replaceAll("ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§", "Section ")
    .replaceAll("Ãƒâ€šÃ‚Â§", "Section ")
    .replaceAll("Ã‚Â§", "Section ")
    .replaceAll("Â§", "Section ")
    .replaceAll("â‚¬", "€")
    .replaceAll("Ã¢â€šÂ¬", "€")
    .replaceAll("ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬", "€")
    .replaceAll("Ã¢â‚¬â„¢", "'")
    .replaceAll("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢", "'")
    .replaceAll("Ã¢â‚¬Å“", '"')
    .replaceAll("Ã¢â‚¬Â", '"')
    .replaceAll("Ã¢â‚¬â€œ", "-")
    .replaceAll("Ã¢â‚¬â€", "-");
}

function normalizeTextArray(values: string[]): string[] {
  return values.map((value) => normalizeAiActText(value));
}

function normalizeArtifactSummary(payload: ArtifactSummary): ArtifactSummary {
  return {
    ...payload,
    file_name: normalizeAiActText(payload.file_name),
    download_url: payload.download_url.startsWith("http")
      ? payload.download_url
      : `${API_BASE_URL}${payload.download_url}`,
  };
}

function normalizeDisclosureResponse(payload: DisclosureResponse): DisclosureResponse {
  return {
    ...payload,
    article: payload.article ? normalizeAiActText(payload.article) : null,
    notices: payload.notices
      ? {
          en: normalizeAiActText(payload.notices.en),
          it: normalizeAiActText(payload.notices.it),
          es: normalizeAiActText(payload.notices.es),
          fr: normalizeAiActText(payload.notices.fr),
          de: normalizeAiActText(payload.notices.de),
        }
      : null,
    placement_recommendations: normalizeTextArray(payload.placement_recommendations),
  };
}

function normalizeAuditSystem<T extends AuditResponse["systems"][number]>(
  system: T,
): T {
  return {
    ...system,
    primary_article: normalizeAiActText(system.primary_article),
    secondary_articles: normalizeTextArray(system.secondary_articles),
    reasoning: normalizeAiActText(system.reasoning),
    deadline: normalizeAiActText(system.deadline),
    detection_signals: normalizeTextArray(system.detection_signals),
  };
}

function normalizeMonitorAlert(payload: MonitorAlert): MonitorAlert {
  return {
    ...payload,
    title: normalizeAiActText(payload.title),
    description: normalizeAiActText(payload.description),
    recommended_action: normalizeAiActText(payload.recommended_action),
  };
}

export function normalizeMonitorResponse(payload: MonitorResponse): MonitorResponse {
  return {
    ...payload,
    summary: normalizeAiActText(payload.summary),
    alerts: payload.alerts.map(normalizeMonitorAlert),
  };
}

export function normalizeClassifierResponse(payload: ClassifierResponse): ClassifierResponse {
  return {
    ...payload,
    primary_article: normalizeAiActText(payload.primary_article),
    secondary_articles: normalizeTextArray(payload.secondary_articles),
    reasoning: normalizeAiActText(payload.reasoning),
    deadline: normalizeAiActText(payload.deadline),
  };
}

export function normalizeAuditResponse(payload: AuditResponse): AuditResponse {
  return {
    ...payload,
    summary: normalizeAiActText(payload.summary),
    systems: payload.systems.map((system) => normalizeAuditSystem(system)),
  };
}

export function normalizeDocumentationResponse(
  payload: DocumentationResponse,
): DocumentationResponse {
  return {
    ...payload,
    message: normalizeAiActText(payload.message),
    system_name: payload.system_name ? normalizeAiActText(payload.system_name) : null,
    section_1_general_description: payload.section_1_general_description
      ? normalizeAiActText(payload.section_1_general_description)
      : null,
    section_2_intended_purpose: payload.section_2_intended_purpose
      ? normalizeAiActText(payload.section_2_intended_purpose)
      : null,
    section_3_human_oversight_measures: payload.section_3_human_oversight_measures
      ? normalizeAiActText(payload.section_3_human_oversight_measures)
      : null,
    section_4_input_data_specs: payload.section_4_input_data_specs
      ? normalizeAiActText(payload.section_4_input_data_specs)
      : null,
    section_5_design_specifications: payload.section_5_design_specifications
      ? normalizeAiActText(payload.section_5_design_specifications)
      : null,
    section_6_risk_management_system: payload.section_6_risk_management_system
      ? normalizeAiActText(payload.section_6_risk_management_system)
      : null,
    section_7_validation_testing: payload.section_7_validation_testing
      ? normalizeAiActText(payload.section_7_validation_testing)
      : null,
    section_8_performance_metrics: payload.section_8_performance_metrics
      ? normalizeAiActText(payload.section_8_performance_metrics)
      : null,
    section_9_post_market_monitoring: payload.section_9_post_market_monitoring
      ? normalizeAiActText(payload.section_9_post_market_monitoring)
      : null,
    gaps_identified: normalizeTextArray(payload.gaps_identified),
    artifact: payload.artifact ? normalizeArtifactSummary(payload.artifact) : null,
  };
}

export function normalizeAuditArtifactsResponse(
  payload: AuditArtifactsResponse,
): AuditArtifactsResponse {
  return {
    ...payload,
    artifacts: payload.artifacts.map(normalizeArtifactSummary),
  };
}

export function normalizeCompliancePackResponse(
  payload: CompliancePackResponse,
): CompliancePackResponse {
  return {
    ...payload,
    summary: normalizeAiActText(payload.summary),
    disclosures: payload.disclosures.map(normalizeDisclosureResponse),
    priority_actions: normalizeTextArray(payload.priority_actions),
    gaps: payload.gaps.map((gap) => ({
      ...gap,
      title: normalizeAiActText(gap.title),
      description: normalizeAiActText(gap.description),
      recommended_action: normalizeAiActText(gap.recommended_action),
      legal_reference: normalizeAiActText(gap.legal_reference),
    })),
  };
}

export function normalizeExecutiveSummaryResponse(
  payload: ExecutiveSummaryResponse,
): ExecutiveSummaryResponse {
  return {
    ...payload,
    board_summary: normalizeAiActText(payload.board_summary),
    investor_style_one_liner: normalizeAiActText(payload.investor_style_one_liner),
    top_5_actions: normalizeTextArray(payload.top_5_actions),
    regulatory_timeline: payload.regulatory_timeline.map((entry) => ({
      ...entry,
      label: normalizeAiActText(entry.label),
      affected_systems: normalizeTextArray(entry.affected_systems),
    })),
  };
}

function normalizeEvidenceVaultGap(payload: EvidenceVaultGap): EvidenceVaultGap {
  return {
    ...payload,
    category: normalizeAiActText(payload.category),
    severity: normalizeAiActText(payload.severity),
    description: normalizeAiActText(payload.description),
    remediation: normalizeAiActText(payload.remediation),
  };
}

function normalizeEvidenceVaultAgentRun(
  payload: EvidenceVaultAgentRun,
): EvidenceVaultAgentRun {
  return {
    ...payload,
    agent_name: normalizeAiActText(payload.agent_name),
    status: normalizeAiActText(payload.status),
    model: payload.model ? normalizeAiActText(payload.model) : null,
    error: payload.error ? normalizeAiActText(payload.error) : null,
  };
}

function normalizeEvidenceVaultSystem(
  payload: EvidenceVaultSystem,
): EvidenceVaultSystem {
  return {
    ...payload,
    description: normalizeAiActText(payload.description),
    primary_article: payload.primary_article
      ? normalizeAiActText(payload.primary_article)
      : null,
    secondary_articles: normalizeTextArray(payload.secondary_articles),
    reasoning: payload.reasoning ? normalizeAiActText(payload.reasoning) : null,
    deadline: payload.deadline ? normalizeAiActText(payload.deadline) : null,
    detection_signals: normalizeTextArray(payload.detection_signals),
    artifacts: payload.artifacts.map(normalizeArtifactSummary),
    disclosures: payload.disclosures.map(normalizeDisclosureResponse),
    gaps: payload.gaps.map(normalizeEvidenceVaultGap),
    agent_runs: payload.agent_runs.map(normalizeEvidenceVaultAgentRun),
  };
}

export function normalizeEvidenceVaultResponse(
  payload: EvidenceVaultResponse,
): EvidenceVaultResponse {
  return {
    ...payload,
    summary: normalizeAiActText(payload.summary),
    systems: payload.systems.map(normalizeEvidenceVaultSystem),
    audit_level_runs: payload.audit_level_runs.map(normalizeEvidenceVaultAgentRun),
    monitor_alerts: payload.monitor_alerts.map(normalizeMonitorAlert),
  };
}

export function normalizeAuditStreamEvent(payload: AuditStreamEvent): AuditStreamEvent {
  return {
    ...payload,
    message: normalizeAiActText(payload.message),
  };
}

export function normalizeOrchestratedAuditCompletedResponse(
  payload: OrchestratedAuditCompletedResponse,
): OrchestratedAuditCompletedResponse {
  return {
    ...payload,
    summary: normalizeAiActText(payload.summary),
    systems: payload.systems.map((system) => normalizeAuditSystem(system)),
    compliance_pack: normalizeCompliancePackResponse(payload.compliance_pack),
    monitor: normalizeMonitorResponse(payload.monitor),
    executive_summary: normalizeExecutiveSummaryResponse(payload.executive_summary),
    evidence_vault: normalizeEvidenceVaultResponse(payload.evidence_vault),
  };
}

async function fetchWithTimeout(
  input: string,
  init: RequestInit,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        `The backend did not respond in time. Check that ${API_BASE_URL} is running and reachable.`,
      );
    }

    if (error instanceof Error) {
      throw new Error(`Unable to reach the backend at ${API_BASE_URL}. ${error.message}`);
    }

    throw new Error(`Unable to reach the backend at ${API_BASE_URL}.`);
  } finally {
    clearTimeout(timeout);
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string | string[] }
      | null;
    const detail = payload?.detail;
    if (Array.isArray(detail)) {
      throw new Error(detail.join(", "));
    }
    throw new Error(
      typeof detail === "string"
        ? normalizeAiActText(detail)
        : `Request failed with status ${response.status}.`,
    );
  }

  return (await response.json()) as T;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export function getAuditStreamUrl(streamUrl: string): string {
  return streamUrl.startsWith("http") ? streamUrl : `${API_BASE_URL}${streamUrl}`;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/`,
    {
      method: "GET",
      cache: "no-store",
    },
    DEFAULT_TIMEOUT_MS,
  );

  return parseResponse<HealthResponse>(response);
}

export async function classifySystem(
  payload: ClassifierRequest,
): Promise<ClassifierResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/agents/classifier`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    DEFAULT_TIMEOUT_MS,
  );

  return normalizeClassifierResponse(await parseResponse<ClassifierResponse>(response));
}

export async function runAudit(payload: AuditRequest): Promise<AuditResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/audits`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    AUDIT_TIMEOUT_MS,
  );

  return normalizeAuditResponse(await parseResponse<AuditResponse>(response));
}

export async function startOrchestratedAudit(
  payload: AuditRequest,
): Promise<OrchestratedAuditStartResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/audits/orchestrated`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    AUDIT_TIMEOUT_MS,
  );

  return parseResponse<OrchestratedAuditStartResponse>(response);
}

export async function generateDocumentation(
  payload: DocumentationRequest,
): Promise<DocumentationResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/agents/documentation`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    DOCUMENTATION_TIMEOUT_MS,
  );

  return normalizeDocumentationResponse(await parseResponse<DocumentationResponse>(response));
}

export async function generateCompliancePack(
  auditId: string,
): Promise<CompliancePackResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/audits/${auditId}/compliance-pack`,
    {
      method: "POST",
      cache: "no-store",
    },
    COMPLIANCE_PACK_TIMEOUT_MS,
  );

  return normalizeCompliancePackResponse(await parseResponse<CompliancePackResponse>(response));
}

export async function getExecutiveSummary(
  auditId: string,
): Promise<ExecutiveSummaryResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/audits/${auditId}/executive-summary`,
    {
      method: "GET",
      cache: "no-store",
    },
    DEFAULT_TIMEOUT_MS,
  );

  return normalizeExecutiveSummaryResponse(
    await parseResponse<ExecutiveSummaryResponse>(response),
  );
}

export async function getEvidenceVault(
  auditId: string,
): Promise<EvidenceVaultResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/audits/${auditId}/evidence-vault`,
    {
      method: "GET",
      cache: "no-store",
    },
    DEFAULT_TIMEOUT_MS,
  );

  return normalizeEvidenceVaultResponse(await parseResponse<EvidenceVaultResponse>(response));
}

export async function listAuditArtifacts(
  auditId: string,
): Promise<AuditArtifactsResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/audits/${auditId}/artifacts`,
    {
      method: "GET",
      cache: "no-store",
    },
    DEFAULT_TIMEOUT_MS,
  );

  return normalizeAuditArtifactsResponse(await parseResponse<AuditArtifactsResponse>(response));
}
