// Countdown helpers (pure; unit-tested with vitest).

export type Urgency = "ok" | "warn" | "critical" | "overdue";

export function remainingMs(deadlineIso: string, now: number = Date.now()): number {
  return new Date(deadlineIso).getTime() - now;
}

/** "23:59:12" style, or "-01:12:03" when overdue. Hours are not capped at 24. */
export function formatCountdown(ms: number): string {
  const neg = ms < 0;
  let s = Math.floor(Math.abs(ms) / 1000);
  const h = Math.floor(s / 3600);
  s -= h * 3600;
  const m = Math.floor(s / 60);
  s -= m * 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${neg ? "-" : ""}${pad(h)}:${pad(m)}:${pad(s)}`;
}

/** Colour thresholds: >6h ok, 1–6h warn, <1h critical, past = overdue. */
export function urgency(ms: number): Urgency {
  if (ms < 0) return "overdue";
  if (ms < 60 * 60 * 1000) return "critical";
  if (ms < 6 * 60 * 60 * 1000) return "warn";
  return "ok";
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "–";
  const d = new Date(iso);
  return d.toLocaleString("en-GB", { timeZone: "Europe/Berlin", hour12: false, dateStyle: "medium", timeStyle: "short" }) + " CE(S)T";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "–";
  return new Date(iso).toLocaleDateString("en-GB", { dateStyle: "medium" });
}
