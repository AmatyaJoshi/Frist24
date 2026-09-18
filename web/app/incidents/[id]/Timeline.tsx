import { Card } from "@/components/ui";
import { formatDateTime } from "@/lib/time";
import type { AuditEvent } from "@/lib/types";

const ICON: Record<string, string> = {
  "incident.opened": "⚠",
  "report.drafted": "✎",
  "report.edited": "✏",
  "report.approved": "✓",
  "report.rejected": "✗",
  "incident.fix_available": "🔧",
  "incident.closed": "■",
};

export default function Timeline({ events }: { events: AuditEvent[] }) {
  return (
    <Card className="p-4">
      <h2 className="text-xs uppercase tracking-wide text-white/40 mb-3">Timeline · hash-chained audit log</h2>
      {events.length === 0 && <div className="text-sm text-white/40">No events yet.</div>}
      <ol className="space-y-3">
        {[...events].reverse().map((e) => (
          <li key={e.id} className="text-sm border-l border-white/10 pl-3 relative">
            <span className="absolute -left-[9px] top-0.5 h-4 w-4 rounded-full bg-[#0b0f14] border border-white/20 text-[10px] flex items-center justify-center">{ICON[e.action] ?? "•"}</span>
            <div className="flex justify-between gap-2">
              <span className="font-medium">{e.action}</span>
              <span className="text-xs text-white/40 whitespace-nowrap">{formatDateTime(e.ts)}</span>
            </div>
            <div className="text-xs text-white/50">by {e.actor}{summary(e)}</div>
            <div className="font-mono text-[10px] text-white/30 truncate" title={`prev ${e.prev_hash}\nhash ${e.hash}`}>#{e.id} {e.hash.slice(0, 16)}… ← {e.prev_hash.slice(0, 8)}…</div>
          </li>
        ))}
      </ol>
    </Card>
  );
}

function summary(e: AuditEvent): string {
  const p = e.payload as Record<string, unknown>;
  const parts: string[] = [];
  if (p.stage) parts.push(`${p.stage}/${p.language ?? ""} v${p.version ?? ""}`);
  if (p.source) parts.push(`source ${p.source}${p.model ? ` (${p.model})` : ""}`);
  if (p.changed_fields && typeof p.changed_fields === "object") parts.push(`fields: ${Object.keys(p.changed_fields as object).join(", ")}`);
  if (p.note) parts.push(`note: ${p.note}`);
  if (p.rule) parts.push(`rule ${p.rule}`);
  if (p.incident_status) parts.push(`→ ${p.incident_status}`);
  return parts.length ? " · " + parts.join(" · ") : "";
}
