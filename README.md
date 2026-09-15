# 🛡️ SchemaSentinel-Strands
> **Autonomous Self-Healing Data Reliability Agent for Streaming Pipelines**  
> Powered by **Strands Agents SDK** on **AWS Bedrock Mantle (Grok 4.6)** • AST Security Sandbox • Dead Letter Queue (DLQ)

---

## ⚡ The Problem & Why SchemaSentinel Exists

**Imagine this:** It's 2:00 AM. A third-party company pushes an update and silently changes a single field name: `"user_id"` becomes `"userId"`.

Instantly, your entire data pipeline crashes. Red alert sirens go off on PagerDuty. Critical executive dashboards freeze, analytics reports show zero, and engineers are woken up in the middle of the night to write an emergency 2-line code fix.

**Data pipes shouldn't be this fragile.**

**SchemaSentinel acts as an autonomous shock-absorber for your data.** Think of it like a smart universal adapter: the moment incoming data shifts or changes shape, SchemaSentinel automatically catches it, rewires the mismatch in 300 milliseconds, and flows clean data straight into your warehouse—**no broken pipelines, no midnight alarms, and zero downtime.**

---

## 🏗️ Architecture

```text
[ Upstream Ingress Stream ] (GitHub REST API + Tavily Grounding)
            │
            ▼
[ Tier-1: Linguistic Entropy Guard ] (Rejects keyboard mash in 0.1ms)
            │
            ▼
[ Warehouse Contract Validator ]
    ├── Matches DDL  ────────► [ ✅ Clean Ingress ] ────┐
    └── Drift Detected                                  │
            │                                           ▼
            ▼                                 [ Live Warehouse ]
  [ Strands Agent Engine ]                     (tech_projects)
    (AWS Bedrock Mantle)                      (0% Schema Downtime)
            │                                           ▲
            ▼                                           │
  [ AST Security Sandbox ]                              │
    ├── Compile Passed ──────► Auto-Heals & Conforms ───┘
    └── Compile Failed ──────► [ Dead Letter Queue (DLQ) ]
                               (tech_projects_dlq)
                               (Zero Warehouse Pollution)
```

---

## 🚀 Quickstart

```bash
# 1. Clone & Install
git clone https://github.com/lvhNaruto/SchemaSentinel-Strands.git
cd SchemaSentinel-Strands
pip install -r requirements.txt

# 2. Environment (.env)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
TAVILY_API_KEY=your_key

# 3. Launch App
streamlit run app.py
```
