"use client";

import { Fingerprint } from "lucide-react";
import type { CacheEntry } from "@/types";
import { Badge } from "@/components/ui/badge";

/**
 * Learned transformation template panel: shows the REAL template cache maintained by the backend.
 * Each entry is a verified AST patch keyed by schema signature. Cache hits skip LLM synthesis.
 */
export function CachePanel({ entries, note }: { entries: CacheEntry[]; note: string }) {
  return (
    <section className="panel" aria-label="Learned transformation template cache">
      <p className="panel-title flex items-center justify-between">
        <span>Learned Templates</span>
        <span className="font-normal normal-case tracking-normal text-inkfaint">
          SHA-256 of normalized key shape
        </span>
      </p>
      {entries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-cyan-400/30 bg-cyan-400/[0.04] p-6 text-center">
          <p className="font-display text-[13px] font-bold text-cyanx">No templates learned yet</p>
          <p className="mt-1 text-[11.5px] text-inkdim">
            Run the pipeline — the first time a drift shape appears it is healed by the LLM and stored as a reusable template.
          </p>
        </div>
      ) : (
        <ul className="space-y-2" role="list">
          {entries.map((e) => (
            <li
              key={e.signature}
              className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-cyan-400/25 bg-cyan-400/[0.04] p-3"
            >
              <Fingerprint size={14} className="shrink-0 text-cyanx" />
              <span className="font-mono text-[11px] font-semibold text-cyanx">{e.signature}</span>
              <span className="min-w-0 flex-1 truncate text-[11px] text-inkdim">{e.label}</span>
              {e.occurrences > 1 ? (
                <Badge tone="cyan">RECURRING ×{e.occurrences}</Badge>
              ) : (
                <Badge tone="neutral">NEW SIGNATURE</Badge>
              )}
              <span className="font-mono text-[9.5px] text-inkfaint">last {e.last_seen}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 font-mono text-[9.5px] leading-relaxed text-inkfaint">{note}</p>
    </section>
  );
}
