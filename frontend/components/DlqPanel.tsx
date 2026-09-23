"use client";

import { Skull } from "lucide-react";
import type { DlqRecord } from "@/types";
import { prettyJson } from "@/lib/utils";

function prettyPayload(raw: string): string {
  try {
    return JSON.stringify(JSON.parse(raw), null, 1);
  } catch {
    return raw;
  }
}

export function DlqPanel({ records }: { records: DlqRecord[] }) {
  return (
    <section className="panel" aria-label="Dead letter queue">
      <p className="panel-title flex items-center justify-between">
        <span>Dead Letter Queue — Secure Quarantine</span>
        <span className="font-normal normal-case tracking-normal text-inkfaint">
          {records.length} quarantined
        </span>
      </p>
      {records.length === 0 ? (
        <div className="rounded-xl border border-dashed border-emerald-400/30 bg-emerald-400/[0.04] p-8 text-center">
          <p className="font-display text-[14px] font-bold text-emeraldx">✓ Zero warehouse pollution</p>
          <p className="mt-1 text-[11.5px] text-inkdim">
            All processed records conformed successfully. Nothing quarantined.
          </p>
        </div>
      ) : (
        <ul className="space-y-2.5" role="list">
          {records.map((r) => (
            <li
              key={r.dlq_id}
              className="rounded-xl border border-rosex/30 border-l-4 border-l-rosex bg-rosex/[0.04] p-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[10px] text-rosex">
                <span className="flex items-center gap-1.5">
                  <Skull size={11} /> DLQ-{r.dlq_id} • {r.batch_id}
                </span>
                <span className="text-inkfaint">{r.quarantined_at}</span>
              </div>
              <p className="mt-2 break-words font-mono text-[11px] text-rose-200">
                ⚠ {r.failure_reason?.split("\n")[0]?.slice(0, 220) || "Unknown failure"}
              </p>
              {r.detected_keys && (
                <p className="mt-1.5 break-words font-mono text-[10px] text-inkfaint">
                  <span className="text-rose-300/80">Detected keys:</span> {r.detected_keys}
                </p>
              )}
              <details className="mt-2 group">
                <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-wider text-inkfaint hover:text-inkdim">
                  Original payload
                </summary>
                <pre className="code-block mt-1.5 max-h-32" aria-label="Quarantined raw payload">
                  {prettyPayload(r.raw_payload).slice(0, 900)}
                </pre>
              </details>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
