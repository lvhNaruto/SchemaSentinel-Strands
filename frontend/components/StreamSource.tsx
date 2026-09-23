"use client";

import { useState } from "react";
import { Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export function StreamSource({
  topics,
  running,
  onRun,
}: {
  topics: string[];
  running: boolean;
  onRun: (body: { mode: string; topics?: string[]; query?: string }) => void;
}) {
  const [mode, setMode] = useState<"preset" | "custom">("preset");
  const [selected, setSelected] = useState<string[]>(topics.length ? [topics[0]] : []);
  const [query, setQuery] = useState("SchemaSentinel Strands");
  const [busy, setBusy] = useState(false);

  const toggle = (t: string) =>
    setSelected((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]));

  const go = async () => {
    setBusy(true);
    try {
      if (mode === "preset") onRun({ mode: "preset", topics: selected });
      else onRun({ mode: "custom", query });
    } finally {
      setTimeout(() => setBusy(false), 1500);
    }
  };

  return (
    <section className="panel" aria-label="Upstream ingress stream source">
      <p className="panel-title">Upstream Ingress Stream</p>
      <div className="mb-3 flex gap-1.5" role="tablist" aria-label="Stream mode">
        {(["preset", "custom"] as const).map((m) => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={cn(
              "rounded-lg border px-3 py-1.5 text-[12px] font-semibold transition-colors",
              mode === m
                ? "border-cyan-400/50 bg-cyan-400/10 text-cyanx"
                : "border-edge bg-panel2/60 text-inkdim hover:text-ink"
            )}
          >
            {m === "preset" ? "Preset Partitions" : "Custom Query / Repo"}
          </button>
        ))}
      </div>

      {mode === "preset" ? (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Preset topics">
          {topics.map((t) => (
            <button
              key={t}
              onClick={() => toggle(t)}
              aria-pressed={selected.includes(t)}
              className={cn(
                "max-w-full truncate rounded-lg border px-2.5 py-1 font-mono text-[10.5px] transition-colors",
                selected.includes(t)
                  ? "border-emerald-400/50 bg-emerald-400/10 text-emeraldx"
                  : "border-edge bg-panel2/70 text-inkdim hover:text-ink"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      ) : (
        <div className="relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-inkfaint" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Custom ingress query"
            placeholder="GitHub repo, username, or topic…"
            className="w-full rounded-lg border border-edge bg-panel2 py-2 pl-9 pr-3 text-[12.5px] text-ink placeholder:text-inkfaint focus:border-cyanx/50"
          />
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="chip">
          {mode === "preset" ? `${selected.length} partition(s) armed` : "live grounded resolution"}
        </span>
        <Button onClick={go} disabled={running || busy || (mode === "preset" && selected.length === 0)} className="ml-auto">
          {busy ? <Loader2 size={14} className="animate-spin" /> : null}
          {running ? "Pipeline active…" : "Ingest from source"}
        </Button>
      </div>
      <p className="mt-2 font-mono text-[9.5px] text-inkfaint">
        Preset partitions resolve live GitHub repositories first, then fall back to the offline catalog
        only if the API is rate-limited. Custom queries always use live grounded resolution.
      </p>
    </section>
  );
}
