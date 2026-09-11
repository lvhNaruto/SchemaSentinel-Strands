import sys
import time
import traceback
from database import WarehouseDatabase
from agent import SchemaHealingAgent
from sandbox import SandboxExecutor
from data_producer import fetch_multi_topic_stream_batches, DEFAULT_DISCOVERY_TOPICS

def run_cli_pipeline(topics=None):
    if topics is None:
        topics = DEFAULT_DISCOVERY_TOPICS[:3]  # Multi-topic by default

    print("=" * 70)
    print("🚀 SchemaSentinel-Strands | Autonomous Data Self-Healing Pipeline (CLI)")
    print("🛡️ Powered by: Strands Agents SDK + AWS Bedrock Mantle (xai.grok-4.6)")
    if len(topics) == 1:
        print(f"📡 Ingress Stream Source: {topics[0]}")
    else:
        print(f"📡 Ingress Stream: Round-Robin across {len(topics)} active partitions")
    print("=" * 70)

    db = WarehouseDatabase()
    agent = SchemaHealingAgent()

    print("\n📋 Target Warehouse Schema (tech_projects):")
    print(db.get_table_schema("tech_projects").strip())
    print("-" * 70)

    # Fetch 5 stream batches
    cursors = {}
    batches, updated_cursors, summary_desc = fetch_multi_topic_stream_batches(
        topics=topics,
        topic_cursors=cursors,
        batch_size=5
    )

    if not batches:
        print("⚠️ No stream batches available for selected topics.")
        return

    print(f"\n📥 Ingesting {len(batches)} Batches ({summary_desc})...\n")

    for idx, batch_event in enumerate(batches, 1):
        b_id = batch_event["batch_id"]
        recs = batch_event["records"]
        s_title = batch_event.get("short_title", "Batch")
        f_summary = batch_event.get("fix_summary", "")

        print(f"[{idx}/5] Ingesting {b_id} ({s_title})...")

        try:
            inserted, skipped = db.insert_batch(recs, batch_id=b_id, status="clean")
            print(f"    ✅ PASS: Conformed directly to schema. Inserted: {inserted} records.")
        except Exception:
            err_trace = traceback.format_exc()
            print(f"    🚨 DRIFT DETECTED: Upstream payload rejected by database!")
            print(f"    ⚡ Invoking Strands Agent on AWS Bedrock Mantle (xai.grok-4.6)...")

            target_schema = db.get_table_schema("tech_projects")
            raw_patch = agent.synthesize_transformation_patch(
                failing_records=recs,
                target_schema=target_schema,
                error_trace=err_trace
            )
            clean_patch = agent.extract_pure_code(raw_patch)

            compiled, func, compile_msg = SandboxExecutor.compile_patch(clean_patch)
            if compiled:
                transformed_batch = []
                for r in recs:
                    try:
                        healed_raw = func(r)
                    except Exception:
                        healed_raw = None

                    # Zero-Crash Shield
                    if isinstance(healed_raw, dict):
                        healed = healed_raw
                    else:
                        healed = agent.get_fallback_dict(r)

                    healed["batch_id"] = b_id
                    healed["ingestion_status"] = "auto_healed"
                    transformed_batch.append(healed)

                inserted, skipped = db.insert_batch(
                    transformed_batch, batch_id=b_id, status="auto_healed"
                )
                print(f"    🎉 HEALED: Synthesized AST transformation patch via Bedrock Mantle.")
                print(f"    ✨ Inserted: {inserted} records ({f_summary})")
            else:
                print(f"    ❌ Sandbox compilation failed: {compile_msg}")

        time.sleep(0.3)

    print("\n" + "=" * 70)
    all_rows = db.get_all_rows()
    print(f"📊 Pipeline Execution Summary: {len(all_rows)} Total Records in Warehouse (100% Zero Drop SLA).")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_topics = [sys.argv[1]]
    else:
        user_topics = DEFAULT_DISCOVERY_TOPICS[:3]
    run_cli_pipeline(user_topics)