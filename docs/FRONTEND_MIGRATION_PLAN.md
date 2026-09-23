# Frontend Migration Plan — Streamlit → Next.js

## 1. Current Architecture (before migration)

```
streamlit run app.py          ← presentation + orchestration (monolith)
        │
        ├── database.py       WarehouseDatabase  (tech_projects + tech_projects_dlq, SQLite)
        ├── agent.py          SchemaHealingAgent (Bedrock Mantle primary → Nebius fallback,
        │                                        synthesize_transformation_patch, extract_pure_code,
        │                                        compute_schema_signature, create_structural_skeleton)
        ├── sandbox.py        SandboxExecutor   (AST safety: banned modules os/sys/subprocess/
        │                                        socket/shutil/requests/urllib; banned calls
        │                                        eval/exec/__import__/compile/open; isolated compile)
        └── data_producer.py  fetch_multi_topic_stream_batches + ChaosSchemaMutator
                            (preset topic catalog + live GitHub/Tavily resolution)

pipeline_runner.py            CLI pipeline (no Streamlit dependency) — keep as-is
```

- Pure backend logic: `database.py`, `agent.py`, `sandbox.py`, `data_producer.py`, `pipeline_runner.py`.
- Streamlit-only logic: everything in `app.py` — session state, widgets, metrics formatting,
  pipeline orchestration loop, playground flow, entropy guard usage, telemetry log strings.
- State that lives only inside Streamlit session: `db handle`, `healing_history`, `healed_urls`,
  `last_patch`, `run_count`, `topic_cursor`, `telemetry_logs`, `last_latency_ms`,
  `total_ingress_attempted`, `sandbox_compiles_count`, `pipeline_stage`, `last_ast_ok`.

## 2. Existing Backend Capabilities (source of truth, unchanged)

1. Multi-topic stream ingress (preset partitions or live grounded resolution).
2. **3-Tier Data Triage:**
   - Clean-commit path: `db.insert_batch(records, status="clean")`.
   - Drift detection = warehouse contract violation (exception from `insert_batch`).
   - Agentic patch synthesis via `SchemaHealingAgent` (Bedrock → Nebius, zero fake fallback).
   - Auto-healed warehouse commit (`insert_batch(..., status="auto_healed")`) with `extra_metadata` side-car for unmapped fields.
   - DLQ quarantine for irrecoverable / alien payloads (`db.insert_dlq` with detected keys).
3. Patch extraction (`extract_pure_code`) + AST sandbox compile (`SandboxExecutor.compile_patch`).
4. Schema signature fingerprinting (`compute_schema_signature`, SHA-256 of sorted keys).
5. Warehouse / DLQ reads; live DDL contract via `get_table_schema`.
6. Entropy guard for custom ingress queries (`is_meaningful_query`).
## 3. Learned Transformation Template Cache

To eliminate repeated LLM calls for the same drift shape, the engine now maintains a `template_cache` table keyed by the schema signature (`compute_schema_signature`).

Flow:
1. Drift detected → compute SHA-256 signature of sorted record keys.
2. Cache hit → compile and execute the stored patch; skip LLM synthesis.
3. Cache miss → invoke the Strands agent, AST-verify the patch, store it in `template_cache`, then execute it.

This makes the engine self-improving: the first occurrence of a drift shape pays the LLM cost, and every subsequent occurrence is healed in single-digit milliseconds with zero API tokens. The cache is exposed via `/api/cache/status` and rendered in the **Learned Templates** UI panel.



## 3. Streamlit Dependencies

- `streamlit` (framework); `pandas` was used for UI dataframe rendering only (not in requirements.txt).
- No other module imports Streamlit. `app.py` is the only Streamlit-dependent file.

## 4. Extraction Plan (minimal, structural only)

| Extracted from app.py | New location | Nature |
|---|---|---|
| pipeline run loop + healing dispatcher | `services/pipeline_service.py` | thread-safe service, identical control flow |
| playground payload flow | `services/pipeline_service.py::test_payload` | identical control flow |
| reset logic | `services/pipeline_service.py::reset` | identical (option to truncate tables, see §7) |
| entropy guard (query validation) | `services/pipeline_service.py` | verbatim functions |
| metrics computation | `services/pipeline_service.py::get_state` | same formulas |
| telemetry strings | service `_emit(tag, message)` events | same semantics, structured |

Additive backend change (no behavior change):
- `database.py::clear_all()` — truncate helper so "Reset Warehouse & DLQ" can actually
  empty the tables (the Streamlit version re-created the connection without deleting rows —
  a legacy gap; `reset(clear_warehouse=False)` preserves the legacy behavior exactly).
