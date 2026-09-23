# 🛡️ SchemaSentinel-Strands
> **Autonomous Self-Healing Data Reliability Agent for Streaming Pipelines**
> Powered by **Strands Agents SDK** on **AWS Bedrock Mantle** with **Nebius Studio SOTA LLM Fallback** • AST Security Sandbox • Dead Letter Queue (DLQ)

---

## 🏗️ Architecture

```
Next.js Frontend (frontend/)          ← the user-facing product
        │  HTTP + SSE (proxied via /api)
        ▼
FastAPI Service Layer (api/)          ← thin, non-business layer
        │
        ▼
Extracted Pipeline Service (services/)  ← orchestration extracted from the old UI
        │
        ▼
Python Core (unchanged)               ← the engine
├── agent.py        Strands healing agent (Bedrock Mantle → Nebius fallback,
│                   patch synthesis, schema signatures)
├── sandbox.py      AST security sandbox (banned modules/calls, isolated compile)
├── database.py     SQLite warehouse (tech_projects) + DLQ (tech_projects_dlq)
└── data_producer.py  Stream ingress + ChaosSchemaMutator (live GitHub/Tavily resolution first, offline catalog fallback)
```

The backend business logic is the single source of truth — the frontend never reimplements it.

---

## 🚀 Quickstart

```bash
# 1. Install backend dependencies
pip install -r requirements.txt

# 2. Environment Configuration (.env) — same keys as before
AWS_REGION=us-west-2
BEDROCK_API_KEY=...
NEBIUS_API_KEY=...
TAVILY_API_KEY=...
# Optional: raises GitHub unauthenticated rate-limit ceiling
GITHUB_TOKEN=ghp_xxx

# 3. Start the API backend
uvicorn api.main:app --reload --port 8000

# 4. Start the frontend (separate terminal)
cd frontend
npm install
npm run dev        # http://localhost:3000
```

CLI pipeline still works exactly as before:

```bash
python pipeline_runner.py
python pipeline_runner.py "your custom topic"
```

## 🧠 3-Tier Data Triage SLA

| Tier | Condition | Outcome |
|---|---|---|---
| **Clean** | Payload matches `title`, `author`, `source_url`, `relevance_score` exactly | Bypasses the LLM; committed to `tech_projects` as `clean` (zero latency, zero tokens) |
| **Drift / Mixed** | Legitimate project data with renamed keys, authors in URLs, percentage scores, or extra fields | Agent synthesizes an AST-verified `transform_record` patch; committed as `auto_healed`; all unmapped keys are preserved in `extra_metadata` |
| **Alien / Corrupted** | No project identity (e.g., IoT sensor readings, random noise) | Agent raises `IRRECOVERABLE_SCHEMA_DRIFT`; sandbox routes the raw payload to `tech_projects_dlq` with detected keys |

## 💾 Learned Template Cache

Drift shapes are fingerprinted with SHA-256 of the sorted key set. The first time a shape is seen, the LLM synthesizes a patch, the AST sandbox verifies it, and the patch is stored in the `template_cache` table. Subsequent records with the same shape reuse the cached template, skipping the LLM entirely. The cache is surfaced in the UI under **Learned Templates**.

---

## 🧪 API Reference (FastAPI, default http://127.0.0.1:8000)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness + engine status |
| GET | `/api/state` | Full dashboard snapshot (metrics, warehouse, DLQ, telemetry, healing, patch, AST, learned templates) |
| GET | `/api/pipeline/status` | Running / stage / counters |
| POST | `/api/pipeline/run` | Start autonomous stream `{mode: "preset"\|"custom", topics?, query?}` |
| POST | `/api/pipeline/test-payload` | Judge playground `{payload: {...}}` — real healing path |
| POST | `/api/pipeline/reset?clear_warehouse=true` | Reset engine state (and optionally truncate tables) |
| GET | `/api/events` | **SSE** stream of real telemetry events |
| GET | `/api/schema` | Live warehouse contract (PRAGMA) |
| GET | `/api/topics` | Preset ingress partitions |
| GET | `/api/warehouse/records` / `/{id}` | Warehouse rows / record + linked healing audit |
| GET | `/api/dlq/records` | DLQ rows |
| GET | `/api/telemetry` | Last telemetry events (REST fallback) |
| GET | `/api/patches/latest` | Last synthesized patch + metadata |
| GET | `/api/ast/status` | Real AST verification state + enforced checks |
| GET | `/api/cache/status` | Learned transformation template cache |

