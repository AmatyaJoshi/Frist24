import type { IncidentStatus } from "@/lib/types";

const STEPS = ["Detected", "Early warning", "Notification", "Final report", "Closed"];
const INDEX: Record<IncidentStatus, number> = { open: 1, early_warning_approved: 2, notification_approved: 3, final_approved: 4, closed: 5 };

export default function Stepper({ status }: { status: IncidentStatus }) {
  const current = INDEX[status];
  return (
    <ol className="flex w-full items-center gap-2 text-xs">
      {STEPS.map((label, idx) => {
        const n = idx + 1;
        const done = n < current || status === "closed";
        const active = n === current && status !== "closed";
        return (
          <li key={label} className="flex flex-1 items-center gap-2 last:flex-none">
            <span
              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[11px] font-medium transition-colors ${
                done ? "border-ok bg-ok-soft text-ok" : active ? "border-accent bg-accent text-white" : "border-border text-faint"
              }`}
            >
              {done ? "✓" : n}
            </span>
            <span className={`hidden whitespace-nowrap sm:inline ${active ? "font-medium text-fg" : done ? "text-ok" : "text-faint"}`}>{label}</span>
            {idx < STEPS.length - 1 && <span className={`h-px flex-1 ${done ? "bg-ok" : "bg-border"}`} />}
          </li>
        );
      })}
    </ol>
  );
}
