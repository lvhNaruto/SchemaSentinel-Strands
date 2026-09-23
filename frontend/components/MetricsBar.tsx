"use client";

import { Database, ShieldCheck, Activity, Zap, Skull } from "lucide-react";
import type { Metrics } from "@/types";
import { cn, formatLatency } from "@/lib/utils";

function MetricCard({
  icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  accent: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-edge bg-gradient-to-b from-panel2 to-[#080d19] p-3.5 transition-transform duration-200 hover:-translate-y-0.5 hover:border-edgelit">
      <span
        aria-hidden
        className={cn(
          "absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-current to-transparent opacity-60",
          accent
        )}
      />
      <div className="flex items-center justify-between font-mono text-[10px] font-bold uppercase tracking-[0.09em] text-inkdim">
        <span>{label}</span>
        <span aria-hidden>{icon}</span>
      </div>
      <div className="mt-1.5 font-display text-[22px] font-bold leading-none text-white">{value}</div>
      <div className="mt-1.5 text-[10.5px] text-inkfaint">{sub}</div>
    </div>
  );
}

export function MetricsBar({ metrics }: { metrics: Metrics | undefined }) {
  const m = metrics;
  const sla = m ? m.sla_percentage : 100;
  return (
    <section aria-label="Live metrics" className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
      <MetricCard
        icon={<Database size={13} />}
        label="Warehouse Records"
        value={m ? String(m.total_records) : "—"}
        sub={m ? `${m.clean_count} clean • ${m.healed_count} healed` : "tech_projects"}
        accent="text-emeraldx"
      />
      <MetricCard
        icon={<ShieldCheck size={13} />}
        label="Auto-Healed"
        value={m ? String(m.healed_count) : "—"}
        sub="drifts resolved autonomously"
        accent="text-teal-300"
      />
      <MetricCard
        icon={<Activity size={13} />}
        label="Reliability SLA"
        value={m ? `${sla}%` : "—"}
        sub={m ? `${m.total_attempted} attempted • ${m.dropped} dropped` : "zero drop target"}
        accent={sla >= 99 ? "text-emeraldx" : "text-rosex"}
      />
      <MetricCard
        icon={<Zap size={13} />}
        label="Synthesis Latency"
        value={m?.last_latency_ms != null ? formatLatency(m.last_latency_ms) : "—"}
        sub="Bedrock Grok 4.6 → Nebius fallback"
        accent="text-amberx"
      />
      <MetricCard
        icon={<Skull size={13} />}
        label="Dead Letter Queue"
        value={m ? String(m.dlq_count) : "—"}
        sub="zero warehouse pollution"
        accent={(m?.dlq_count ?? 0) > 0 ? "text-rosex" : "text-emeraldx"}
      />
    </section>
  );
}
