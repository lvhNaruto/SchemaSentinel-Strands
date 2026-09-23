"""
SchemaSentinel-Strands API — thin FastAPI layer over the extracted pipeline service.
The Python core (agent, sandbox, database, data producer) remains the single source of truth.
Run:  uvicorn api.main:app --reload --port 8000
"""
import asyncio
import json

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from services.pipeline_service import service, is_meaningful_query
from data_producer import DEFAULT_DISCOVERY_TOPICS
from api.schemas import RunRequest, TestPayloadRequest

app = FastAPI(title="SchemaSentinel-Strands API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    state = service.get_state()
    return {
        "status": "ok",
        "engine": "SchemaSentinel-Strands",
        "running": state["running"],
        "stage": state["stage"],
        "run_count": state["run_count"],
    }


@app.get("/api/state")
def get_state():
    return service.get_state()


@app.get("/api/pipeline/status")
def pipeline_status():
    state = service.get_state()
    return {
        "running": state["running"],
        "stage": state["stage"],
        "dlq_active": state["dlq_active"],
        "run_count": state["run_count"],
    }


@app.post("/api/pipeline/run")
def run_pipeline(req: RunRequest):
    topics: list = []
    if req.mode == "custom":
        if not req.query or not req.query.strip():
            raise HTTPException(status_code=400, detail="Custom mode requires a query.")
        valid, reason = is_meaningful_query(req.query)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Search Guard intercepted: {reason}")
        topics = [req.query.strip()]
    else:
        topics = [t for t in (req.topics or []) if t and t.strip()]
        if not topics:
            raise HTTPException(status_code=400, detail="Select at least one topic.")
    accepted, detail = service.run_pipeline(topics)
    if not accepted:
        raise HTTPException(status_code=409, detail=detail)
    return {"accepted": True, "detail": "Pipeline started", "topics": topics}


@app.post("/api/pipeline/test-payload")
def test_payload(req: TestPayloadRequest):
    result = service.test_payload(req.payload)
    if result.get("status") == "invalid":
        raise HTTPException(status_code=400, detail=result.get("reason", "Invalid payload"))
    return result


@app.post("/api/pipeline/reset")
def reset(clear_warehouse: bool = Query(default=True)):
    result = service.reset(clear_warehouse=clear_warehouse)
    if not result.get("ok"):
        raise HTTPException(status_code=409, detail=result.get("error", "Reset rejected"))
    return result


@app.get("/api/events")
async def events(request: Request, last_id: int = 0):
    """Server-Sent Events stream of real telemetry events (stage changes included)."""
    async def gen():
        last = last_id
        yield f"event: ready\ndata: {json.dumps({'last_id': last})}\n\n"
        while True:
            if await request.is_disconnected():
                break
            new_events = service.events_since(last)
            for ev in new_events:
                last = ev["id"]
                yield f"id: {ev['id']}\nevent: telemetry\ndata: {json.dumps(ev)}\n\n"
            if not new_events:
                yield ": heartbeat\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.get("/api/topics")
def topics():
    return {"topics": DEFAULT_DISCOVERY_TOPICS}


@app.get("/api/schema")
def schema_contract():
    return {"schema": service.db.get_table_schema("tech_projects"), "table": "tech_projects"}


@app.get("/api/warehouse/records")
def warehouse_records():
    return service.db.get_all_rows()


@app.get("/api/warehouse/records/{record_id}")
def warehouse_record(record_id: int):
    for row in service.db.get_all_rows():
        if row.get("project_id") == record_id:
            audit = None
            with service.lock:
                for h in service.healing_history:
                    if h.get("batch_id") == row.get("batch_id"):
                        audit = {k: h[k] for k in ("batch_id", "signature", "latency_ms", "ast_verified", "ts", "patch") if k in h}
                        break
            return {"record": row, "healing_audit": audit}
    raise HTTPException(status_code=404, detail="Record not found")


@app.get("/api/dlq/records")
def dlq_records():
    return service.db.get_dlq_rows()


@app.get("/api/telemetry")
def telemetry():
    return service.telemetry()


@app.get("/api/patches/latest")
def latest_patch():
    state = service.get_state()
    if not state["patch"]:
        return {"available": False}
    return {"available": True, **state["patch"]}


@app.get("/api/ast/status")
def ast_status():
    return service.get_state()["ast"]


@app.get("/api/cache/status")
def cache_status():
    return service.get_state()["cache"]

