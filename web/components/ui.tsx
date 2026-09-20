import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-xl border border-border bg-surface shadow-(--shadow) ${className}`}>{children}</div>;
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted leading-relaxed">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

type Tone = "ok" | "warn" | "danger" | "info" | "neutral";
const TONE: Record<string, Tone> = {
  open: "danger",
  early_warning_approved: "warn",
  notification_approved: "info",
  final_approved: "ok",
  closed: "neutral",
  pending_review: "warn",
  approved: "ok",
  rejected: "neutral",
  active: "ok",
  discontinued: "neutral",
  ok: "ok",
  error: "danger",
  running: "info",
  llm: "info",
  template: "neutral",
  human: "ok",
};
const TONE_CLASS: Record<Tone, string> = {
  ok: "bg-ok-soft text-ok border-ok/30",
  warn: "bg-warn-soft text-warn border-warn/30",
  danger: "bg-danger-soft text-danger border-danger/30",
  info: "bg-info-soft text-info border-info/30",
  neutral: "bg-surface-2 text-muted border-border",
};

export function Badge({ value, tone, className = "" }: { value: string; tone?: Tone; className?: string }) {
  const t = tone ?? TONE[value] ?? "neutral";
  return (
    <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[11px] font-medium tracking-wide whitespace-nowrap ${TONE_CLASS[t]} ${className}`}>
      {value.replace(/_/g, " ")}
    </span>
  );
}

export function Empty({ title, hint }: { title: string; hint?: ReactNode }) {
  return (
    <Card className="p-12 text-center">
      <div className="text-fg font-medium">{title}</div>
      {hint && <div className="mt-2 text-sm text-muted">{hint}</div>}
    </Card>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{message}</div>;
}

export function SectionTitle({ children, hint }: { children: ReactNode; hint?: ReactNode }) {
  return (
    <h2 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-faint">
      {children}
      {hint && <span className="normal-case font-normal tracking-normal text-faint/80">{hint}</span>}
    </h2>
  );
}

export function Spinner() {
  return <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />;
}

export const btn =
  "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40";
export const btnPrimary = `${btn} border-accent bg-accent text-white hover:brightness-110 shadow-(--shadow)`;
export const btnGhost = `${btn} border-border bg-surface text-fg hover:bg-surface-2`;
export const btnDanger = `${btn} border-danger/40 bg-surface text-danger hover:bg-danger-soft`;
export const btnSuccess = `${btn} border-ok/40 bg-ok-soft text-ok hover:brightness-95`;
export const input = "w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm text-fg placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 transition";
