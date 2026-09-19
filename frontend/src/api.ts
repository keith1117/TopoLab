import type { RunPage, RunSnapshot, TopologyProblem } from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export async function listRuns(cursor?: string): Promise<RunPage> {
  const query = new URLSearchParams({ limit: "10" });
  if (cursor) {
    query.set("cursor", cursor);
  }
  return requestJson<RunPage>(`/runs?${query.toString()}`);
}

export async function getRun(runId: string): Promise<RunSnapshot> {
  return requestJson<RunSnapshot>(`/runs/${encodeURIComponent(runId)}`);
}

export async function createRun(problem: TopologyProblem): Promise<RunSnapshot> {
  return requestJson<RunSnapshot>("/runs", {
    method: "POST",
    body: JSON.stringify(problem),
  });
}

export async function cancelRun(runId: string): Promise<RunSnapshot> {
  return requestJson<RunSnapshot>(
    `/runs/${encodeURIComponent(runId)}/cancel`,
    { method: "POST" },
  );
}

async function requestJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      detail = formatErrorDetail(payload.detail) ?? detail;
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

function formatErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }
  if (!Array.isArray(detail)) {
    return null;
  }
  const messages = detail.flatMap((item) => {
    if (!item || typeof item !== "object" || !("msg" in item)) {
      return [];
    }
    const message = String(item.msg);
    if (!("loc" in item) || !Array.isArray(item.loc)) {
      return [message];
    }
    const location = (item.loc as unknown[])
      .filter((part: unknown) => part !== "body")
      .map(String)
      .join(" → ");
    return [location ? `${location}: ${message}` : message];
  });
  return messages.length > 0 ? messages.join("; ") : null;
}
