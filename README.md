# 🛡️ SchemaSentinel-Strands
> **Autonomous Self-Healing Data Reliability Agent for Streaming Pipelines**  
> Powered by **Strands Agents SDK** on **AWS Bedrock Mantle** with **Nebius Studio SOTA LLM Fallback** • AST Security Sandbox • Dead Letter Queue (DLQ)

---

## ⚡ The Problem & Why SchemaSentinel Exists

**Imagine this:** It's 2:00 AM. A third-party company pushes an update and silently changes a single field name: `"user_id"` becomes `"userId"`.

Instantly, your entire data pipeline crashes. Red alert sirens go off on PagerDuty. Critical executive dashboards freeze, analytics reports show zero, and engineers are woken up in the middle of the night to write an emergency 2-line code fix.

**Data pipes shouldn't be this fragile.**

**SchemaSentinel acts as an autonomous shock-absorber for your data.** Think of it like a smart universal adapter: the moment incoming data shifts or changes shape, SchemaSentinel automatically catches it, rewires the mismatch in 300 milliseconds using pure multi-cloud agentic reasoning, and flows clean data straight into your warehouse—**no broken pipelines, no midnight alarms, and zero downtime.**

---

## 🏗️ Multi-Cloud Resilience Architecture

<p align="center">
  <img src="https://github.com/user-attachments/assets/c639e77f-3409-44c9-96f4-aa158d1146d4" alt="SchemaSentinel Architecture Flow" width="100%" />
</p>

---

## 🚀 Quickstart

```bash
# 1. Clone & Install
git clone https://github.com/lvhNaruto/SchemaSentinel-Strands.git
cd SchemaSentinel-Strands
pip install -r requirements.txt

# 2. Environment Configuration (.env)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-west-2
NEBIUS_API_KEY=your_nebius_studio_key
TAVILY_API_KEY=your_tavily_key

# 3. Launch Dashboard
streamlit run app.py
