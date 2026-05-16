import type { ClassifierRequest, ClassifierResponse, HealthResponse } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/`, {
    method: "GET",
    cache: "no-store"
  });

  return parseResponse<HealthResponse>(response);
}

export async function classifySystem(
  payload: ClassifierRequest
): Promise<ClassifierResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agents/classifier`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse<ClassifierResponse>(response);
}