- Latent bug found during extraction: `agent.get_fallback_dict(r)` is called by the old UI but
  does not exist on `SchemaHealingAgent`. Guarded via `getattr` — if absent, the record is
  routed to DLQ (the Zero-Crash Shield intent) instead of crashing. `agent.py` is NOT modified.

NOT changed: `agent.py` (prompts, providers, models), `sandbox.py`, `data_producer.py`,

## 5. API Plan (FastAPI, thin layer over the service)

| Endpoint | Purpose |
|---|---|
| GET  /api/health | liveness + engine status |
| POST /api/pipeline/run | start autonomous stream (background thread), body `{mode, topics?, query?}` |
| GET  /api/pipeline/status | running / stage / run counters |
| POST /api/pipeline/test-payload | Judge Playground — real healing path, returns structured verdict |
| POST /api/pipeline/reset | reset state; `?clear_warehouse=true|false` (default true) |
| GET  /api/events | SSE stream of telemetry events (each carries stage + dlq_active) |
| GET  /api/state | full dashboard snapshot (metrics, rows, dlq, telemetry, healing, patch, ast, cache) |
| GET  /api/schema | live target schema contract (PRAGMA) |
| GET  /api/warehouse/records | warehouse rows |
| GET  /api/warehouse/records/{id} | single record + linked healing audit |
| GET  /api/dlq/records | DLQ rows |
| GET  /api/telemetry | last telemetry events (REST fallback) |
| GET  /api/patches/latest | last synthesized patch + metadata |
| GET  /api/ast/status | real AST verification state + enforced checks (derived from SandboxExecutor) |
| GET  /api/cache/status | real fingerprint signature registry (see §7 cache honesty) |

CORS enabled for the Next.js dev origin; SSE preferred, no WebSockets (unnecessary here).

## 6. Frontend Plan (frontend/, Next.js App Router)

- Stack: Next.js 14 + React 18 + TypeScript + Tailwind + shadcn-style components (hand-rolled),
  Motion (framer-motion) for micro-interactions, GSAP (matchMedia, reduced-motion aware) for
  the pipeline flow, Lucide icons.
- Sections: Header (status, Run, Target Schema, Reset) → Metrics → Live Pipeline →
  Before/AI/After hero → Warehouse (tabs + search + inspector) → DLQ → Telemetry →
  AST Sandbox + Patch viewer → Fingerprint panel → Judge Playground.
- Data: `useSentinel` hook — SSE for liveness + polling `/api/state` on every event (server
  is authoritative; no fabricated state).
- Visual system: Deep Obsidian/Midnight Navy; semantic colors emerald/violet/cyan/amber/rose;
  Inter + Space Grotesk, JetBrains Mono for JSON/Python/SQL/telemetry.
- Accessibility: semantic HTML, ARIA labels, visible focus, keyboard-navigable dialogs/tabs,
  `prefers-reduced-motion` honored in both Motion and GSAP.

## 7. Risks & Mitigations

- **LLM dependency:** synthesis needs live Bedrock/Nebius credentials. If unreachable, the
  engine routes drifted batches to DLQ (real, documented failure defense) — never faked success.
- **Fingerprint cache honesty:** the engine tracks SHA-256 signatures but has no
  synthesis-skip cache; the UI reports the real registry (NEW vs RECURRING signature) and never
  claims "LLM synthesis skipped" unless the backend actually reports it.
- **Concurrent runs:** service is single-flight (a run lock) — matches the single-operator demo.
- **SSE through Next rewrites:** dev proxy streams SSE; REST polling is the automatic fallback.
- **Windows environment:** uvicorn + threads verified on the existing Python 3.11 install.

## 8. Verification Strategy

Backend: uvicorn boot → /api/health → POST /api/pipeline/run (preset topics) → poll
/api/state for COMMITTED / DRIFT_DETECTED / AST_VERIFIED / DLQ_QUARANTINED events, warehouse
rows, DLQ rows → POST /api/pipeline/test-payload (alien payload) → POST /api/pipeline/reset.
CLI regression: `python pipeline_runner.py` still runs.

Frontend: `npm install` → `npm run build` (type-safe) → `npm run dev` → HTTP 200 on / ,
API wired through Next rewrites → run pipeline from the UI flow (same API calls) → verify
warehouse/DLQ/telemetry update.

Streamlit removal: delete `app.py`, `app_original_backup.py`, `.streamlit/`; drop `streamlit`
and `rich` from requirements.txt (verified unused by remaining modules).


