<img width="276" height="150" alt="architecture-flow" src="https://github.com/user-attachments/assets/c639e77f-3409-44c9-96f4-aa158d1146d4" /># 🛡️ SchemaSentinel-Strands
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

![Upl<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 500" width="100%" height="100%" style="background: #020617; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <defs>
    <!-- Gradients -->
    <linearGradient id="emeraldGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#064e3b" stop-opacity="0.3"/>
    </linearGradient>
    <linearGradient id="cyanGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#083344" stop-opacity="0.3"/>
    </linearGradient>
    <linearGradient id="amberGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#451a03" stop-opacity="0.3"/>
    </linearGradient>
    <linearGradient id="roseGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#4c0519" stop-opacity="0.3"/>
    </linearGradient>

    <!-- Filters -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <!-- Animated Dash Pattern -->
    <style>
      .flow-line { stroke-dasharray: 6 6; animation: dash 1.5s linear infinite; }
      @keyframes dash { to { stroke-dashoffset: -24; } }
      .pulse-node { animation: pulse 2s ease-in-out infinite; }
      @keyframes pulse { 0%, 100% { opacity: 0.9; transform: scale(1); } 50% { opacity: 1; transform: scale(1.02); } }
      .badge-blink { animation: blink 1.2s ease-in-out infinite; }
      @keyframes blink { 0%, 100% { opacity: 0.8; } 50% { opacity: 1; } }
    </style>
  </defs>

  <!-- Canvas Subtle Grid -->
  <g stroke="#1e293b" stroke-width="0.5" opacity="0.4">
    <line x1="0" y1="100" x2="920" y2="100" />
    <line x1="0" y1="200" x2="920" y2="200" />
    <line x1="0" y1="300" x2="920" y2="300" />
    <line x1="0" y1="400" x2="920" y2="400" />
    <line x1="150" y1="0" x2="150" y2="500" />
    <line x1="300" y1="0" x2="300" y2="500" />
    <line x1="450" y1="0" x2="450" y2="500" />
    <line x1="600" y1="0" x2="600" y2="500" />
    <line x1="750" y1="0" x2="750" y2="500" />
  </g>

  <!-- Title Header inside Graphic -->
  <text x="40" y="42" fill="#ffffff" font-size="16" font-weight="bold" letter-spacing="-0.5">🛡️ SchemaSentinel-Strands Architecture</text>
  <text x="40" y="60" fill="#94a3b8" font-size="11">Autonomous Cognitive Data Self-Healing Engine for Streaming Pipelines</text>

  <!-- Top Badges -->
  <rect x="650" y="28" width="230" height="28" rx="14" fill="#022c22" stroke="#10b981" stroke-width="1" />
  <circle cx="666" cy="42" r="4" fill="#34d399" class="badge-blink" />
  <text x="680" y="46" fill="#34d399" font-size="11" font-weight="600">Sub-10ms Fingerprint Cache</text>

  <!-- ==================== FLOW TRACES ==================== -->
  <!-- 1. Stream Ingress to Entropy Guard -->
  <path d="M 160 140 L 250 140" stroke="#10b981" stroke-width="2.5" class="flow-line" />

  <!-- 2. Entropy Guard to Contract Interceptor -->
  <path d="M 380 140 L 460 140" stroke="#06b6d4" stroke-width="2.5" class="flow-line" />

  <!-- 3A. Clean Pass Line (Direct to SQLite Target) -->
  <path d="M 580 140 L 740 140" stroke="#10b981" stroke-width="2.5" class="flow-line" />
  <text x="660" y="130" fill="#34d399" font-size="10" font-weight="bold" text-anchor="middle">✓ Clean Pass</text>

  <!-- 3B. Drift Intercepted Line (Down to Cache) -->
  <path d="M 520 175 L 520 240" stroke="#f59e0b" stroke-width="2.5" class="flow-line" />
  <text x="535" y="210" fill="#fbbf24" font-size="10" font-weight="bold">Drift Detected</text>

  <!-- 4A. Cache Hit (<0.01s) direct to AST Sandbox -->
  <path d="M 590 275 Q 680 275 680 340 L 610 375" stroke="#06b6d4" stroke-width="2" class="flow-line" />
  <text x="690" y="305" fill="#22d3ee" font-size="9" font-family="monospace">Cache HIT (&lt;0.01s)</text>

  <!-- 4B. Cache Miss (1.8s) to Cognitive Multi-Cloud Agent -->
  <path d="M 450 275 L 340 275" stroke="#f59e0b" stroke-width="2.5" class="flow-line" />
  <text x="395" y="265" fill="#f59e0b" font-size="9" font-weight="bold" text-anchor="middle">Cache MISS</text>

  <!-- 5. Multi-Cloud Agent to AST Sandbox -->
  <path d="M 265 310 L 265 375 L 470 375" stroke="#8b5cf6" stroke-width="2.5" class="flow-line" />

  <!-- 6A. AST Sandbox to Live Warehouse (Commit) -->
  <path d="M 590 375 L 810 375 L 810 175" stroke="#10b981" stroke-width="2.5" class="flow-line" />
  <text x="700" y="365" fill="#34d399" font-size="10" font-weight="bold">Auto-Healed</text>

  <!-- 6B. AST Sandbox to Dead Letter Queue (DLQ Quarantine) -->
  <path d="M 530 410 L 530 445 L 740 445" stroke="#f43f5e" stroke-width="2" class="flow-line" />
  <text x="620" y="440" fill="#f43f5e" font-size="9" font-weight="bold">Alien / Malicious</text>

  <!-- ==================== ARCHITECTURE NODES ==================== -->
  <!-- NODE 1: Ingress Stream -->
  <g transform="translate(40, 105)">
    <rect width="120" height="70" rx="10" fill="#090e1a" stroke="#10b981" stroke-width="1.5" />
    <text x="60" y="32" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Stream Ingress</text>
    <text x="60" y="48" fill="#64748b" font-size="9" font-family="monospace" text-anchor="middle">GitHub / Tavily</text>
    <text x="60" y="62" fill="#34d399" font-size="9" font-family="monospace" text-anchor="middle">Kafka Partitions</text>
  </g>

  <!-- NODE 2: Shannon Entropy Guard -->
  <g transform="translate(250, 105)">
    <rect width="130" height="70" rx="10" fill="#090e1a" stroke="#06b6d4" stroke-width="1.5" />
    <text x="65" y="32" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Entropy Guard</text>
    <text x="65" y="48" fill="#38bdf8" font-size="9" font-family="monospace" text-anchor="middle">H(x) ≥ 1.80 Guard</text>
    <text x="65" y="62" fill="#64748b" font-size="8" font-family="monospace" text-anchor="middle">0.1ms Noise Filter</text>
  </g>

  <!-- NODE 3: Contract Validator -->
  <g transform="translate(460, 105)">
    <rect width="120" height="70" rx="10" fill="#090e1a" stroke="#3b82f6" stroke-width="1.5" />
    <text x="60" y="32" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Contract Check</text>
    <text x="60" y="48" fill="#93c5fd" font-size="9" font-family="monospace" text-anchor="middle">SQLite DDL</text>
    <text x="60" y="62" fill="#64748b" font-size="8" font-family="monospace" text-anchor="middle">Strict Types</text>
  </g>

  <!-- NODE 4: Fingerprint Cache -->
  <g transform="translate(450, 240)">
    <rect width="140" height="70" rx="10" fill="#082f49" stroke="#06b6d4" stroke-width="2" />
    <text x="70" y="30" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">⚡ Fingerprint Cache</text>
    <text x="70" y="46" fill="#38bdf8" font-size="9" font-family="monospace" text-anchor="middle">Payload SHA-256 Sig</text>
    <text x="70" y="60" fill="#22d3ee" font-size="9" font-weight="600" text-anchor="middle">&lt;0.01s Bytecode HIT</text>
  </g>

  <!-- NODE 5: Cognitive Multi-Cloud Agent -->
  <g transform="translate(190, 240)">
    <rect width="150" height="70" rx="10" fill="#1e1b4b" stroke="#8b5cf6" stroke-width="2" />
    <text x="75" y="28" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">🧠 Multi-Cloud Agent</text>
    <text x="75" y="44" fill="#c084fc" font-size="9" font-weight="600" text-anchor="middle">Nebius Studio Qwen-30B</text>
    <text x="75" y="58" fill="#f59e0b" font-size="8" font-family="monospace" text-anchor="middle">AWS Bedrock Fallback</text>
  </g>

  <!-- NODE 6: AST Sandbox Gate -->
  <g transform="translate(470, 340)">
    <rect width="120" height="70" rx="10" fill="#090e1a" stroke="#10b981" stroke-width="2" />
    <text x="60" y="30" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">🔒 AST Sandbox</text>
    <text x="60" y="46" fill="#34d399" font-size="9" font-family="monospace" text-anchor="middle">Bytecode Analysis</text>
    <text x="60" y="60" fill="#64748b" font-size="8" font-family="monospace" text-anchor="middle">Blocks os/sys/eval</text>
  </g>

  <!-- TARGET 1: Live Relational Warehouse -->
  <g transform="translate(740, 105)">
    <rect width="140" height="70" rx="10" fill="#022c22" stroke="#10b981" stroke-width="2" />
    <text x="70" y="32" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">🗄️ tech_projects</text>
    <text x="70" y="48" fill="#34d399" font-size="9" font-family="monospace" text-anchor="middle">SQLite Warehouse</text>
    <text x="70" y="62" fill="#a7f3d0" font-size="8" font-family="monospace" text-anchor="middle">100% Zero Loss</text>
  </g>

  <!-- TARGET 2: Dead Letter Queue (DLQ Quarantine) -->
  <g transform="translate(740, 410)">
    <rect width="140" height="65" rx="10" fill="#4c0519" stroke="#f43f5e" stroke-width="1.5" />
    <text x="70" y="28" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">⚠️ Dead Letter Queue</text>
    <text x="70" y="44" fill="#fca5a5" font-size="8" font-family="monospace" text-anchor="middle">Zero Pollution Shield</text>
    <text x="70" y="56" fill="#fda4af" font-size="8" font-family="monospace" text-anchor="middle">Audit Logs Preserved</text>
  </g>
</svg>oading architecture-flow.svg…]()


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
```
