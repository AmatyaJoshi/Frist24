"use client";

import { useEffect, useState } from "react";
import { formatCountdown, remainingMs, urgency, type Urgency } from "@/lib/time";

const COLOR: Record<Urgency, string> = {
  ok: "text-emerald-300",
  warn: "text-amber-300",
  critical: "text-red-400",
  overdue: "text-red-500",
};

export default function Countdown({ deadline, label, compact = false }: { deadline: string | null; label?: string; compact?: boolean }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!deadline) return <span className="text-white/40 font-mono">—</span>;
  if (now === null) return <span className="font-mono text-white/40">--:--:--</span>;
  const ms = remainingMs(deadline, now);
  const u = urgency(ms);
  return (
    <span className={`font-mono tabular-nums ${COLOR[u]} ${compact ? "" : "text-lg"}`} title={new Date(deadline).toISOString()}>
      {formatCountdown(ms)}
      {label && <span className="ml-2 text-xs text-white/50 font-sans">{label}</span>}
      {u === "overdue" && <span className="ml-2 text-xs font-sans uppercase tracking-wide">overdue</span>}
    </span>
  );
}
