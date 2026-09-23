"use client";

import { Shield, Play, RotateCcw, ScrollText, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function Header({
  connected,
  running,
  runCount,
  dlqCount,
  onRun,
  onSchema,
  onReset,
}: {
  connected: boolean;
  running: boolean;
  runCount: number;
  dlqCount: number;
  onRun: () => void;
  onSchema: () => void;
  onReset: () => void;
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-edge bg-obsidian/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-5 gap-y-3 px-4 py-3 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-xl border border-emerald-400/45 bg-gradient-to-br from-[#0f2b22] to-[#071018] shadow-[0_0_20px_rgba(16,185,129,0.25)]">
            <Shield size={22} className="text-emeraldx" strokeWidth={2} />
            <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 animate-pulse-dot rounded-full border-2 border-obsidian bg-cyanx shadow-[0_0_8px_#22d3ee]" />
          </div>
          <div>
            <h1 className="font-display text-[19px] font-bold leading-tight text-white">
              SchemaSentinel<span className="text-emeraldx">-Strands</span>
            </h1>
            <p className="text-[11.5px] text-inkdim">
              Autonomous Cognitive Data Self-Healing Engine
            </p>
          </div>
        </div>

        <Badge tone={connected ? "emerald" : "rose"} className="ml-auto">
          <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
          {connected ? "System Operational" : "Backend Offline"}
        </Badge>
        <span className="chip">RUNS: {runCount}</span>
        <span className="chip">DLQ: {dlqCount}</span>

        <div className="flex w-full items-center gap-2 sm:w-auto">
          <Button onClick={onRun} disabled={running} variant="primary" className="min-w-[220px]">
            {running ? (
              <>
                <Loader2 size={15} className="animate-spin" /> Healing Pipeline Active…
              </>
            ) : (
              <>
                <Play size={15} /> Run Autonomous Healing Pipeline
              </>
            )}
          </Button>
          <Button onClick={onSchema} aria-label="Show target schema contract">
            <ScrollText size={14} /> Target Schema
          </Button>
          <Button onClick={onReset} variant="danger" aria-label="Reset warehouse and DLQ">
            <RotateCcw size={14} /> Reset
          </Button>
        </div>
      </div>
    </header>
  );
}
