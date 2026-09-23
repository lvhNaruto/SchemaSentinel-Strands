"use client";

import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface TabDef {
  key: string;
  label: ReactNode;
  content: ReactNode;
}

/** Keyboard-accessible tabs (arrow keys + Home/End) with proper ARIA roles. */
export function Tabs({
  tabs,
  className,
  panelClassName,
}: {
  tabs: TabDef[];
  className?: string;
  panelClassName?: string;
}) {
  const [active, setActive] = useState(0);

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight") setActive((a) => (a + 1) % tabs.length);
    else if (e.key === "ArrowLeft") setActive((a) => (a - 1 + tabs.length) % tabs.length);
    else if (e.key === "Home") setActive(0);
    else if (e.key === "End") setActive(tabs.length - 1);
    else return;
    e.preventDefault();
  };

  return (
    <div className={className}>
      <div role="tablist" onKeyDown={onKeyDown} className="flex flex-wrap gap-1.5">
        {tabs.map((t, i) => (
          <button
            key={t.key}
            role="tab"
            id={`tab-${t.key}`}
            aria-selected={i === active}
            aria-controls={`panel-${t.key}`}
            tabIndex={i === active ? 0 : -1}
            onClick={() => setActive(i)}
            className={cn(
              "rounded-lg border px-3.5 py-1.5 text-[12.5px] font-semibold transition-colors",
              i === active
                ? "border-emerald-400/50 bg-emerald-400/10 text-emeraldx"
                : "border-edge bg-panel2/60 text-inkdim hover:text-ink"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tabs.map((t, i) => (
        <div
          key={t.key}
          role="tabpanel"
          id={`panel-${t.key}`}
          aria-labelledby={`tab-${t.key}`}
          hidden={i !== active}
          className={cn("mt-3", panelClassName)}
        >
          {t.content}
        </div>
      ))}
    </div>
  );
}
