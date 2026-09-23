"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { Radar, Fingerprint, GitBranch, BrainCircuit, ShieldCheck, Database, Skull } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PipelineStage } from "@/types";

interface StageDef {
  key: PipelineStage | "dlq";
  label: string;
  hint: string;
  color: string; // hex for GSAP
  ring: string; // tailwind border/text tone when active
  icon: React.ReactNode;
}

const STAGES: StageDef[] = [
  { key: "ingress", label: "Stream Ingress", hint: "partitions", color: "#22d3ee", ring: "border-cyan-400 text-cyan-300", icon: <Radar size={15} /> },
  { key: "fingerprint", label: "Fingerprint", hint: "SHA-256 signature", color: "#22d3ee", ring: "border-cyan-400 text-cyan-300", icon: <Fingerprint size={15} /> },
  { key: "drift", label: "Drift Detector", hint: "contract validation", color: "#fbbf24", ring: "border-amber-400 text-amber-300", icon: <GitBranch size={15} /> },
  { key: "agent", label: "Strands Agent", hint: "multi-cloud LLM", color: "#a78bfa", ring: "border-violet-400 text-violet-300", icon: <BrainCircuit size={15} /> },
  { key: "ast", label: "AST Sandbox", hint: "security verification", color: "#a78bfa", ring: "border-violet-400 text-violet-300", icon: <ShieldCheck size={15} /> },
  { key: "warehouse", label: "Warehouse", hint: "tech_projects", color: "#34d399", ring: "border-emerald-400 text-emerald-300", icon: <Database size={15} /> },
];

const DLQ_STAGE: StageDef = {
  key: "dlq", label: "Dead Letter Queue", hint: "irrecoverable payloads", color: "#fb7185",
  ring: "border-rosex text-rosex", icon: <Skull size={15} />,
};

export function PipelineFlow({ stage, dlqActive }: { stage: string | null; dlqActive: boolean }) {
  const packetRef = useRef<HTMLDivElement>(null);
  const activeIdx = stage ? STAGES.findIndex((s) => s.key === stage) : -1;

  useEffect(() => {
    // GSAP cinematic moment: packet travels along the track to the real active stage.
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      if (!packetRef.current || activeIdx < 0) return;
      const pct = (activeIdx / (STAGES.length - 1)) * 100;
      const color = STAGES[activeIdx]?.color ?? "#22d3ee";
      gsap.to(packetRef.current, { left: `${pct}%`, duration: 0.55, ease: "power3.inOut" });
      gsap.to(packetRef.current, { boxShadow: `0 0 16px 3px ${color}`, duration: 0.35 });
    });
    return () => mm.revert();
  }, [activeIdx]);

  return (
    <div className="panel" aria-label="Live healing pipeline">
      <p className="panel-title flex items-center justify-between">
        <span>Live Healing Pipeline</span>
        <span className="font-normal normal-case tracking-normal text-inkfaint">
          driven by real execution state
        </span>
      </p>

      <div className="relative">
        <div aria-hidden className="absolute left-0 right-0 top-[26px] h-[3px] rounded bg-edge" />
        <div
          aria-hidden
          className="absolute left-0 top-[26px] h-[3px] rounded bg-gradient-to-r from-cyanx via-violetx to-emeraldx transition-all duration-500"
          style={{ width: activeIdx >= 0 ? `${(activeIdx / (STAGES.length - 1)) * 100}%` : "0%" }}
        />
        {activeIdx >= 0 && (
          <div
            ref={packetRef}
            aria-hidden
            className="absolute top-[21px] left-0 z-10 h-5 w-5 -translate-x-1/2 rounded-full border-2 border-obsidian"
            style={{ background: STAGES[activeIdx]?.color ?? "#22d3ee" }}
          />
        )}
        <ol className="grid grid-cols-3 gap-x-2 gap-y-4 sm:grid-cols-6">
          {STAGES.map((s, i) => {
            const done = activeIdx > i;
            const active = activeIdx === i;
            return (
              <li key={s.key} className="flex flex-col items-center gap-1.5 text-center">
                <span
                  className={cn(
                    "flex h-[52px] w-[52px] items-center justify-center rounded-xl border bg-panel2 transition-all duration-300",
                    active
                      ? cn(s.ring, "scale-110 animate-pulse-dot")
                      : done
                      ? "border-emerald-400/40 text-emeraldx"
                      : "border-edge text-inkfaint"
                  )}
                  aria-current={active ? "step" : undefined}
                >
                  {s.icon}
                </span>
                <span className={cn("text-[10.5px] font-semibold leading-tight", active ? "text-white" : "text-inkdim")}>
                  {s.label}
                </span>
                <span className="font-mono text-[9px] uppercase tracking-wider text-inkfaint">
                  {active ? "ACTIVE" : done ? "DONE" : "STANDBY"}
                </span>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="mt-5 border-t border-edge pt-4">
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-lg border transition-all duration-300",
              dlqActive
                ? cn(DLQ_STAGE.ring, "bg-rosex/10 shadow-[0_0_14px_rgba(251,113,133,0.25)]")
                : "border-edge text-inkfaint"
            )}
          >
            {DLQ_STAGE.icon}
          </span>
          <div className="min-w-0">
            <p className={cn("text-[11.5px] font-semibold", dlqActive ? "text-rosex" : "text-inkdim")}>
              Dead Letter Queue branch
            </p>
            <p className="font-mono text-[9.5px] text-inkfaint">
              {dlqActive ? "PAYLOAD QUARANTINED — WAREHOUSE PROTECTED" : "STANDBY — no quarantine"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

