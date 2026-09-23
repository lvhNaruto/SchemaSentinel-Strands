"use client";

import { useState } from "react";
import { Copy, Check, ShieldCheck, ShieldX, ShieldAlert } from "lucide-react";
import { formatLatency } from "@/lib/utils";
import type { AstInfo, PatchInfo } from "@/types";

function AstHeader({ ast }: { ast: AstInfo }) {
  if (ast.state === "verified")
    return (
      <p className="mb-3 flex items-center gap-2 font-mono text-[11.5px] font-bold text-emeraldx">
        <ShieldCheck size={15} /> AST VERIFIED SAFE — {ast.compiles} validated compile{ast.compiles === 1 ? "" : "s"}
      </p>
    );
  if (ast.state === "rejected")
    return (
      <p className="mb-3 flex items-center gap-2 font-mono text-[11.5px] font-bold text-rosex">
        <ShieldX size={15} /> SANDBOX REJECTED PATCH
      </p>
    );
  return (
    <p className="mb-3 flex items-center gap-2 font-mono text-[11.5px] font-bold text-inkdim">
      <ShieldAlert size={15} /> STANDBY — awaiting synthesized patch
    </p>
  );
}

export function SandboxPanel({ ast, patch }: { ast: AstInfo; patch: PatchInfo | null }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    if (!patch?.code) return;
    try {
      await navigator.clipboard.writeText(patch.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <section className="panel" aria-label="AST security sandbox and patch viewer">
      <p className="panel-title">AST Security Sandbox</p>
      <AstHeader ast={ast} />
      <ul className="mb-4 space-y-0" role="list">
        {ast.checks.map((c) => (
          <li
            key={c.name}
            className="flex items-center gap-2 border-b border-edge/60 py-1.5 text-[11px] last:border-0"
          >
            <Check size={12} className="shrink-0 text-emeraldx" />
            <span className="min-w-[150px] font-semibold text-ink">{c.name}</span>
            <span className="text-inkfaint">{c.detail}</span>
          </li>
        ))}
      </ul>
      {ast.state === "rejected" && (
        <p className="code-block mb-3 text-rosex">{ast.message}</p>
      )}

      <p className="panel-title mt-4">Synthesized Transformation Patch</p>
      {patch?.code ? (
        <>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="chip">PATCH ID: patch_{patch.signature}</span>
            <span className="chip text-amberx">LATENCY: {formatLatency(patch.latency_ms)}</span>
            <span className="chip text-emeraldx">{patch.verified ? "✓ AST VERIFIED" : "UNVERIFIED"}</span>
            <button
              onClick={copy}
              aria-label="Copy patch to clipboard"
              className="chip cursor-pointer border-edgelit hover:border-emeraldx/50 hover:text-emeraldx"
            >
              {copied ? <Check size={11} /> : <Copy size={11} />} {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <pre className="code-block" aria-label="Generated Python transformation patch">
            {patch.code}
          </pre>
        </>
      ) : (
        <div className="rounded-xl border border-dashed border-violet-400/30 bg-violet-400/[0.04] p-6 text-center">
          <p className="font-display text-[13px] font-bold text-violet-300">No synthesized patch yet</p>
          <p className="mt-1 text-[11.5px] text-inkdim">
            A drift event will trigger the Strands Agent to synthesize a transformation here.
          </p>
        </div>
      )}
    </section>
  );
}
