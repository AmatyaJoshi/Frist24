"use client";

import { useEffect, useState } from "react";
import { formatCountdown, remainingMs, urgency, type Urgency } from "@/lib/time";

const COLOR: Record<Urgency, string> = {
  ok: "text-ok",
  warn: "text-warn",
  critical: "text-danger",
  overdue: "text-danger",
};

export default function Countdown({ deadline, label, compact = false }: { deadline: string | null; label?: string; compact?: boolean }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!deadline) return <span className="text-faint font-mono">—</span>;
  if (now === null) return <span className="font-mono text-faint">--:--:--</span>;
  const ms = remainingMs(deadline, now);
  const u = urgency(ms);
  return (
    <span className={`font-mono tabular-nums ${COLOR[u]} ${compact ? "" : "text-lg"}`} title={new Date(deadline).toISOString()}>
      {formatCountdown(ms)}
      {label && <span className="ml-2 text-xs text-muted font-sans">{label}</span>}
      {u === "overdue" && <span className="ml-2 text-xs font-sans uppercase tracking-wide">overdue</span>}
    </span>
  );
}
