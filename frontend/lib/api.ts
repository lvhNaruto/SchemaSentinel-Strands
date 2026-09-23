import type { RecordDetail, SentinelState, TestResult } from "@/types";

const BASE = "/api"; // proxied to the FastAPI backend via next.config.mjs rewrites

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((detail as { detail?: string }).detail || `POST ${path} → ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  state: () => get<SentinelState>("/state"),
  topics: () => get<{ topics: string[] }>("/topics"),
  schema: () => get<{ schema: string; table: string }>("/schema"),
  record: (id: number) => get<RecordDetail>(`/warehouse/records/${id}`),
  runPipeline: (body: { mode: string; topics?: string[]; query?: string }) =>
    post<{ accepted: boolean; detail: string }>("/pipeline/run", body),
  testPayload: (payload: unknown) => post<TestResult>("/pipeline/test-payload", { payload }),
  reset: (clear_warehouse = true) =>
    post<{ ok: boolean }>(`/pipeline/reset?clear_warehouse=${clear_warehouse}`),
};
