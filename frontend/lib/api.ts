import type {
  ArtifactSummary,
  AuditArtifactsResponse,
  AuditRequest,
  AuditResponse,
  ClassifierRequest,
  ClassifierResponse,
  DemoHighRiskSystemResponse,
  DocumentationRequest,
  DocumentationResponse,
  HealthResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEFAULT_TIMEOUT_MS = 15000;
const AUDIT_TIMEOUT_MS = 240000;
const DOCUMENTATION_TIMEOUT_MS = 180000;

function normalizeAiActText(value: string): string {
  return value
    .replaceAll("Ãƒâ€šÃ‚Â§", "Section ")
    .replaceAll("Ã‚Â§", "Section ")
    .replaceAll("Â§", "Section ")
    .replaceAll("§", "Section ");
}

function normalizeClassifierResponse(payload: ClassifierResponse): ClassifierResponse {
  return {
    ...payload,
    primary_article: normalizeAiActText(payload.primary_article),
    secondary_articles: payload.secondary_articles.map(normalizeAiActText),
    reasoning: normalizeAiActText(payload.reasoning),
    deadline: normalizeAiActText(payload.deadline),
  };
}

function normalizeAuditResponse(payload: AuditResponse): AuditResponse {
  return {
    ...payload,
    summary: normalizeAiActText(payload.summary),
    systems: payload.systems.map((system) => ({
      ...system,
      primary_article: normalizeAiActText(system.primary_article),
      secondary_articles: system.secondary_articles.map(normalizeAiActText),
      reasoning: normalizeAiActText(system.reasoning),
      deadline: normalizeAiActText(system.deadline),
      detection_signals: system.detection_signals.map(normalizeAiActText),
    })),
  };
}

function normalizeArtifactSummary(payload: ArtifactSummary): ArtifactSummary {
  return {
    ...payload,
    download_url: payload.download_url.startsWith("http")
      ? payload.download_url
      : `${API_BASE_URL}${payload.download_url}`,
  };
}

function normalizeDocumentationResponse(payload: DocumentationResponse): DocumentationResponse {
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
    gaps_identified: payload.gaps_identified.map(normalizeAiActText),
    artifact: payload.artifact ? normalizeArtifactSummary(payload.artifact) : null,
  };
}

function normalizeAuditArtifactsResponse(payload: AuditArtifactsResponse): AuditArtifactsResponse {
  return {
    ...payload,
    artifacts: payload.artifacts.map(normalizeArtifactSummary),
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
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
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

export async function classifySystem(payload: ClassifierRequest): Promise<ClassifierResponse> {
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

export async function createDemoHighRiskSystem(): Promise<DemoHighRiskSystemResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/demo/high-risk-system`,
    {
      method: "POST",
      cache: "no-store",
    },
    DEFAULT_TIMEOUT_MS,
  );

  return parseResponse<DemoHighRiskSystemResponse>(response);
}

export async function listAuditArtifacts(auditId: string): Promise<AuditArtifactsResponse> {
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
