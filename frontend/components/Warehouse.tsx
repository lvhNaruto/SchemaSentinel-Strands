"use client";

import { useMemo, useState } from "react";
import { Search, Sparkles, CheckCircle2 } from "lucide-react";
import { Tabs } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { formatLatency } from "@/lib/utils";
import type { RecordDetail, WarehouseRecord } from "@/types";

function StatusBadge({ status }: { status: string | null }) {
  if (status === "auto_healed") return <Badge tone="violet"><Sparkles size={10} /> Auto-Healed</Badge>;
  return <Badge tone="emerald"><CheckCircle2 size={10} /> Clean</Badge>;
}

function Row({ r, onOpen }: { r: WarehouseRecord; onOpen: (r: WarehouseRecord) => void }) {
  return (
    <tr
      tabIndex={0}
      role="button"
      onClick={() => onOpen(r)}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onOpen(r))}
      className="cursor-pointer border-b border-edge/70 transition-colors hover:bg-white/[0.03] focus:bg-white/[0.05]"
    >
      <td className="px-3 py-2"><StatusBadge status={r.ingestion_status} /></td>
      <td className="max-w-[240px] truncate px-3 py-2 text-[12px] font-semibold text-ink">{r.title}</td>
      <td className="px-3 py-2 font-mono text-[11px] text-inkdim">{r.author}</td>
      <td className="max-w-[220px] truncate px-3 py-2 font-mono text-[10.5px] text-cyanx/80">{r.source_url}</td>
      <td className="px-3 py-2 font-mono text-[11px] text-inkdim">{r.relevance_score}</td>
      <td className="px-3 py-2 font-mono text-[10.5px] text-inkfaint">{r.created_at}</td>
    </tr>
  );
}

export function Warehouse({ records }: { records: WarehouseRecord[] }) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<WarehouseRecord | null>(null);
  const [detail, setDetail] = useState<RecordDetail | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const base = q
      ? records.filter((r) => [r.title, r.author, r.source_url].join(" ").toLowerCase().includes(q))
      : records;
    return base;
  }, [records, query]);

  const clean = filtered.filter((r) => r.ingestion_status !== "auto_healed");
  const healed = filtered.filter((r) => r.ingestion_status === "auto_healed");

  const openInspector = async (r: WarehouseRecord) => {
    setSelected(r);
    setDetail(null);
    try {
      setDetail(await api.record(r.project_id));
    } catch {
      setDetail({ record: r, healing_audit: null });
    }
  };

  const table = (rows: WarehouseRecord[]) =>
    rows.length ? (
      <div className="overflow-x-auto rounded-xl border border-edge">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="bg-panel2 font-mono text-[10px] uppercase tracking-wider text-inkfaint">
              <th className="px-3 py-2">Status</th><th className="px-3 py-2">Title</th>
              <th className="px-3 py-2">Author</th><th className="px-3 py-2">Source URL</th>
              <th className="px-3 py-2">Score</th><th className="px-3 py-2">Ingested</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => <Row key={r.project_id} r={r} onOpen={openInspector} />)}
          </tbody>
        </table>
      </div>
    ) : (
      <p className="rounded-xl border border-edge bg-panel2/50 px-4 py-6 text-center text-[12px] text-inkdim">
        No records in this view{query ? " matching the filter" : ""}.
      </p>
    );

  return (
    <section className="panel" aria-label="Live warehouse records">
      <p className="panel-title flex items-center justify-between">
        <span>Live Warehouse — tech_projects</span>
        <span className="font-normal normal-case tracking-normal text-inkfaint">● active SQLite conformed storage</span>
      </p>
      <div className="relative mb-3">
        <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-inkfaint" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by title, author, or URL…"
          aria-label="Search warehouse records"
          className="w-full rounded-lg border border-edge bg-panel2 py-2 pl-9 pr-3 text-[12.5px] text-ink placeholder:text-inkfaint focus:border-emeraldx/50"
        />
      </div>
      <Tabs
        tabs={[
          { key: "all", label: `All (${filtered.length})`, content: table(filtered) },
          { key: "clean", label: `Clean (${clean.length})`, content: table(clean) },
          { key: "healed", label: `✨ Auto-Healed (${healed.length})`, content: table(healed) },
        ]}
      />

      <Dialog open={!!selected} onClose={() => setSelected(null)} title={`Record Inspector — #${selected?.project_id ?? ""}`} wide>
        {detail ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={detail.record.ingestion_status} />
              <span className="chip">BATCH: {detail.record.batch_id ?? "—"}</span>
              <span className="chip">INGESTED: {detail.record.created_at}</span>
            </div>
            <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {Object.entries(detail.record).map(([k, v]) => (
                <div key={k} className="rounded-lg border border-edge bg-panel2/60 p-2.5">
                  <dt className="font-mono text-[9.5px] uppercase tracking-wider text-inkfaint">{k}</dt>
                  <dd className="mt-0.5 break-words font-mono text-[11.5px] text-inkdim">{String(v)}</dd>
                </div>
              ))}
            </dl>
            {detail.healing_audit ? (
              <div>
                <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-violet-300">
                  Linked healing audit
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="chip">SIGNATURE: {detail.healing_audit.signature}</span>
                  <span className="chip">LATENCY: {formatLatency(detail.healing_audit.latency_ms)}</span>
                  <span className="chip">AST: {detail.healing_audit.ast_verified ? "VERIFIED" : "N/A"}</span>
                  <span className="chip">HEALED AT: {detail.healing_audit.ts}</span>
                </div>
                {detail.healing_audit.patch && (
                  <pre className="code-block mt-2" aria-label="Transformation patch used">
                    {detail.healing_audit.patch}
                  </pre>
                )}
              </div>
            ) : (
              <p className="text-[12px] text-inkfaint">No linked healing audit — record conformed natively.</p>
            )}
          </div>
        ) : (
          <p className="py-6 text-center text-[12px] text-inkdim">Loading record…</p>
        )}
      </Dialog>
    </section>
  );
}

