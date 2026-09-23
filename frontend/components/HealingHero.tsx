"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Zap, ShieldCheck } from "lucide-react";
import type { HealingAudit } from "@/types";
import { cn, prettyJson, formatLatency } from "@/lib/utils";

/** Renders one side of the diff with semantic row highlights. */
function JsonPane({
  data,
  side,
  counterpart,
}: {
  data: Record<string, unknown>;
  side: "before" | "after";
  counterpart?: Record<string, unknown>;
}) {
  const entries = Object.entries(data);
  return (
    <div className="code-block" role="group" aria-label={side === "before" ? "raw drifted payload" : "healed conformed payload"}>
      {entries.length === 0 && <span className="text-inkfaint">{"{ }"}</span>}
      {entries.map(([k, v]) => {
        const removed = side === "before" && counterpart && !(k in counterpart);
        const added = side === "after" && counterpart && !(k in counterpart);
        return (
          <div
            key={k}
            className={cn(
              "flex items-start gap-2 border-b border-edge/60 py-1 last:border-0",
              removed && "text-violet-300",
              added && "text-emerald-300"
            )}
          >
            <span className="text-inkfaint">"{k}":</span>
            <span className="min-w-0 flex-1 break-words">
              {typeof v === "object" ? prettyJson(v) : String(v)}
            </span>
            {removed && <span className="font-mono text-[9px] uppercase text-violet-300/80">mutated</span>}
            {added && <span className="font-mono text-[9px] uppercase text-emerald-300/80">conformed</span>}
          </div>
        );
      })}
    </div>
  );
}

export function HealingHero({ healing }: { healing: HealingAudit | null }) {
  const reduce = useReducedMotion();
  if (!healing) {
    return (
      <section className="panel" aria-label="Self-healing transformation">
        <p className="panel-title">Self-Healing Transformation — Before → AI → After</p>
        <div className="rounded-xl border border-dashed border-emerald-400/30 bg-emerald-400/[0.04] p-8 text-center">
          <p className="font-display text-[14px] font-bold text-emeraldx">No schema drift events yet</p>
          <p className="mt-1 text-[11.5px] text-inkdim">
            Run the autonomous healing pipeline to watch drift get healed in real time.
          </p>
        </div>
      </section>
    );
  }
  return (
    <section className="panel" aria-label="Self-healing transformation">
      <p className="panel-title flex items-center justify-between">
        <span>Self-Healing Transformation — Before → AI → After</span>
        <span className="font-mono text-[10px] font-normal normal-case tracking-normal text-cyanx">
          sig {healing.signature} • {formatLatency(healing.latency_ms)}
        </span>
      </p>
      <div className="grid gap-3 md:grid-cols-[1fr_auto_1fr]">
        <motion.div
          initial={reduce ? undefined : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="rounded-xl border border-rosex/30 bg-rosex/[0.04] p-3"
        >
          <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.1em] text-rosex">
            ● Before AI — Drifted Raw Ingress
          </p>
          <JsonPane data={healing.before} side="before" counterpart={healing.after} />
        </motion.div>

        <motion.div
          className="flex flex-row items-center justify-center gap-3 md:flex-col"
          initial={reduce ? undefined : { opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <span className="flex h-14 w-14 items-center justify-center rounded-full border border-violet-400/50 bg-violet-400/10 shadow-[0_0_22px_rgba(139,92,246,0.35)]">
            <Zap size={22} className="text-violet-300" />
          </span>
          <div className="flex flex-col items-center gap-1">
            <span className="font-mono text-[9px] font-bold text-violet-300">AI FIX</span>
            <span className="flex items-center gap-1 font-mono text-[9px] text-inkdim">
              <ShieldCheck size={11} className="text-emeraldx" /> AST VERIFIED
            </span>
          </div>
        </motion.div>

        <motion.div
          initial={reduce ? undefined : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.15 }}
          className="rounded-xl border border-emerald-400/35 bg-emerald-400/[0.05] p-3"
        >
          <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.1em] text-emeraldx">
            ● After AI — Conformed Record
          </p>
          <JsonPane data={healing.after} side="after" counterpart={healing.before} />
        </motion.div>
      </div>
    </section>
  );
}
