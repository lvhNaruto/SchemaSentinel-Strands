"use client";

import { useCallback, useEffect, useState } from "react";
import { useSentinel } from "@/hooks/useSentinel";
import { api } from "@/lib/api";
import { Header } from "@/components/Header";
import { MetricsBar } from "@/components/MetricsBar";
import { PipelineFlow } from "@/components/PipelineFlow";
import { HealingHero } from "@/components/HealingHero";
import { Warehouse } from "@/components/Warehouse";
import { DlqPanel } from "@/components/DlqPanel";
import { TelemetryFeed } from "@/components/TelemetryFeed";
import { SandboxPanel } from "@/components/SandboxPanel";
import { CachePanel } from "@/components/CachePanel";
import { Playground } from "@/components/Playground";
import { StreamSource } from "@/components/StreamSource";
import { Dialog } from "@/components/ui/dialog";
import type { AstInfo } from "@/types";

const FALLBACK_AST: AstInfo = {
  state: "standby",
  verified: null,
  message: "Awaiting synthesized patch.",
  checks: [],
  compiles: 0,
};

export default function Page() {
  const { state, connected, refresh } = useSentinel();
  const [topics, setTopics] = useState<string[]>([]);
  const [runBody, setRunBody] = useState<{ mode: string; topics?: string[]; query?: string }>({
    mode: "preset",
  });
  const [schemaOpen, setSchemaOpen] = useState(false);
  const [schemaText, setSchemaText] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    api.topics().then((t) => setTopics(t.topics)).catch(() => setTopics([]));
  }, []);

  useEffect(() => {
    if (notice) {
      const t = setTimeout(() => setNotice(null), 4200);
      return () => clearTimeout(t);
    }
  }, [notice]);

  const runPipeline = useCallback(
    async (body: { mode: string; topics?: string[]; query?: string }) => {
      setRunBody(body);
      try {
        await api.runPipeline(body);
        setNotice("Pipeline started — watch the live pipeline & telemetry.");
        refresh();
      } catch (e) {
        setNotice(e instanceof Error ? e.message : "Failed to start pipeline");
      }
    },
    [refresh]
  );

  const openSchema = useCallback(async () => {
    setSchemaOpen(true);
    setSchemaText(null);
    try {
      const s = await api.schema();
      setSchemaText(s.schema);
    } catch {
      setSchemaText("Failed to load schema contract from backend.");
    }
  }, []);

  const resetAll = useCallback(async () => {
    try {
      await api.reset(true);
      setNotice("Warehouse & DLQ reset. Engine re-armed.");
      refresh();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Reset failed");
    }
  }, [refresh]);

  const metrics = state?.metrics;
  const running = state?.running ?? false;

  return (
    <div className="min-h-screen">
      <Header
        connected={connected}
        running={running}
        runCount={state?.run_count ?? 0}
        dlqCount={metrics?.dlq_count ?? 0}
        onRun={() => runPipeline(runBody)}
        onSchema={openSchema}
        onReset={resetAll}
      />

      {notice && (
        <p
          role="status"
          className="mx-auto max-w-[1600px] px-4 pt-3 lg:px-8"
        >
          <span className="inline-block rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-3 py-1.5 font-mono text-[11px] text-emeraldx">
            {notice}
          </span>
        </p>
      )}

      <main className="mx-auto max-w-[1600px] space-y-6 px-4 py-6 lg:px-8">
        <MetricsBar metrics={metrics} />

        <PipelineFlow stage={state?.stage ?? null} dlqActive={state?.dlq_active ?? false} />

        <div className="grid gap-6 xl:grid-cols-[1.25fr_1fr]">
          <div className="space-y-6">
            <HealingHero healing={state?.healing ?? null} />
            <Warehouse records={state?.warehouse ?? []} />
            <DlqPanel records={state?.dlq ?? []} />
            <TelemetryFeed events={state?.telemetry ?? []} />
          </div>
          <div className="space-y-6">
            <StreamSource topics={topics} running={running} onRun={runPipeline} />
            <SandboxPanel ast={state?.ast ?? FALLBACK_AST} patch={state?.patch ?? null} />
            <CachePanel
              entries={state?.cache?.signatures ?? []}
              note={state?.cache?.note ?? ""}
            />
            <Playground onDone={refresh} />
          </div>
        </div>

        <footer className="border-t border-edge pt-4 text-center font-mono text-[10px] text-inkfaint">
          SchemaSentinel-Strands — Strands Agents SDK on AWS Bedrock Mantle • Nebius Studio fallback •
          AST security sandbox • SQLite warehouse + DLQ
        </footer>
      </main>

      <Dialog open={schemaOpen} onClose={() => setSchemaOpen(false)} title="Target Schema Contract — tech_projects" wide>
        {schemaText ? (
          <pre className="code-block" aria-label="Live warehouse schema contract">
            {schemaText}
          </pre>
        ) : (
          <p className="py-6 text-center text-[12px] text-inkdim">Loading schema contract…</p>
        )}
      </Dialog>
    </div>
  );
}