---

## 🖥️ The Demo (2 minutes)

1. Open **http://localhost:3000** — deep obsidian command center.
2. Click **Run Autonomous Healing Pipeline** — watch the live pipeline stage tracker (GSAP),
   telemetry terminal, and Before → AI → After transformation.
3. Open **Judge Playground**, pick **Alien Payload**, click **Test Healing** — the real Strands
   agent synthesizes a patch, the AST sandbox verifies it, and the verdict stepper shows
   Detected → Agent → AST → Healed (or → DLQ).
4. Watch the warehouse fill with ✨ Auto-Healed rows and the DLQ stay clean.
5. **Reset** to wipe state and re-arm for the next demo.

---

## 📁 Repository Layout

```
SchemaSentinel-Strands/
├── agent.py / sandbox.py / database.py / data_producer.py   # the engine (unchanged)
├── pipeline_runner.py                                       # CLI pipeline (unchanged)
├── services/pipeline_service.py                             # orchestration extracted from the old UI
├── api/                                                     # FastAPI layer (main, schemas)
├── frontend/                                                # Next.js 14 + TS + Tailwind + Motion + GSAP
│   ├── app/          # layout, page, globals.css
│   ├── components/   # Header, PipelineFlow, HealingHero, Warehouse, DlqPanel,
│   │                 # TelemetryFeed, SandboxPanel, CachePanel, Playground, StreamSource
│   ├── components/ui/# hand-rolled shadcn-style primitives (button, badge, dialog, tabs)
│   ├── hooks/        # useSentinel (SSE + polling)
│   ├── lib/ types/   # api client, shared types
├── docs/FRONTEND_MIGRATION_PLAN.md
└── requirements.txt
```

See `docs/FRONTEND_MIGRATION_PLAN.md` for the full migration analysis, risks, and verification strategy.


---

## ⚡ The Problem & Why SchemaSentinel Exists

 *"Data engineers spend over 40% of their working hours manually firefighting broken data pipelines instead of building strategic infrastructure."* — **Gartner & Monte Carlo Data Reliability Study**
> 
> *"The cost of bad data in the US alone is estimated at a staggering $3.1 Trillion per year."* — **IBM & Harvard Business Review Research**

**Imagine this:** It's 2:00 AM. A third-party company pushes an update and silently changes a single field name: `"user_id"` becomes `"userId"`.

Instantly, your entire data pipeline crashes. Red alert sirens go off on PagerDuty. Critical executive dashboards freeze, analytics reports show zero, and engineers are woken up in the middle of the night to write an emergency 2-line code fix.

**Data pipes shouldn't be this fragile.**

**SchemaSentinel acts as an autonomous shock-absorber for your data.** Think of it like a smart universal adapter: the moment incoming data shifts or changes shape, SchemaSentinel automatically catches it, rewires the mismatch in 300 milliseconds using pure multi-cloud agentic reasoning, and flows clean data straight into your warehouse—**no broken pipelines, no midnight alarms, and zero downtime.**

---

## 🏗️ Multi-Cloud Resilience Architecture

<p align="center">
  <img src="https://github.com/user-attachments/assets/c639e77f-3409-44c9-96f4-aa158d1146d4" alt="SchemaSentinel Architecture Flow" width="100%" />
</p>

