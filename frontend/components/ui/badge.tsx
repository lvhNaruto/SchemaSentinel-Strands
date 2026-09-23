import { cn } from "@/lib/utils";

export type BadgeTone = "emerald" | "violet" | "cyan" | "amber" | "rose" | "neutral";

const tones: Record<BadgeTone, string> = {
  emerald: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300",
  violet: "border-violet-400/40 bg-violet-400/10 text-violet-300",
  cyan: "border-cyan-400/40 bg-cyan-400/10 text-cyan-300",
  amber: "border-amber-400/40 bg-amber-400/10 text-amber-300",
  rose: "border-rose-400/40 bg-rose-400/10 text-rose-300",
  neutral: "border-edge bg-white/[0.04] text-inkdim",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
