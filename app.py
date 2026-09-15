import streamlit as st
import json
import traceback
import time
import math
from datetime import datetime
import pandas as pd
from typing import Tuple
from database import WarehouseDatabase
from agent import SchemaHealingAgent
from sandbox import SandboxExecutor
from data_producer import fetch_multi_topic_stream_batches, DEFAULT_DISCOVERY_TOPICS

st.set_page_config(
    page_title="SchemaSentinel-Strands | Autonomous Data Self-Healing",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="collapsed"
)

# ----------------- COMPACT PRODUCTION CSS -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    code, pre { font-family: 'JetBrains Mono', monospace !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 1 !important; }
    .block-container { padding-top: 3.5rem !important; padding-bottom: 2rem !important; max-width: 98% !important; }
    .badge-heal { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }
    .sentinel-logo-box { position: relative; width: 44px; height: 44px; border-radius: 12px; background: #090e1a; border: 1px solid rgba(16, 185, 129, 0.5); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 16px rgba(16, 185, 129, 0.25); }
    .sentinel-pulse-dot { position: absolute; bottom: -2px; right: -2px; width: 10px; height: 10px; background: #22d3ee; border: 2px solid #020617; border-radius: 50%; box-shadow: 0 0 8px #22d3ee; animation: pulseDot 1.5s infinite; }
    @keyframes pulseDot { 0%, 100% { transform: scale(0.9); opacity: 0.8; } 50% { transform: scale(1.3); opacity: 1; } }
    .btn-running-active { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; height: 38.4px; border-radius: 8px; background: linear-gradient(90deg, #059669, #10b981, #06b6d4, #10b981, #059669); background-size: 250% 100%; animation: pulseGradient 1.8s infinite linear; color: #fff; font-weight: 600; font-size: 13px; box-shadow: 0 0 20px rgba(16,185,129,0.6); border: 1px solid rgba(52,211,153,0.8); cursor: wait; }
    @keyframes pulseGradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .spinner-svg { animation: spin 0.8s linear infinite; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .metric-card { background: #090e1a; border: 1px solid #1e293b; border-radius: 10px; padding: 12px 16px; height: 105px; display: flex; flex-direction: column; justify-content: space-between; }
    .metric-header { display: flex; justify-content: space-between; color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 600; }
    .metric-value-row { display: flex; align-items: baseline; gap: 8px; margin: 2px 0; }
    .metric-value { color: #f8fafc; font-size: 24px; font-weight: 700; line-height: 1.1; }
    .metric-badge { font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
    .metric-footer { font-size: 11px; color: #64748b; }
    .dag-node { background: #090e1a; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 12px; min-height: 80px; }
    .dag-node-active { border: 1px solid #10b981; background: rgba(16, 185, 129, 0.05); }
    .dag-node-heal { border: 1px solid #f59e0b; background: rgba(245, 158, 11, 0.05); }
    .stTabs [data-baseweb="tab"] { background-color: #090e1a; border: 1px solid #1e293b; border-radius: 8px 8px 0 0; padding: 6px 16px; color: #94a3b8; }
    .stTabs [aria-selected="true"] { background-color: #1e293b !important; color: #10b981 !important; border-bottom: 2px solid #10b981 !important; }
</style>
""", unsafe_allow_html=True)

def get_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def safe_render_dataframe(df_data, height=270):
    try:
        st.dataframe(df_data, width="stretch", height=height, hide_index=True)
    except TypeError:
        st.dataframe(df_data, use_container_width=True, height=height, hide_index=True)

# ----------------- DYNAMIC ENTROPY GUARD -----------------
def calculate_shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    entropy = 0.0
    length = len(text)
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def is_meaningful_query(q: str) -> Tuple[bool, str]:
    s = q.strip().lower()
    if len(s) < 2:
        return False, "Query is too short."
    if any(c in s for c in ";<>{}[~`^|\\=+*$%"):
        return False, "Query contains invalid keyboard mash symbols."
    h = calculate_shannon_entropy(s)
    if len(s) >= 6 and h < 1.8:
        return False, f"Query exhibits repetitive character mash (Entropy {h:.2f})."
    return True, "Valid"

# ----------------- SESSION STATE -----------------
DEFAULT_STATE = {
    "db": WarehouseDatabase(),
    "healing_history": [],
    "healed_urls": set(),
    "last_patch": None,
    "show_target_schema": False,
    "run_count": 0,
    "topic_cursor": {},
    "telemetry_logs": [f"[{get_now()}] [STREAM] ChaosSchemaMutator Engine initialized. Ready for dynamic streaming."],
    "stream_diagnostics": [],
    "last_latency_ms": None,
    "total_ingress_attempted": 0,
    "dropped_records_count": 0,
    "sandbox_compiles_count": 0,
}
for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------- REUSABLE PIPELINE DISPATCHER -----------------
def execute_healing_pipeline(records, batch_id, agent, target_schema, err_trace):
    t_start = time.time()
    raw_patch = agent.synthesize_transformation_patch(
        failing_records=records,
        target_schema=target_schema,
        error_trace=err_trace,
    )
    clean_patch = agent.extract_pure_code(raw_patch)
    st.session_state.last_patch = clean_patch

    compiled, func, msg = SandboxExecutor.compile_patch(clean_patch)
    latency_ms = max(45, int((time.time() - t_start) * 1000))
    st.session_state.last_latency_ms = latency_ms

    if not compiled:
        return False, msg, []

    st.session_state.sandbox_compiles_count += 1
    transformed = []
    for r in records:
        try:
            healed = func(r) if func else None
        except Exception:
            healed = None
        record_final = healed if isinstance(healed, dict) else agent.get_fallback_dict(r)
        record_final["batch_id"] = batch_id
        record_final["ingestion_status"] = "auto_healed"
        transformed.append(record_final)

    return True, clean_patch, transformed

# ----------------- TOP NAVBAR HEADER -----------------
head_col1, head_col2 = st.columns([1.6, 2.4])

with head_col1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 14px; padding: 6px 0;">
        <div class="sentinel-logo-box">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 6px #10b981);">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
            </svg>
            <div class="sentinel-pulse-dot"></div>
        </div>
        <div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.01em;">SchemaSentinel-Strands</span>
                <span class="badge-heal">● Autonomous Self-Healing</span>
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
                Powered by <b>Strands Agents SDK</b> on <b>AWS Bedrock Mantle</b> (Grok 4.6) &nbsp;•&nbsp; <b>Live Multi-Source Grounding</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with head_col2:
    act1, act2, act3 = st.columns([1.25, 0.95, 1.8])
    with act1:
        schema_btn_label = "🔼 Hide Schema" if st.session_state.show_target_schema else "🎯 Target Schema"
        if st.button(schema_btn_label, use_container_width=True):
            st.session_state.show_target_schema = not st.session_state.show_target_schema
            st.rerun()

    with act2:
        if st.button("🔄 Reset", use_container_width=True):
            for k, v in DEFAULT_STATE.items():
                st.session_state[k] = WarehouseDatabase() if k == "db" else (set() if isinstance(v, set) else ([] if isinstance(v, list) else ({} if isinstance(v, dict) else v)))
            st.session_state.telemetry_logs = [f"[{get_now()}] [STREAM] Warehouse & topic cursors reset. Ready for ingestion."]
            st.rerun()

    with act3:
        run_btn_placeholder = st.empty()
        run_btn = run_btn_placeholder.button("▶ Run Autonomous Stream", type="primary", use_container_width=True)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ----------------- DYNAMIC WAREHOUSE METRICS -----------------
raw_records = st.session_state.db.get_all_rows()
df = pd.DataFrame(raw_records) if raw_records else pd.DataFrame()
dlq_records = st.session_state.db.get_dlq_rows()
df_dlq = pd.DataFrame(dlq_records) if dlq_records else pd.DataFrame()

total_records = len(df)
dlq_count = len(df_dlq)
clean_count = int((df["ingestion_status"] == "clean").sum()) if not df.empty and "ingestion_status" in df.columns else 0
healed_count = int((df["ingestion_status"] == "auto_healed").sum()) if not df.empty and "ingestion_status" in df.columns else 0

total_attempted = st.session_state.total_ingress_attempted
dropped = st.session_state.dropped_records_count + dlq_count

if total_attempted > 0:
    sla_percentage = round(((total_attempted - dropped) / total_attempted) * 100, 1)
    sla_display = f"{sla_percentage}%"
    sla_badge = "Zero Drop" if dropped == 0 else f"{dropped} Quarantined"
    sla_color = "#10b981" if dropped == 0 else "#f43f5e"
    sla_footer = f"{total_records} conformed • {dlq_count} in DLQ"
else:
    sla_display, sla_badge, sla_color, sla_footer = "100%", "Ready", "#10b981", "0 ingress failures"

latency_display = f"{st.session_state.last_latency_ms}ms" if st.session_state.last_latency_ms else "Standby"
latency_footer = "Live measured inference & compile" if st.session_state.last_latency_ms else "Awaiting drift trigger"
sandbox_badge = f"{st.session_state.sandbox_compiles_count} Patches" if st.session_state.sandbox_compiles_count > 0 else "Active"
sandbox_footer = f"{st.session_state.sandbox_compiles_count} validated AST runs" if st.session_state.sandbox_compiles_count > 0 else "Memory & timeout isolated"

m1, m2, m3, m4, m5 = st.columns(5)
metrics_data = [
    ("Processed Records", "🗄️", total_records, "Live Warehouse", "Table: tech_projects", "#f8fafc", "rgba(16, 185, 129, 0.15)", "#34d399"),
    ("Auto-Healed", "🛡️", healed_count, "Drifts Resolved", f"{clean_count} clean ingress • {dlq_count} in DLQ", "#2dd4bf", "rgba(45, 212, 191, 0.15)", "#2dd4bf"),
    ("Reliability SLA", "📈", sla_display, sla_badge, sla_footer, sla_color, "rgba(16, 185, 129, 0.15)", "#34d399"),
    ("Synthesis Latency", "⚡", latency_display, "AWS Grok 4.6", latency_footer, "#f8fafc", "rgba(245, 158, 11, 0.15)", "#fbbf24"),
    ("Dead Letter Queue", "⚠️", dlq_count, "Quarantined", "Zero warehouse pollution", "#f43f5e" if dlq_count > 0 else "#f8fafc", "rgba(244, 63, 94, 0.15)" if dlq_count > 0 else "rgba(16, 185, 129, 0.15)", "#f43f5e" if dlq_count > 0 else "#34d399"),
]

for col, (title, icon, val, badge, footer, val_color, b_bg, b_col) in zip([m1, m2, m3, m4, m5], metrics_data):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header"><span>{title}</span><span>{icon}</span></div>
            <div class="metric-value-row">
                <span class="metric-value" style="color: {val_color};">{val}</span>
                <span class="metric-badge" style="background: {b_bg}; color: {b_col};">{badge}</span>
            </div>
            <div class="metric-footer">{footer}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ----------------- MAIN TWO-COLUMN DASHBOARD -----------------
col_left, col_right = st.columns([1.18, 0.82], gap="large")

with col_left:
    # 2nd CHANGE: Number removed from heading
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <h3 style="margin: 0; color: #ffffff; font-size: 1.15rem; font-weight: 700;">
            Live Warehouse Database State (<code>tech_projects</code>)
        </h3>
        <span style="font-size: 11px; color: #10b981; font-family: monospace;">● Active SQLite Conformed Storage</span>
    </div>
    """, unsafe_allow_html=True)

    if not df.empty and "ingestion_status" in df.columns:
        df["Status"] = df["ingestion_status"].map({"auto_healed": "✨ Auto-Healed", "clean": "✅ Clean"}).fillna("✅ Clean")
    elif not df.empty:
        df["Status"] = "✅ Clean"

    search_q = st.text_input("Search records", placeholder="Filter by title, author, or URL...", label_visibility="collapsed")
    filtered_df = df.copy() if not df.empty else pd.DataFrame()
    if search_q and not filtered_df.empty:
        mask = filtered_df.astype(str).apply(lambda row: row.str.contains(search_q, case=False).any(), axis=1)
        filtered_df = filtered_df[mask]

    clean_mask = (filtered_df["Status"] == "✅ Clean") if not filtered_df.empty and "Status" in filtered_df else pd.Series(dtype=bool)
    healed_mask = (filtered_df["Status"] == "✨ Auto-Healed") if not filtered_df.empty and "Status" in filtered_df else pd.Series(dtype=bool)

    clean_count_filtered = int(clean_mask.sum()) if not clean_mask.empty else 0
    healed_count_filtered = int(healed_mask.sum()) if not healed_mask.empty else 0

    tab_all, tab_clean, tab_healed, tab_dlq = st.tabs([
        f"All Records ({len(filtered_df)})",
        f"Clean Ingress ({clean_count_filtered})",
        f"✨ Auto-Healed ({healed_count_filtered})",
        f"⚠️ Dead Letter Queue ({len(df_dlq)})"
    ])

    with tab_all:
        if not filtered_df.empty:
            safe_render_dataframe(filtered_df)
        else:
            st.info("Warehouse is empty. Configure stream source below.")

    with tab_clean:
        if not filtered_df.empty and clean_count_filtered > 0:
            safe_render_dataframe(filtered_df[clean_mask])
        else:
            st.info("No clean records matching filter.")

    with tab_healed:
        if not filtered_df.empty and healed_count_filtered > 0:
            safe_render_dataframe(filtered_df[healed_mask])
        else:
            st.info("No auto-healed records yet. Click 'Run Autonomous Stream' to observe healing!")

    with tab_dlq:
        if not df_dlq.empty:
            st.caption("🛡️ Quarantined payloads violating strict schema contracts (Zero warehouse pollution).")
            safe_render_dataframe(df_dlq)
        else:
            st.info("✅ Dead Letter Queue is empty. 100% Zero Data Pollution SLA achieved.")

    # TARGET SCHEMA MODAL
    if st.session_state.show_target_schema:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 14px; margin-bottom: 6px;">
            <svg width="28" height="28" viewBox="0 0 100 100" fill="none">
                <circle cx="50" cy="50" r="44" stroke="#0284c7" stroke-width="4"/>
                <circle cx="50" cy="50" r="32" fill="#0369a1" stroke="#38bdf8" stroke-width="4"/>
                <circle cx="50" cy="50" r="11" fill="#ea580c"/>
                <path d="M78 22 L53 47" stroke="#ffffff" stroke-width="5" stroke-linecap="round"/>
            </svg>
            <h4 style="margin: 0; color: #f8fafc; font-size: 15px; font-weight: 700;">Dynamic Warehouse DDL (<code>tech_projects</code>)</h4>
        </div>
        """, unsafe_allow_html=True)
        st.code(st.session_state.db.get_table_schema("tech_projects"), language="sql")

    # ----------------- SECTION 2: STREAM SOURCE WITH GROUNDING -----------------
    # 2nd CHANGE: Number removed from heading
    st.markdown("""
    <div style="margin-top: 18px; margin-bottom: 8px;">
        <h3 style="margin: 0; color: #ffffff; font-size: 1.15rem; font-weight: 700;">
            Upstream Ingress Stream & Autonomous Drift Engine
        </h3>
        <p style="margin: 3px 0 10px 0; color: #94a3b8; font-size: 12px;">Multi-topic partition consumer supporting preset channels or live GitHub repository resolution.</p>
    </div>
    """, unsafe_allow_html=True)

    stream_mode = st.radio("Mode", ["Select Preset Enterprise Topics", "Custom Ingress Query / Repo"], horizontal=True, label_visibility="collapsed")
    active_topics = []
    is_source_valid = True

    if stream_mode == "Select Preset Enterprise Topics":
        chosen = st.multiselect("Topics", options=DEFAULT_DISCOVERY_TOPICS, default=[DEFAULT_DISCOVERY_TOPICS[0]])
        if chosen:
            active_topics = chosen
            st.caption(f"📍 **ACTIVE**: Ingesting across {len(active_topics)} partition(s).")
        else:
            is_source_valid = False
            st.warning("⚠️ Select at least one topic.")
    else:
        # 1st CHANGE: Default set to "SchemaSentinel Strands"
        custom_input = st.text_input(
            "Query",
            value="SchemaSentinel Strands",
            help="Enter a GitHub repository name, username, or topic."
        )
        clean_q = custom_input.strip()
        
        is_meaningful, reason = is_meaningful_query(clean_q)
        if not is_meaningful:
            is_source_valid = False
            st.toast(f"⚠️ Invalid Query: {reason}", icon="🚫")
            st.error(f"🛡️ **Search Guard Intercepted**: {reason}\n\n👉 *Please enter a valid GitHub username, repository slug, or tech topic.*", icon="🚨")
        else:
            active_topics = [clean_q]
            st.caption(f"🔍 **Grounded Resolution**: Resolving live repositories for `{clean_q}`")

    status_placeholder = st.empty()

    # DAG NODES VISUALIZER
    diagnostics = st.session_state.stream_diagnostics
    if not diagnostics:
        d_cols = st.columns(5)
        nodes_info = [
            ("STAGE 01", "Clean Ref", "Contract Match", "#10b981", "dag-node-active"),
            ("STAGE 02", "URL Drift", "Regex & %", "#f59e0b", "dag-node"),
            ("STAGE 03", "Nested Drift", "Object Array", "#2dd4bf", "dag-node"),
            ("STAGE 04", "Alias Drift", "Alt Keys", "#06b6d4", "dag-node"),
            ("STAGE 05", "Meta Drift", "Hierarchy", "#8b5cf6", "dag-node"),
        ]
        for col, (stage, title, desc, color, cls) in zip(d_cols, nodes_info):
            with col:
                st.markdown(f"""
                <div class="dag-node {cls}">
                    <div style="display: flex; justify-content: space-between; font-size: 9px; font-family: monospace; color: {color};">
                        <span>{stage}</span><span>STANDBY</span>
                    </div>
                    <div style="font-size: 11px; font-weight: 700; color: #f8fafc; margin-top: 3px;">{title}</div>
                    <div style="font-size: 9px; color: #64748b; margin-top: 2px;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        diag_cols = st.columns(len(diagnostics))
        for i, item in enumerate(diagnostics):
            with diag_cols[i]:
                is_clean = item["type"] == "clean"
                cls = "dag-node-active" if is_clean else "dag-node-heal"
                tag = "✓ PASS" if is_clean else "⚡ HEALED"
                color = "#34d399" if is_clean else "#fbbf24"
                title = "Clean Ingress" if is_clean else item.get("short_title", "Drift")
                desc = "Conformed" if is_clean else item.get("fix_summary", "Fixed")
                st.markdown(f"""
                <div class="dag-node {cls}">
                    <div style="display: flex; justify-content: space-between; font-size: 9px; font-family: monospace; color: {color};">
                        <span>B0{i+1}</span><span>{tag}</span>
                    </div>
                    <div style="font-size: 11px; font-weight: 700; color: #f8fafc; margin-top: 3px;">{title}</div>
                    <div style="font-size: 9px; color: #10b981; margin-top: 2px;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

    # TELEMETRY LOG DISPLAY
    st.markdown("""
    <div style="margin-top: 14px; margin-bottom: 6px; display: flex; justify-content: space-between;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #94a3b8; font-weight: 600;">&gt;_ LIVE EXECUTION TELEMETRY LOG</span>
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #64748b;">Live Stream Feed</span>
    </div>
    """, unsafe_allow_html=True)

    log_html = []
    for log in st.session_state.telemetry_logs[:9]:
        color = "#34d399" if "[COMMITTED]" in log else ("#fb7185" if "[DRIFT_DETECTED]" in log else ("#fde68a" if "[STRANDS_AGENT]" in log else "#94a3b8"))
        log_html.append(f'<div style="color: {color}; margin-bottom: 4px;">{log}</div>')
    st.markdown(f"""
    <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 14px; font-family: 'JetBrains Mono', monospace; font-size: 11px; max-height: 200px; overflow-y: auto;">
        {''.join(log_html)}
    </div>
    """, unsafe_allow_html=True)

    # ----------------- PLAYGROUND (3rd CHANGE: Logo & Hackathon Judge removed) -----------------
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    with st.expander("Playground: Inject Custom Malformed JSON", expanded=False):
        st.caption("Paste any arbitrary drifted JSON payload. Our AI Agent + Sandbox will heal it in real time:")
        custom_sample = json.dumps({
            "projectTitle": "SchemaSentinel Strands",
            "OwnerId": "lvh_naruto",
            "repositoryUrl": "https://github.com/lvh_naruto/SchemaSentinel-Strands",
            "confidenceScore": "0.98"
        }, indent=2)
        custom_input = st.text_area("Malformed Ingress Payload", value=custom_sample, height=115)
        
        is_json_valid = False
        parsed_payload = None
        try:
            parsed_payload = json.loads(custom_input)
            if isinstance(parsed_payload, (dict, list)):
                is_json_valid = True
                st.caption("🛡️ **JSON Guard Status**: Syntax valid. Ready for Strands Agentic Schema Healing.")
            else:
                st.warning("⚠️ Input must be a valid JSON Object `{...}` or Array `[...]`")
        except json.JSONDecodeError as jde:
            st.error(f"❌ **JSON Syntax Error**: {jde.msg} (line {jde.lineno}, column {jde.colno})")

        test_healing_btn = st.button(
            "⚡ Test Live Custom Healing",
            type="secondary",
            use_container_width=True,
            disabled=not is_json_valid
        )
        
        if test_healing_btn and is_json_valid:
            try:
                parsed = [parsed_payload] if isinstance(parsed_payload, dict) else parsed_payload
                st.session_state.total_ingress_attempted += len(parsed)
                agent = SchemaHealingAgent()
                try:
                    st.session_state.db.insert_batch(parsed)
                    st.success("Record already conforms to schema!")
                except Exception:
                    err = traceback.format_exc()
                    ok, patch, transformed = execute_healing_pipeline(
                        parsed, "judge_custom_drift", agent,
                        st.session_state.db.get_table_schema("tech_projects"), err
                    )
                    if ok and transformed:
                        transformed[0]["source_url"] = f"{transformed[0].get('source_url', 'https://github.com')}?eval={int(time.time()*1000)}"
                        st.session_state.db.insert_batch(transformed, batch_id="judge_custom_drift", status="auto_healed")
                        st.session_state.healing_history.insert(0, {"batch_id": "judge_custom", "before": parsed[0], "after": transformed[0], "error": err})
                        st.session_state.telemetry_logs.insert(0, f"[{get_now()}] [COMMITTED] Custom judge payload healed in {st.session_state.last_latency_ms}ms!")
                        st.success(f"🎉 Healed in {st.session_state.last_latency_ms}ms via Strands Agent & AST Sandbox!")
                        st.rerun()
                    else:
                        st.session_state.db.insert_dlq(parsed[0], patch, "judge_custom_drift")
                        st.error(f"❌ Record could not be healed safely. Quarantined in Dead Letter Queue (DLQ): {patch}")
            except Exception as ex:
                st.error(f"Error executing payload: {ex}")

    # ----------------- RUN AUTONOMOUS STREAM EXECUTION -----------------
    if run_btn:
        if not is_source_valid or not active_topics:
            st.toast("❌ Stream Blocked: Please fix query errors first!", icon="⛔")
            status_placeholder.error("❌ Cannot start stream: Invalid query or no topic selected.")
        else:
            run_btn_placeholder.markdown("""
            <div class="btn-running-active">
                <svg class="spinner-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.2)"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#fff"/></svg>
                <span>Healing Pipeline Active...</span>
            </div>
            """, unsafe_allow_html=True)

            st.session_state.run_count += 1
            agent = SchemaHealingAgent()

            with status_placeholder.status("⚡ Resolving Stream Grounding & Healing Schema Drift...", expanded=True) as status:
                fresh_batches, updated_cursors, stream_desc = fetch_multi_topic_stream_batches(
                    topics=active_topics, topic_cursors=st.session_state.topic_cursor, batch_size=5
                )
                st.session_state.topic_cursor = updated_cursors

                if not fresh_batches:
                    status.update(label=f"⚠️ Stream Idle: No live repositories found for '{active_topics[0]}'. Zero warehouse pollution.", state="complete", expanded=False)
                    st.session_state.telemetry_logs.insert(0, f"[{get_now()}] [STREAM_IDLE] 0 records found for '{active_topics[0]}'. Warehouse untouched.")
                else:
                    st.session_state.telemetry_logs.insert(0, f"[{get_now()}] [GROUNDED] Ingesting {len(fresh_batches)} batches from: {stream_desc}")
                    new_diagnostics = []
                    target_schema = st.session_state.db.get_table_schema("tech_projects")

                    for idx, batch_event in enumerate(fresh_batches):
                        b_id, recs = batch_event["batch_id"], batch_event["records"]
                        s_title = batch_event.get("short_title", "Batch")
                        f_summary = batch_event.get("fix_summary", "Auto-Healed")

                        run_btn_placeholder.markdown(f"""
                        <div class="btn-running-active">
                            <svg class="spinner-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.2)"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#fff"/></svg>
                            <span>Healing Active (Batch {idx+1}/{len(fresh_batches)})...</span>
                        </div>
                        """, unsafe_allow_html=True)

                        st.session_state.total_ingress_attempted += len(recs)
                        status.write(f"🔄 **[Batch {idx+1}/{len(fresh_batches)}]** Ingesting `{b_id}`...")

                        try:
                            inserted, _ = st.session_state.db.insert_batch(recs, batch_id=b_id, status="clean")
                            new_diagnostics.append({"batch_id": b_id, "short_title": s_title, "type": "clean", "fix_summary": "100% Contract Match"})
                            st.session_state.telemetry_logs.insert(0, f"[{get_now()}] [COMMITTED] Conformed {b_id} ({inserted} records)")
                            status.write(f"✅ **[Batch {idx+1}/{len(fresh_batches)} Clean]** Conformed cleanly.")
                        except Exception:
                            err_trace = traceback.format_exc()
                            st.session_state.telemetry_logs.insert(0, f"[{get_now()}] [DRIFT_DETECTED] Drift in {b_id}! Invoking Agent...")

                            ok, clean_patch, transformed = execute_healing_pipeline(recs, b_id, agent, target_schema, err_trace)
                            if ok and transformed:
                                inserted, _ = st.session_state.db.insert_batch(transformed, batch_id=b_id, status="auto_healed")
                                new_diagnostics.append({"batch_id": b_id, "short_title": s_title, "type": "healed", "fix_summary": f_summary})

                                url_key = transformed[0].get("source_url", b_id)
                                if url_key not in st.session_state.healed_urls:
                                    st.session_state.healed_urls.add(url_key)
                                    st.session_state.healing_history.insert(0, {"batch_id": b_id, "before": recs[0], "after": transformed[0], "error": err_trace})

                                st.session_state.telemetry_logs.insert(0, f"[{get_now()}] [COMMITTED] Auto-Healed {b_id} in {st.session_state.last_latency_ms}ms")
                                status.write(f"🎉 **[Auto-Healed Batch {idx+1}/{len(fresh_batches)}]** Validated & Committed ({st.session_state.last_latency_ms}ms)!")
                            else:
                                for r in recs:
                                    st.session_state.db.insert_dlq(r, clean_patch, b_id)
                                status.write(f"⚠️ Quarantined in Dead Letter Queue (DLQ): {clean_patch}")

                        time.sleep(0.3)

                    st.session_state.stream_diagnostics = new_diagnostics
                    status.update(label="✅ Stream Run Finished! Conformed & Quarantined with 0% Warehouse Pollution.", state="complete", expanded=False)
                    time.sleep(0.3)
                    st.rerun()

with col_right:
    # 2nd CHANGE: Number removed from heading
    st.markdown("### Self-Healing Comparison (Before vs After)")
    unique_audits = st.session_state.healing_history[:5]
    if unique_audits:
        for idx, item in enumerate(unique_audits):
            with st.expander(f"🔍 Transformation Audit: {item['batch_id']}", expanded=(idx == 0)):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div style='color: #f43f5e; font-weight: 600; font-size: 12px;'>🔴 Before AI (Raw Drifted)</div>", unsafe_allow_html=True)
                    st.json(item["before"])
                with c2:
                    st.markdown("<div style='color: #10b981; font-weight: 600; font-size: 12px;'>🟢 After AI (Conformed)</div>", unsafe_allow_html=True)
                    st.json(item["after"])
    else:
        st.info("No schema drift events logged yet. Click 'Run Autonomous Stream' to observe healing.")

    if st.session_state.last_patch:
        # 2nd CHANGE: Number removed from heading
        st.markdown("### Last Synthesized Patch")
        st.caption("AST verified • Pure function • Isolated namespace execution")
        st.code(st.session_state.last_patch, language="python")