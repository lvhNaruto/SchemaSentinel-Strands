"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { SentinelState } from "@/types";

/**
 * Server-authoritative dashboard state:
 * - SSE (/api/events) pushes a notification on every real telemetry event
 * - the hook refetches the full snapshot on each event
 * - a 3s poll is kept as a REST fallback (also covers SSE reconnects)
 */
export function useSentinel() {
  const [state, setState] = useState<SentinelState | null>(null);
  const [connected, setConnected] = useState(false);
  const inflight = useRef(false);

  const refresh = useCallback(async () => {
    if (inflight.current) return;
    inflight.current = true;
    try {
      const next = await api.state();
      setState(next);
      setConnected(true);
    } catch {
      setConnected(false);
    } finally {
      inflight.current = false;
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    let es: EventSource | null = null;
    try {
      es = new EventSource("/api/events");
      es.addEventListener("telemetry", refresh);
      es.addEventListener("ready", () => setConnected(true));
      es.onerror = () => setConnected(false);
      es.onopen = () => setConnected(true);
    } catch {
      // SSE unsupported — the 3s poll still drives the UI
    }
    return () => {
      clearInterval(timer);
      es?.close();
    };
  }, [refresh]);

  return { state, connected, refresh };
}
