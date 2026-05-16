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

export interface AgentRoadmapItem {
  name: string;
  model: string;
  status: string;
  purpose: string;
}
