export type RiskClass =
  | "UNACCEPTABLE"
  | "HIGH_RISK"
  | "LIMITED_RISK"
  | "MINIMAL_RISK";

export type ResponseMode = "gemini" | "fallback";
export type GapSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type MonitorAlertSeverity = "CRITICAL" | "WARNING" | "INFO";
export type MonitorAlertType =
  | "DEADLINE_APPROACH"
  | "REGULATORY_UPDATE"
  | "DRIFT_SIMULATION"
  | "MISSING_CONTROL";
export type ReadinessLevel = "LOW" | "MEDIUM" | "HIGH" | "ENTERPRISE_READY";
export type AgentKey =
  | "scanner"
  | "classifier"
  | "documentation"
  | "disclosure"
  | "gap_auditor"
  | "monitor";
export type AgentPipelineState = "idle" | "active" | "complete" | "queued" | "failed";
export type AuditStreamStatus = "started" | "completed" | "failed";
export type AuditStreamEventName =
  | "audit_started"
  | "scanner_started"
  | "scanner_completed"
  | "classifier_started"
  | "classifier_completed"
  | "documentation_started"
  | "documentation_completed"
  | "disclosure_started"
  | "disclosure_completed"
  | "gap_auditor_started"
  | "gap_auditor_completed"
  | "monitor_started"
  | "monitor_completed"
  | "audit_completed"
  | "audit_failed";

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

export interface DisclosureNotices {
  en: string;
  it: string;
  es: string;
  fr: string;
  de: string;
}

export interface DisclosureResponse {
  audit_id: string;
  ai_system_id: string;
  requires_disclosure: boolean;
  article: string | null;
  notices: DisclosureNotices | null;
  placement_recommendations: string[];
  confidence: number | null;
  mode: ResponseMode | null;
}

export interface ComplianceGap {
  severity: GapSeverity;
  title: string;
  description: string;
  affected_system_id: string | null;
  recommended_action: string;
  legal_reference: string;
}

export interface CompliancePackResponse {
  audit_id: string;
  compliance_score: number;
  estimated_fine_exposure_eur: number;
  time_to_compliant_days: number;
  systems_count: number;
  high_risk_count: number;
  article_50_count: number;
  gaps: ComplianceGap[];
  disclosures: DisclosureResponse[];
  priority_actions: string[];
  summary: string;
}

export interface MonitorAlert {
  severity: MonitorAlertSeverity;
  type: MonitorAlertType;
  title: string;
  description: string;
  affected_system_id: string | null;
  recommended_action: string;
  deadline_iso: string | null;
}

export interface MonitorResponse {
  audit_id: string;
  alerts: MonitorAlert[];
  next_check_at: string;
  summary: string;
  mode: ResponseMode | null;
}

export interface ExecutiveBusinessImpact {
  estimated_fine_exposure_eur: number;
  time_to_compliant_days: number;
  systems_at_risk: number;
  critical_actions_count: number;
}

export interface RegulatoryTimelineEntry {
  date: string;
  label: string;
  affected_systems: string[];
}

export interface ExecutiveSummaryResponse {
  audit_id: string;
  board_summary: string;
  business_impact: ExecutiveBusinessImpact;
  regulatory_timeline: RegulatoryTimelineEntry[];
  top_5_actions: string[];
  investor_style_one_liner: string;
  readiness_level: ReadinessLevel;
}

export interface EvidenceVaultGap {
  category: string;
  severity: string;
  description: string;
  remediation: string;
  deadline: string | null;
}

export interface EvidenceVaultAgentRun {
  agent_name: string;
  status: string;
  model: string | null;
  started_at: string;
  completed_at: string | null;
  error: string | null;
  output: Record<string, unknown> | null;
}

export interface EvidenceVaultSystem {
  id: string;
  name: string;
  description: string;
  source_files: string[];
  detection_signals: string[];
  risk_class: string | null;
  primary_article: string | null;
  secondary_articles: string[];
  reasoning: string | null;
  deadline: string | null;
  deadline_iso: string | null;
  confidence: number | null;
  triggers_article_50: boolean;
  artifacts: ArtifactSummary[];
  disclosures: DisclosureResponse[];
  gaps: EvidenceVaultGap[];
  agent_runs: EvidenceVaultAgentRun[];
}

export interface EvidenceVaultResponse {
  audit_id: string;
  repo_url: string;
  systems: EvidenceVaultSystem[];
  audit_level_runs: EvidenceVaultAgentRun[];
  monitor_alerts: MonitorAlert[];
  summary: string;
}

export interface OrchestratedAuditStartResponse {
  audit_id: string;
  repo_url: string;
  status: "running";
  stream_url: string;
}

export interface AuditStreamEvent {
  audit_id: string;
  agent: string;
  status: AuditStreamStatus;
  message: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface OrchestratedAuditCompletedResponse {
  audit_id: string;
  repo_url: string;
  status: "completed";
  systems: AuditSystem[];
  portfolio_risk_index: number;
  summary: string;
  compliance_pack: CompliancePackResponse;
  monitor: MonitorResponse;
  executive_summary: ExecutiveSummaryResponse;
  evidence_vault: EvidenceVaultResponse;
}

export interface AgentPipelineItem {
  key: AgentKey;
  name: string;
  model: string;
  blurb: string;
  state: AgentPipelineState;
  cue?: string;
  branch?: "core" | "parallel" | "post";
}

export interface SampleRepo {
  label: string;
  repoUrl: string;
  maxFiles: number;
  note: string;
}
