export type RiskClass =
  | "UNACCEPTABLE"
  | "HIGH_RISK"
  | "LIMITED_RISK"
  | "MINIMAL_RISK";

export type ResponseMode = "gemini" | "fallback";

export interface HealthResponse {
  status: "operational";
  service: string;
  version: string;
}

export interface ClassifierRequest {
  system_description: string;
  context_files?: string[];
}

export interface ClassifierResponse {
  risk_class: RiskClass;
  primary_article: string;
  secondary_articles: string[];
  reasoning: string;
  deadline: string;
  deadline_iso: string | null;
  confidence: number;
  triggers_article_50: boolean;
  mode: ResponseMode;
}

export interface AuditRequest {
  repo_url: string;
  max_files_to_inspect: number;
}

export interface AuditSystem {
  id: string;
  name: string;
  description: string;
  source_files: string[];
  detection_signals: string[];
  risk_class: RiskClass;
  primary_article: string;
  secondary_articles: string[];
  reasoning: string;
  deadline: string;
  deadline_iso: string | null;
  confidence: number;
  triggers_article_50: boolean;
}

export interface AuditResponse {
  audit_id: string;
  repo_url: string;
  status: "completed";
  systems: AuditSystem[];
  portfolio_risk_index: number;
  summary: string;
}

export interface ArtifactSummary {
  artifact_id: string;
  audit_id: string;
  ai_system_id: string | null;
  kind: string;
  language: string | null;
  file_name: string;
  download_url: string;
  created_at: string;
}

export interface AuditArtifactsResponse {
  audit_id: string;
  artifacts: ArtifactSummary[];
}

export interface DocumentationRequest {
  audit_id: string;
  ai_system_id: string;
  system_description: string;
  risk_class: RiskClass;
  primary_article: string;
  source_code_snippets: string[];
  repo_metadata: Record<string, unknown>;
}

export interface DocumentationResponse {
  audit_id: string;
  ai_system_id: string;
  required: boolean;
  status: "generated" | "not_required";
  message: string;
  mode: ResponseMode | null;
  artifact: ArtifactSummary | null;
  system_name: string | null;
  section_1_general_description: string | null;
  section_2_intended_purpose: string | null;
  section_3_human_oversight_measures: string | null;
  section_4_input_data_specs: string | null;
  section_5_design_specifications: string | null;
  section_6_risk_management_system: string | null;
  section_7_validation_testing: string | null;
  section_8_performance_metrics: string | null;
  section_9_post_market_monitoring: string | null;
  gaps_identified: string[];
  confidence: number | null;
}

export interface DemoHighRiskSystemResponse {
  audit_id: string;
  ai_system_id: string;
}

export type AgentPipelineState = "idle" | "active" | "complete" | "queued";

export interface AgentPipelineItem {
  name: string;
  model: string;
  blurb: string;
  state: AgentPipelineState;
  cue?: string;
}

export interface SampleRepo {
  label: string;
  repoUrl: string;
  maxFiles: number;
  note: string;
}

export type AuditProgressKey =
  | "initializing"
  | "scanning"
  | "detecting"
  | "classifying"
  | "building";

export interface AuditProgressStage {
  key: AuditProgressKey;
  label: string;
  detail: string;
  buttonLabel: string;
  progressStart: number;
  progressEnd: number;
}
