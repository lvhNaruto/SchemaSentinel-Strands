"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<Variant, string> = {
  primary:
    "bg-gradient-to-r from-emerald-600 via-emerald-500 to-cyan-500 text-white border border-emerald-400/60 shadow-[0_0_18px_rgba(16,185,129,0.4)] hover:brightness-110",
  secondary:
    "bg-panel2 text-ink border border-edgelit hover:border-emeraldx/50 hover:text-emeraldx",
  ghost: "bg-transparent text-inkdim border border-transparent hover:bg-white/[0.04] hover:text-ink",
  danger:
    "bg-panel2 text-rosex border border-rosex/40 hover:bg-rosex/10 hover:border-rosex/70",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "secondary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-[13px] font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
