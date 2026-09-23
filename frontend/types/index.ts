// Type mirror of the FastAPI service state — server is authoritative.

export interface Metrics {
  total_records: number;
  clean_count: number;
  healed_count: number;
  dlq_count: number;
  sla_percentage: number;
  total_attempted: number;
  dropped: number;
  last_latency_ms: number | null;
  sandbox_compiles: number;
}

export interface WarehouseRecord {
  project_id: number;
  title: string;
  author: string;
  source_url: string;
  relevance_score: number;
  extra_metadata?: string;
  batch_id: string | null;
  ingestion_status: string | null;
  created_at: string;
}

export interface DlqRecord {
  dlq_id: number;
  raw_payload: string;
  failure_reason: string;
  detected_keys?: string;
  batch_id: string;
  quarantined_at: string;
}

export type TelemetryTag =
  | "SYSTEM"
  | "INGRESS"
  | "COMMITTED"
  | "DRIFT_DETECTED"
  | "STRANDS_AGENT"
  | "AST_VERIFIED"
  | "DLQ_QUARANTINED"
  | "STREAM_IDLE";

export interface TelemetryEvent {
  id: number;
  ts: string;
  tag: string;
  message: string;
  stage: string | null;
  dlq_active: boolean;
}

export interface HealingAudit {
  batch_id: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  error?: string;
  patch?: string;
  signature: string;
  latency_ms: number | null;
  ast_verified: boolean;
  ts: string;
}

export interface AstCheck {
  name: string;
  detail: string;
}

export interface AstInfo {
  state: "verified" | "rejected" | "standby";
  verified: boolean | null;
  message: string;
  checks: AstCheck[];
  compiles: number;
}

export interface CacheEntry {
  signature: string;
  label: string;
  first_seen: string;
  last_seen: string;
  occurrences: number;
}

export interface PatchInfo {
  code: string;
  signature: string | null;
  latency_ms: number | null;
  verified: boolean;
}

export interface SentinelState {
  running: boolean;
  stage: string | null;
  dlq_active: boolean;
  run_count: number;
  metrics: Metrics;
  warehouse: WarehouseRecord[];
  dlq: DlqRecord[];
  telemetry: TelemetryEvent[];
  healing: HealingAudit | null;
  patch: PatchInfo | null;
  ast: AstInfo;
  cache: { note: string; signatures: CacheEntry[] };
}

export interface RecordAudit {
  batch_id: string;
  signature: string;
  latency_ms: number | null;
  ast_verified: boolean;
  ts: string;
  patch: string;
}

export interface RecordDetail {
  record: WarehouseRecord;
  healing_audit: RecordAudit | null;
}

export type TestStatus = "healed" | "clean" | "quarantined";

export interface TestResult {
  status: TestStatus;
  before?: Record<string, unknown>;
  after?: Record<string, unknown>;
  patch?: string;
  signature?: string;
  latency_ms?: number | null;
  ast_verified?: boolean;
  reason?: string;
}

export type PipelineStage =
  | "ingress"
  | "fingerprint"
  | "drift"
  | "agent"
  | "ast"
  | "warehouse";
