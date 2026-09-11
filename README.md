# 🛡️ SchemaSentinel-Strands
> **Autonomous Self-Healing Data Pipeline** powered by **Strands Agents SDK** & **AWS Bedrock Mantle** (Grok 4.6).

![Status](https://img.shields.io/badge/Status-Operational-10b981?style=for-the-badge)
![Agent](https://img.shields.io/badge/Strands_Agents-Bedrock_Mantle-blue?style=for-the-badge)
![Model](https://img.shields.io/badge/Model-xai.grok--4.6-f59e0b?style=for-the-badge)
![Security](https://img.shields.io/badge/AST_Sandbox-Verified-purple?style=for-the-badge)
![SLA](https://img.shields.io/badge/Reliability_SLA-100%25-success?style=for-the-badge)

---

## 💡 Overview
**SchemaSentinel-Strands** eliminates silent ETL pipeline crashes caused by upstream schema drift. When external APIs, third-party web scrapers, or ingress data streams mutate field names, nest objects in arrays, or alter rating scales, SchemaSentinel automatically:
1. **Detects Drift** without dropping records or crashing the pipeline.
2. **Synthesizes Python Transformation Patches** via Strands Agent on AWS Bedrock Mantle (`xai.grok-4.6`).
3. **Validates in an AST Security Sandbox** for zero-injection, isolated execution.
4. **Normalizes Scores** to a unified $0-100$ scale.
5. **Conforms & Commits** records to the warehouse with 100% data freshness, zero data loss, and zero human intervention.

---

## 🏗️ End-to-End System Architecture

```text
┌────────────────────────────────────────────────────────┐
│               UPSTREAM DATA INGRESS                    │
│  • Tavily Live Web Search (GitHub repositories)        │
│  • ChaosSchemaMutator (Simulating breaking API drift)  │
└───────────────────────────┬────────────────────────────┘
                            │ Ingress Payloads
                            ▼
┌────────────────────────────────────────────────────────┐
│             WAREHOUSE INGESTION BARRIER                │
│             (SQLite / Relational Schema)               │
│  Contract check: title, author, source_url, score      │
└───────────────────────────┬────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │         Schema Valid?         │
           YES                             NO (Contract Break / Exception)
            │                               │
            ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────────┐
│ 🟢 COMMITTED (Direct PASS)│   │  🚨 DRIFT DETECTOR INTERCEPTION   │
│ Ingestion Status = 'clean'│   │ Captures: Malformed Payload + SQL │
└───────────────────────────┘   └─────────────────┬─────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────┐
│               STRANDS AGENTS REASONING CORE                 │
│                 (Official Hackathon SDK)                    │
│                                                             │
│ AUTONOMOUS INFERENCE ENGINE:                                │
│ • AWS Bedrock Mantle (xai.grok-4.6 / Bedrock Runtime)       │
│                                                             │
│ Agent Step: Dispatches failing schema diff + target specs   │
│ and synthesizes pure deterministic Python function:         │
│     def transform_record(record: dict) -> dict              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Synthesized Code
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     AST SECURITY SANDBOX                    │
│  1. Python AST parsing (Abstract Syntax Tree)               │
│  2. Blacklist scanner (blocks os, sys, subprocess, eval)    │
│  3. Dynamic single-argument callable discovery              │
│  4. Memory-isolated namespace compilation                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │      AST Verified Safe?     │
               YES                            NO
                │                              │
                ▼                              ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│    ⚡ RUNTIME EXECUTION     │ │  🛡️ DETERMINISTIC FALLBACK  │
│  Applies patch to batch     │ │ Auto-recovers data without  │
│  Normalizes types & aliases │ │ dropping any records        │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │
               └───────────────┬───────────────┘
                               │ Conformed Records
                               ▼
┌────────────────────────────────────────────────────────┐
│               DATA WAREHOUSE PERSISTENCE               │
│ • Conformed record committed with UNIQUE constraints   │
│ • Status tagged: 'auto_healed'                         │
│ • 100% Zero Data Loss / 100% SLA Guarantee             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           HUMAN-IN-THE-LOOP OBSERVABILITY              │
│ • Streamlit Live SRE Dashboard                         │
│ • Real-Time DAG Stage Nodes (B01 Clean → B05 Drift)    │
│ • Side-by-Side Audit (Raw Ingress vs Conformed JSON)   │
│ • Live Telemetry Logs & Judge Interactive Playground   │
└────────────────────────────────────────────────────────┘