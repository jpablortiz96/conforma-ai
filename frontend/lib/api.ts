import type { ClassifierRequest, ClassifierResponse, HealthResponse } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 12000;

function normalizeClassifierText(value: string): string {
  return value.replaceAll("Â§", "Section ").replaceAll("§", "Section ");
}

function normalizeClassifierResponse(payload: ClassifierResponse): ClassifierResponse {
  return {
    ...payload,
    primary_article: normalizeClassifierText(payload.primary_article),
    secondary_articles: payload.secondary_articles.map(normalizeClassifierText),
    reasoning: normalizeClassifierText(payload.reasoning),
    deadline: normalizeClassifierText(payload.deadline)
  };
}

async function fetchWithTimeout(input: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The backend did not respond in time. Check that http://localhost:8000 is running.");
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

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/`, {
    method: "GET",
    cache: "no-store"
  });

  return parseResponse<HealthResponse>(response);
}

export async function classifySystem(
  payload: ClassifierRequest
): Promise<ClassifierResponse> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/agents/classifier`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return normalizeClassifierResponse(await parseResponse<ClassifierResponse>(response));
}
