import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-lg border border-white/10 bg-white/[0.02] ${className}`}>{children}</div>;
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-white/50 mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

const BADGE: Record<string, string> = {
  open: "bg-red-500/15 text-red-300 border-red-500/30",
  early_warning_approved: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  notification_approved: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  final_approved: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  closed: "bg-white/5 text-white/50 border-white/10",
  pending_review: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  approved: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  rejected: "bg-white/5 text-white/50 border-white/10",
  active: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  discontinued: "bg-white/5 text-white/60 border-white/10",
  ok: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  error: "bg-red-500/15 text-red-300 border-red-500/30",
  running: "bg-sky-500/15 text-sky-300 border-sky-500/30",
};

export function Badge({ value, className = "" }: { value: string; className?: string }) {
  return (
    <span className={`inline-block rounded border px-1.5 py-0.5 text-[11px] font-medium tracking-wide ${BADGE[value] ?? "bg-white/5 text-white/70 border-white/10"} ${className}`}>
      {value.replace(/_/g, " ")}
    </span>
  );
}

export function Empty({ title, hint }: { title: string; hint?: ReactNode }) {
  return (
    <Card className="p-10 text-center">
      <div className="text-white/70">{title}</div>
      {hint && <div className="text-sm text-white/40 mt-2">{hint}</div>}
    </Card>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="rounded border border-red-500/30 bg-red-500/10 text-red-200 text-sm px-3 py-2">{message}</div>;
}

export const btn = "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors";
export const btnPrimary = `${btn} border-amber-400/60 bg-amber-400/15 text-amber-200 hover:bg-amber-400/25`;
export const btnGhost = `${btn} border-white/15 text-white/80 hover:bg-white/5`;
export const btnDanger = `${btn} border-red-500/40 text-red-300 hover:bg-red-500/10`;
export const btnSuccess = `${btn} border-emerald-500/50 bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500/25`;
