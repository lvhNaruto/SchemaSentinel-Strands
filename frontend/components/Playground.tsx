"use client";

import { useState } from "react";
import { Zap, Loader2, Check, X, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { prettyJson, formatLatency } from "@/lib/utils";
import type { TestResult } from "@/types";

const PRESETS: Record<string, Record<string, unknown>> = {
  "Renamed Key": {
    projectTitle: "SchemaSentinel Strands",
    OwnerId: "lvh_naruto",
    repositoryUrl: "https://github.com/lvh_naruto/SchemaSentinel-Strands",
    confidenceScore: 91,
  },
  "Percentage String": {
    title: "SchemaSentinel Strands",
    author: "lvh_naruto",
    source_url: "https://github.com/lvh_naruto/SchemaSentinel-Strands",
    relevance_score: "96%",
  },
  "Word Rating": {
    title: "SchemaSentinel Strands",
    author: "lvh_naruto",
    source_url: "https://github.com/lvh_naruto/SchemaSentinel-Strands",
    relevance_score: "high",
  },
  "Author In URL": {
    title: "SchemaSentinel Strands",
    source_url: "https://github.com/lvh_naruto/SchemaSentinel-Strands",
    relevance_score: 95,
  },
  "Nested Metadata": {
    title: "SchemaSentinel Strands",
    author: "lvh_naruto",
    source_url: "https://github.com/lvh_naruto/SchemaSentinel-Strands",
    relevance_score: 93,
    metadata: { stars: 1200, language: "python" },
  },
  "Alien Payload": {
    event: "user_login",
    device: "mobile",
    session: "abc123",
  },
  "IoT Sensor Noise": {
    sensor_id: "temp-42",
    reading_celsius: 23.4,
    unit: "°C",
    timestamp: "2026-09-23T10:00:00Z",
  },
};

function Step({ done, fail, label }: { done: boolean; fail?: boolean; label: string }) {
  return (
    <li className="flex items-center gap-2 text-[11.5px]">
      {fail ? (
        <X size={13} className="text-rosex" />
      ) : done ? (
        <Check size={13} className="text-emeraldx" />
      ) : (
        <ChevronRight size={13} className="text-inkfaint" />
      )}
      <span className={done ? (fail ? "text-rosex" : "text-ink") : "text-inkfaint"}>{label}</span>
    </li>
  );
}

export function Playground({ onDone }: { onDone: () => void }) {
  const [payloadText, setPayloadText] = useState(prettyJson(PRESETS["Renamed Key"]));
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  let payloadValid = false;
  try {
    const parsed = JSON.parse(payloadText);
    payloadValid = typeof parsed === "object" && parsed !== null;
  } catch {
    payloadValid = false;
  }

  const runTest = async () => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.testPayload(JSON.parse(payloadText));
      setResult(res);
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Payload test failed");
    } finally {
      setBusy(false);
    }
  };

  const healed = result?.status === "healed";
  const quarantined = result?.status === "quarantined";
  const clean = result?.status === "clean";

  return (
    <section className="panel" aria-label="Judge playground">
      <p className="panel-title">Judge Playground — Inject Custom Malformed JSON</p>
      <div className="mb-3 flex flex-wrap gap-1.5" role="group" aria-label="Preset drift payloads">
        {Object.entries(PRESETS).map(([name, p]) => (
          <button
            key={name}
            onClick={() => setPayloadText(prettyJson(p))}
            className="rounded-lg border border-edge bg-panel2/70 px-2.5 py-1 font-mono text-[10.5px] font-semibold text-inkdim transition-colors hover:border-violet-400/50 hover:text-violet-300"
          >
            {name}
          </button>
        ))}
      </div>
      <label htmlFor="playground-payload" className="sr-only">
        Malformed ingress payload JSON
      </label>
      <textarea
        id="playground-payload"
        value={payloadText}
        onChange={(e) => setPayloadText(e.target.value)}
        rows={6}
        spellCheck={false}
        className="code-block w-full resize-y"
        aria-invalid={!payloadValid}
      />
      <p className={`mt-1.5 font-mono text-[10px] ${payloadValid ? "text-emeraldx" : "text-rosex"}`}>
        {payloadValid ? "● JSON GUARD: syntax valid — ready for agentic healing" : "✕ JSON syntax error — fix before testing"}
      </p>
      <Button onClick={runTest} disabled={busy || !payloadValid} variant="primary" className="mt-3 w-full sm:w-auto">
        {busy ? (
          <>
            <Loader2 size={14} className="animate-spin" /> Strands Agent synthesizing…
          </>
        ) : (
          <>
            <Zap size={14} /> Test Healing
          </>
        )}
      </Button>

      {error && (
        <p role="alert" className="mt-3 rounded-lg border border-rosex/40 bg-rosex/10 p-2.5 font-mono text-[11px] text-rosex">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-4 rounded-xl border border-edge bg-panel2/60 p-3.5" aria-live="polite">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            {healed && <Badge tone="emerald">✓ HEALED & COMMITTED</Badge>}
            {clean && <Badge tone="cyan">CONFORMED NATIVELY</Badge>}
            {quarantined && <Badge tone="rose">⚠ QUARANTINED IN DLQ</Badge>}
            {result.latency_ms != null && <span className="chip">LATENCY: {formatLatency(result.latency_ms)}</span>}
            {result.signature && <span className="chip">SIGNATURE: {result.signature}</span>}
          </div>
          <ol className="space-y-1" aria-label="Healing verdict steps">
            <Step done label="Detected — contract validation" />
            <Step done fail={quarantined} label={quarantined ? "Agent rejected — unsafe / irrecoverable" : "Strands Agent synthesis"} />
            <Step done={healed} fail={quarantined} label="AST sandbox verification" />
            <Step done={healed || clean} fail={quarantined} label={quarantined ? "Routed to Dead Letter Queue" : "Committed to warehouse"} />
          </ol>
          {result.reason && (
            <p className="mt-3 break-words font-mono text-[10.5px] text-inkfaint">{result.reason.split("\n")[0].slice(0, 240)}</p>
          )}
          {result.patch && (
            <details className="mt-2">
              <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-wider text-violet-300">
                View synthesized patch
              </summary>
              <pre className="code-block mt-1.5">{result.patch}</pre>
            </details>
          )}
        </div>
      )}
    </section>
  );
}


