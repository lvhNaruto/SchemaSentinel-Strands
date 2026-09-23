import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function formatLatency(ms: number | null | undefined): string {
  if (ms == null || Number.isNaN(ms)) return "—";
  const seconds = Number(ms) / 1000;
  if (seconds < 0.01) return `${seconds.toFixed(3)}s`;
  if (seconds < 1) return `${seconds.toFixed(2)}s`;
  return `${seconds.toFixed(1)}s`;
}
