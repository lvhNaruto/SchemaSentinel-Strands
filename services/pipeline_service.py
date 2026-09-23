"""
Pipeline Service — extracted from the former Streamlit presentation layer (app.py).
All domain behavior preserved: ingress -> drift detection -> Strands agent synthesis ->
AST sandbox -> warehouse commit / DLQ quarantine. No backend logic was reinvented;
this module orchestrates the same existing modules (database, agent, sandbox, data_producer).
"""
import threading
import time
import traceback
import math
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from database import WarehouseDatabase
from agent import SchemaHealingAgent
from sandbox import SandboxExecutor
from data_producer import fetch_multi_topic_stream_batches, DEFAULT_DISCOVERY_TOPICS
from score_contract import get_valid_score_keys, get_raw_metric_score_keys


def get_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ----------------- DYNAMIC ENTROPY GUARD (verbatim from app.py) -----------------
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


class SentinelService:
    """Thread-safe singleton that holds the state which previously lived in
    Streamlit session_state, plus the extracted pipeline orchestration."""

    MAX_EVENTS = 500

    def __init__(self):
        self.lock = threading.RLock()
        self.db = WarehouseDatabase()
        self.agent = SchemaHealingAgent()
        self.healing_history: List[Dict[str, Any]] = []
        self.healed_urls: set = set()
        self.last_patch: Optional[str] = None
        self.last_latency_ms: Optional[int] = None
        self.last_ast_ok: Optional[bool] = None
        self.last_ast_msg: Optional[str] = None
        self.run_count = 0
        self.topic_cursor: Dict[str, int] = {}
        self.total_ingress_attempted = 0
        self.dropped_records_count = 0
        self.sandbox_compiles_count = 0
        self.events: List[Dict[str, Any]] = []  # ascending, id-ordered, ring-capped
        self.pipeline_stage: Optional[str] = None
        self.dlq_active = False
        self.running = False
        self.fingerprints: Dict[str, Dict[str, Any]] = {}
        self._event_id = 0

    # ----------------- telemetry event bus -----------------
    def _emit(self, tag: str, message: str) -> Dict[str, Any]:
        with self.lock:
            self._event_id += 1
            ev = {
                "id": self._event_id,
                "ts": get_now(),
                "tag": tag,
                "message": message,
                "stage": self.pipeline_stage,
                "dlq_active": self.dlq_active,
            }
            self.events.append(ev)
            if len(self.events) > self.MAX_EVENTS:
                del self.events[:-self.MAX_EVENTS]
        return ev

    def events_since(self, last_id: int) -> List[Dict[str, Any]]:
        with self.lock:
            return [e for e in self.events if e["id"] > last_id]

    def telemetry(self, limit: int = 60) -> List[Dict[str, Any]]:
        with self.lock:
            return list(reversed(self.events[-limit:]))

    def _set_stage(self, stage: Optional[str], dlq: bool = False):
        with self.lock:
            self.pipeline_stage = stage
            self.dlq_active = dlq

    # ----------------- fingerprint registry (tracking only) -----------------
    def _register_fingerprint(self, record: Dict[str, Any], label: str = "") -> str:
        sig = self.agent.compute_schema_signature(record)
        with self.lock:
            entry = self.fingerprints.get(sig)
            if entry is None:
                self.fingerprints[sig] = {
                    "signature": sig,
                    "label": label or sig,
                    "first_seen": get_now(),
                    "last_seen": get_now(),
                    "occurrences": 1,
                }
            else:
                entry["occurrences"] += 1
                entry["last_seen"] = get_now()
        return sig

    # ----------------- reset -----------------
    def reset(self, clear_warehouse: bool = True) -> Dict[str, Any]:
        with self.lock:
            if self.running:
                return {"ok": False, "error": "Pipeline is running"}
            if clear_warehouse:
                self.db.clear_all()
            self.db = WarehouseDatabase()
            self.healing_history = []
            self.healed_urls = set()
            self.last_patch = None
            self.last_latency_ms = None
            self.last_ast_ok = None
            self.last_ast_msg = None
            self.topic_cursor = {}
            self.total_ingress_attempted = 0
            self.dropped_records_count = 0
            self.sandbox_compiles_count = 0
            self.pipeline_stage = None
            self.dlq_active = False
            self.fingerprints = {}
            # telemetry kept as an append-only log; emit the reset marker
        self._emit("SYSTEM", "Warehouse, DLQ & topic cursors reset. Engine re-armed for ingestion." if clear_warehouse
                   else "Session state reset. Warehouse rows preserved (legacy mode).")
        return {"ok": True}

    # ----------------- healing dispatcher (verbatim control flow from app.py) -----------------
    def execute_healing(self, records: List[Dict[str, Any]], batch_id: str,
                        target_schema: str, err_trace: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        t_start = time.time()
        sig = self.agent.compute_schema_signature(records[0])

        cached = self.db.get_template(sig)
        if cached:
            clean_patch = cached["patch_code"]
            source = "cache"
            self._emit("STRANDS_AGENT", f"Cache hit for signature `{sig}` — skipping LLM synthesis.")
            with self.lock:
                self.last_patch = clean_patch
        else:
            raw_patch = self.agent.synthesize_transformation_patch(
                failing_records=records,
                target_schema=target_schema,
                error_trace=err_trace,
            )
            clean_patch = self.agent.extract_pure_code(raw_patch)
            source = "llm"
            self._emit("STRANDS_AGENT", f"Cache miss for signature `{sig}` — invoking LLM patch synthesis.")
            with self.lock:
                self.last_patch = clean_patch

        compiled, func, msg = SandboxExecutor.compile_patch(clean_patch)
        latency_ms = max(45, int((time.time() - t_start) * 1000))
        with self.lock:
            self.last_latency_ms = latency_ms
            self.last_ast_ok = bool(compiled)
            self.last_ast_msg = msg
            if compiled:
                self.sandbox_compiles_count += 1

        if not compiled:
            return False, msg, []

        transformed = self._apply_transform(func, records, batch_id)

        if transformed:
            if source == "llm":
                self.db.save_template(sig, clean_patch, records[0])
            elif source == "cache":
                self.db.increment_template_usage(sig)

        return (True, clean_patch, transformed) if transformed else (False, "Transformation produced no conforming records", [])

    def _apply_transform(self, func: Callable[[Dict[str, Any]], Dict[str, Any]],
                         records: List[Dict[str, Any]], batch_id: str) -> List[Dict[str, Any]]:
        """Execute a compiled transformation function against a batch of drifted records."""
        fallback_fn = getattr(self.agent, "get_fallback_dict", None)  # legacy UI call; absent on current agent
        quarantine_signal = "IRRECOVERABLE_SCHEMA_DRIFT"
        transformed = []
        for r in records:
            try:
                healed = func(r) if func else None
            except ValueError as ve:
                if quarantine_signal in str(ve):
                    with self.lock:
                        self.last_ast_msg = str(ve)
                    return []  # signal quarantine to caller
                healed = None
            except Exception:
                healed = None

            record_final = healed if isinstance(healed, dict) else (fallback_fn(r) if callable(fallback_fn) else None)
            if record_final is None:
                continue  # Zero-Crash Shield: unhealable record routed to DLQ by caller
            self._normalize_relevance_score(record_final, r)
            if not self._is_conformed_record(record_final):
                continue  # Patch did not produce a valid warehouse record
            record_final["batch_id"] = batch_id
            record_final["ingestion_status"] = "auto_healed"
            self._attach_extra_metadata(record_final, r)
            transformed.append(record_final)

        return transformed

    def _is_conformed_record(self, r: Dict[str, Any]) -> bool:
        """Verify the transformed record satisfies the warehouse NOT-NULL contract."""
        try:
            return bool(
                r.get("title") and str(r["title"]).strip()
                and r.get("author") and str(r["author"]).strip()
                and r.get("source_url") and str(r["source_url"]).strip()
                and r.get("relevance_score") is not None
                and 0 <= int(r["relevance_score"]) <= 100
            )
        except Exception:
            return False

    def _normalize_relevance_score(self, record: Dict[str, Any], original: Dict[str, Any]) -> None:
        """Enforce the score-source contract even if the synthesized patch ignores it.
        Only values from explicit score keys or from raw_metrics sub-keys may drive
        relevance_score. Raw star/fork/watcher counts and free-text words force a
        default of 0 and the raw value is preserved in extra_metadata.
        """
        import json
        VALID_SCORE_KEYS = get_valid_score_keys()
        RAW_METRIC_SCORE_KEYS = get_raw_metric_score_keys()
        has_valid_source = any(k in VALID_SCORE_KEYS for k in original.keys())
        if not has_valid_source:
            raw_metrics = original.get("raw_metrics")
            if isinstance(raw_metrics, dict):
                has_valid_source = any(k in RAW_METRIC_SCORE_KEYS for k in raw_metrics.keys())
        if not has_valid_source:
            current = record.get("relevance_score")
            if current not in (0, 0.0, None):
                extra = {}
                existing = record.get("extra_metadata")
                if isinstance(existing, str) and existing:
                    try:
                        extra = json.loads(existing) or {}
                    except Exception:
                        pass
                extra["agent_rejected_relevance_score"] = current
                record["extra_metadata"] = json.dumps(extra)
            record["relevance_score"] = 0
        else:
            try:
                record["relevance_score"] = max(0, min(100, int(round(float(record.get("relevance_score", 0))))))
            except (TypeError, ValueError):
                record["relevance_score"] = 0

    # ----------------- autonomous stream run -----------------

    def _wrapper_values_consumed(self, wrapper: Any, record: Dict[str, Any]) -> bool:
        """Return True if every value inside a wrapper dict is already represented
        by a core field in the conformed record. This lets us drop flattened
        wrappers such as `metadata` instead of duplicating them in extra_metadata."""
        if not isinstance(wrapper, dict):
            return False
        core_values: set = set()
        for key in ("title", "author"):
            v = record.get(key)
            if v is not None:
                core_values.add(str(v))
        source_url = record.get("source_url")
        if source_url is not None:
            core_values.add(str(source_url).split("?", 1)[0])
        relevance = record.get("relevance_score")
        if relevance is not None:
            core_values.add(str(relevance))
        for v in wrapper.values():
            candidate = str(v).split("?", 1)[0] if isinstance(v, str) else str(v)
            if candidate not in core_values:
                return False
        return True

    def _attach_extra_metadata(self, record: Dict[str, Any], original: Dict[str, Any]) -> None:
        """Preserve every unmapped key from the original payload in extra_metadata.
        Also snapshot any unparseable core-field value (e.g. 'ten %') so nothing is lost.
        Fully-consumed wrapper objects (e.g. `metadata` whose nested fields were all
        mapped to core fields) are dropped to avoid redundant side-car data."""
        import json
        core = {"title", "author", "source_url", "relevance_score"}
        meta = {"project_id", "batch_id", "ingestion_status", "created_at", "extra_metadata"}
        unmapped = {k: v for k, v in original.items() if k not in core and k not in meta}

        # Drop wrapper objects whose contents are already represented by core fields.
        for k in list(unmapped.keys()):
            if self._wrapper_values_consumed(unmapped[k], record):
                del unmapped[k]

        # Snapshot the original relevance_score if it could not be parsed into a number.
        orig_score = original.get("relevance_score")
        if isinstance(orig_score, str):
            parsed = None
            s = orig_score.strip()
            if s.endswith("%"):
                try:
                    parsed = float(s[:-1])
                except ValueError:
                    pass
            else:
                try:
                    parsed = float(s)
                except ValueError:
                    pass
            if parsed is None:
                unmapped["original_relevance_score"] = orig_score

        if not unmapped:
            return
        existing = {}
        extra = record.get("extra_metadata")
        if isinstance(extra, str) and extra:
            try:
                existing = json.loads(extra) if json.loads(extra) else {}
            except Exception:
                pass
        existing.update(unmapped)
        record["extra_metadata"] = json.dumps(existing)
    def run_pipeline(self, topics: List[str]) -> Tuple[bool, str]:
        with self.lock:
            if self.running:
                return False, "Pipeline already running"
            self.running = True
            self.run_count += 1
        t = threading.Thread(target=self._run_stream, args=(list(topics),), daemon=True)
        t.start()
        return True, "started"

    def _run_stream(self, topics: List[str]):
        try:
            self._set_stage("ingress")
            self._emit("INGRESS", f"Resolving stream grounding across {len(topics)} partition(s)...")
            fresh_batches, updated_cursors, stream_desc = fetch_multi_topic_stream_batches(
                topics=topics, topic_cursors=self.topic_cursor, batch_size=5
            )
            with self.lock:
                self.topic_cursor = updated_cursors

            if not fresh_batches:
                self._emit("STREAM_IDLE", f"0 records found for '{topics[0]}'. Warehouse untouched.")
                self._set_stage(None)
                return

            self._emit("INGRESS", f"Ingesting {len(fresh_batches)} batches from: {stream_desc}")
            target_schema = self.db.get_table_schema("tech_projects")

            for idx, batch_event in enumerate(fresh_batches):
                b_id = batch_event["batch_id"]
                recs = batch_event["records"]
                s_title = batch_event.get("short_title", "Batch")
                with self.lock:
                    self.total_ingress_attempted += len(recs)

                self._set_stage("fingerprint")
                sig = self._register_fingerprint(recs[0], s_title)
                self._emit("INGRESS", f"Batch {idx+1}/{len(fresh_batches)} `{b_id}` ingesting ({s_title})")

                self._set_stage("drift")
                try:
                    inserted, _ = self.db.insert_batch(recs, batch_id=b_id, status="clean")
                    self._set_stage("warehouse")
                    self._emit("COMMITTED", f"Conformed {b_id} ({inserted} records) — 100% contract match")
                except Exception:
                    err_trace = traceback.format_exc()
                    self._emit("DRIFT_DETECTED", f"Drift in {b_id}! Invoking Strands Agent...")
                    self._set_stage("agent")

                    ok, clean_patch, transformed = False, "", []
                    try:
                        ok, clean_patch, transformed = self.execute_healing(recs, b_id, target_schema, err_trace)
                    except Exception as synth_err:
                        clean_patch = f"Agentic Synthesis Failure: {synth_err}"
                        with self.lock:
                            self.last_ast_ok = False
                            self.last_ast_msg = clean_patch

                    self._set_stage("ast")
                    if ok and transformed:
                        self._emit("AST_VERIFIED", "Patch compiled safely in isolated namespace.")
                        self._set_stage("warehouse")
                        inserted, _ = self.db.insert_batch(transformed, batch_id=b_id, status="auto_healed")
                        url_key = transformed[0].get("source_url", b_id)
                        with self.lock:
                            if url_key not in self.healed_urls:
                                self.healed_urls.add(url_key)
                                self.healing_history.insert(0, {
                                    "batch_id": b_id, "before": recs[0], "after": transformed[0],
                                    "error": err_trace, "patch": clean_patch, "signature": sig,
                                    "latency_ms": self.last_latency_ms, "ast_verified": True, "ts": get_now(),
                                })
                            latency = self.last_latency_ms
                        self._emit("COMMITTED", f"Auto-Healed {b_id} in {latency/1000:.1f}s — validated & committed")
                    else:
                        self._set_stage("drift", dlq=True)
                        detected_keys = ", ".join(str(k) for k in recs[0].keys())
                        for r in recs:
                            self.db.insert_dlq(r, clean_patch, b_id, detected_keys=detected_keys)
                        self._emit("DLQ_QUARANTINED", f"{b_id} quarantined — irrecoverable shape. Warehouse protected.")

                time.sleep(0.3)

            self._set_stage("warehouse")
            self._emit("SYSTEM", "Stream run finished. Conformed & quarantined with 0% warehouse pollution.")
        except Exception as ex:
            self._emit("SYSTEM", f"Pipeline error: {ex}")
        finally:
            with self.lock:
                self.running = False

    # ----------------- judge playground (verbatim control flow from app.py) -----------------
    def test_payload(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            parsed = [payload]
        elif isinstance(payload, list):
            parsed = list(payload)
        else:
            return {"status": "invalid", "reason": "Payload must be a JSON object or array."}

        with self.lock:
            self.total_ingress_attempted += len(parsed)

        before = parsed[0]
        sig = self._register_fingerprint(before, "judge_playground")

        try:
            self.db.insert_batch(parsed)
            self._emit("COMMITTED", "Playground payload conformed natively to the warehouse contract.")
            return {"status": "clean", "before": before, "after": before,
                    "signature": sig, "reason": "Record already conforms to schema."}
        except Exception:
            err_trace = traceback.format_exc()
            self._emit("DRIFT_DETECTED", "Judge playground drift detected! Invoking Strands Agent...")

            ok, patch, transformed = False, "", []
            try:
                ok, patch, transformed = self.execute_healing(
                    parsed, "judge_custom_drift", self.db.get_table_schema("tech_projects"), err_trace
                )
            except Exception as synth_err:
                patch = f"Agentic Synthesis Failure: {synth_err}"

            if ok and transformed:
                transformed[0]["source_url"] = f"{transformed[0].get('source_url', 'https://github.com')}?eval={int(time.time()*1000)}"
                inserted, _ = self.db.insert_batch(transformed, batch_id="judge_custom_drift", status="auto_healed")
                with self.lock:
                    self.healing_history.insert(0, {
                        "batch_id": "judge_custom_drift", "before": before, "after": transformed[0],
                        "error": err_trace, "patch": patch, "signature": sig,
                        "latency_ms": self.last_latency_ms, "ast_verified": True, "ts": get_now(),
                    })
                    latency = self.last_latency_ms
                self._emit("AST_VERIFIED", "Playground patch compiled safely in isolated namespace.")
                self._emit("COMMITTED", f"Playground payload healed in {latency/1000:.1f}s via Strands Agent & AST Sandbox.")
                return {"status": "healed", "before": before, "after": transformed[0],
                        "patch": patch, "signature": sig, "latency_ms": latency,
                        "ast_verified": True, "reason": "Healed and committed as auto_healed."}
            else:
                detected_keys = ", ".join(str(k) for k in parsed[0].keys())
                self.db.insert_dlq(parsed[0], patch, "judge_custom_drift", detected_keys=detected_keys)
                self._emit("DLQ_QUARANTINED", "Playground payload quarantined — irrecoverable shape. Warehouse protected.")
                return {"status": "quarantined", "before": before, "reason": patch,
                        "signature": sig, "ast_verified": False}

    # ----------------- state snapshot (same metric formulas as app.py) -----------------
    def ast_checks(self) -> List[Dict[str, str]]:
        banned_mods = ", ".join(sorted(SandboxExecutor.BANNED_MODULES))
        banned_calls = ", ".join(sorted({"eval", "exec", "__import__", "compile", "open"}))
        return [
            {"name": "Banned module imports", "detail": f"Blocks: {banned_mods}"},
            {"name": "Dynamic execution", "detail": f"Blocks {banned_calls}() calls"},
            {"name": "Isolated namespace", "detail": "Compiled via exec in empty local scope"},
            {"name": "Callable discovery", "detail": "Detects transform_record or any user-defined function"},
            {"name": "Syntax safety", "detail": "Full ast.parse static analysis before compile"},
        ]

    def get_state(self) -> Dict[str, Any]:
        rows = self.db.get_all_rows()
        dlq = self.db.get_dlq_rows()

        total_records = len(rows)
        dlq_count = len(dlq)
        clean_count = sum(1 for r in rows if r.get("ingestion_status") == "clean")
        healed_count = sum(1 for r in rows if r.get("ingestion_status") == "auto_healed")

        total_attempted = self.total_ingress_attempted
        dropped = self.dropped_records_count + dlq_count
        if total_attempted > 0:
            sla_percentage = round(((total_attempted - dropped) / total_attempted) * 100, 1)
        else:
            sla_percentage = 100.0

        with self.lock:
            healing = dict(self.healing_history[0]) if self.healing_history else None
            patch_code = self.last_patch
            ast_verified = self.last_ast_ok
            ast_msg = self.last_ast_msg
            latency = self.last_latency_ms

        ast_state = "verified" if ast_verified is True else ("rejected" if ast_verified is False else "standby")
        return {
            "running": self.running,
            "stage": self.pipeline_stage,
            "dlq_active": self.dlq_active,
            "run_count": self.run_count,
            "metrics": {
                "total_records": total_records,
                "clean_count": clean_count,
                "healed_count": healed_count,
                "dlq_count": dlq_count,
                "sla_percentage": sla_percentage,
                "total_attempted": total_attempted,
                "dropped": dropped,
                "last_latency_ms": latency,
                "sandbox_compiles": self.sandbox_compiles_count,
            },
            "warehouse": rows,
            "dlq": dlq,
            "telemetry": self.telemetry(),
            "healing": healing,
            "patch": {
                "code": patch_code,
                "signature": (healing or {}).get("signature"),
                "latency_ms": latency,
                "verified": ast_verified is True,
            } if patch_code else None,
            "ast": {
                "state": ast_state,
                "verified": ast_verified,
                "message": ast_msg or "Awaiting synthesized patch.",
                "checks": self.ast_checks(),
                "compiles": self.sandbox_compiles_count,
            },
            "cache": {
                "note": "Learned transformation templates keyed by schema signature. Cache hits skip LLM synthesis.",
                "signatures": [
                    {
                        "signature": t["signature"],
                        "label": ", ".join(sorted(t.get("sample_record", {}).keys())) or "template",
                        "first_seen": t["first_seen"],
                        "last_seen": t["last_seen"],
                        "occurrences": t["occurrences"],
                    }
                    for t in self.db.get_all_templates()
                ],
            },
        }


service = SentinelService()




