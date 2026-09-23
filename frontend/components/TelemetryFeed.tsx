"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import type { TelemetryEvent } from "@/types";
import { cn } from "@/lib/utils";

const TAG_TONE: Record<string, string> = {
  SYSTEM: "text-emerald-300",
  INGRESS: "text-cyan-300",
  COMMITTED: "text-emerald-300",
  DRIFT_DETECTED: "text-rosex",
  STRANDS_AGENT: "text-amberx",
  AST_VERIFIED: "text-violet-300",
  DLQ_QUARANTINED: "text-rosex",
  STREAM_IDLE: "text-rosex",
};

export function TelemetryFeed({ events }: { events: TelemetryEvent[] }) {
  const reduce = useReducedMotion();
  return (
    <section className="panel" aria-label="Live execution telemetry">
      <p className="panel-title flex items-center justify-between">
        <span>&gt;_ Live Execution Telemetry</span>
        <span className="font-normal normal-case tracking-normal text-inkfaint">real event stream</span>
      </p>
      <div
        role="log"
        aria-live="polite"
        aria-label="Telemetry terminal"
        className="max-h-64 overflow-y-auto rounded-xl border border-edge bg-[#030509] p-3"
      >
        {events.length === 0 && (
          <p className="font-mono text-[11px] text-inkfaint">&gt;_ awaiting events…</p>
        )}
        <AnimatePresence initial={false}>
          {events.slice(0, 40).map((ev) => (
            <motion.div
              key={ev.id}
              layout={!reduce}
              initial={reduce ? undefined : { opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="term-line"
            >
              <span className="text-inkfaint">{ev.ts}</span>{" "}
              <span className={cn("font-bold", TAG_TONE[ev.tag] ?? "text-inkdim")}>[{ev.tag}]</span>{" "}
              <span className="text-inkdim">{ev.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </section>
  );
}
