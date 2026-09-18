import type { RunPage, RunSnapshot } from "./types";

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

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}
