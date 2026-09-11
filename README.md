# 🛡️ SchemaSentinel: Autonomous Self-Healing Data Pipeline

> **Zero-Downtime Data Ingestion Engine Powered by NVIDIA Nemotron-3.5-Lightning & Nebius Token Factory**

---

## 📌 Overview

Modern data pipelines frequently fail due to **upstream schema drift**—unannounced API changes, field renames, missing keys, or varying data representations (percentages, strings, nested objects). Standard data pipelines crash when encountering these anomalies, requiring manual debugging, code hotfixes, and engineering downtime.

**SchemaSentinel** is an autonomous, self-healing streaming data pipeline designed to detect schema mismatches in real time, query an LLM transformation agent to synthesize custom runtime Python patches, verify those patches in an isolated sandbox, and commit repaired records directly to an operational warehouse—all with zero human intervention and zero pipeline downtime.

---

## ✨ Key Features

* **Autonomous Schema Drift Interception:** Intercepts runtime schema mismatches (e.g., `KeyError`, type mismatches, missing nested fields) without terminating the ingestion stream.
* **LLM-Driven Code Synthesis:** Leverages **NVIDIA Nemotron-3.5-Lightning** hosted on **Nebius Token Factory** to evaluate the delta between raw payload structures and the target warehouse contract, dynamically producing executable Python transformation logic.
* **Deterministic Sandbox Validation:** Validates dynamically generated transformation patches within an isolated execution environment using Python's `ast` (Abstract Syntax Tree) engine before database commitment.
* **Resilient Heuristic Fallbacks:** Integrates deterministic fallback logic to ensure uninterrupted pipeline operation if external API limits or network latencies occur.
* **Real-Time Visual Audit Dashboard:** A Streamlit interface providing side-by-side **Before AI vs. After AI** JSON diffs, real-time database state views, and live generated patch inspections.

---

## 🏗️ Architecture & Workflow

```text
[ Live Web / Tavily / Stream Source ]
                  │
                  ▼
         [ Ingestion Attempt ]
                  │
         ┌────────┴────────┐
         │                 │
    (Valid Schema)    (Schema Drift Detected)
         │                 │
         ▼                 ▼
   [ DB Commit ]     [ Schema Sentinel Agent ]
                           │ (Nebius + NVIDIA Nemotron)
                           ▼
                    [ Synthesize Code Patch ]
                           │
                           ▼
                    [ Sandbox Executor ]
                           │
                           ▼
                 [ Warehouse Ingestion ]