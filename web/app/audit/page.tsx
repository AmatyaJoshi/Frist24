import Link from "next/link";
import { getAudit } from "@/lib/api";
import { formatDateTime } from "@/lib/time";
import { Badge, Card, Empty, ErrorBox, PageHeader } from "@/components/ui";
import VerifyButton from "./VerifyButton";
import type { AuditEvent } from "@/lib/types";

export const dynamic = "force-dynamic";

const TONE: Record<string, "ok" | "warn" | "danger" | "info" | "neutral"> = {
  "incident.opened": "danger",
  "report.drafted": "info",
  "report.edited": "warn",
  "report.approved": "ok",
  "report.rejected": "neutral",
  "incident.fix_available": "info",
  "incident.closed": "neutral",
  "sbom.ingested": "info",
  "product.created": "neutral",
  "feed.synced": "neutral",
  "settings.updated": "warn",
  "package.exported": "ok",
  "notification.sent": "ok",
  "notification.failed": "danger",
};

export default async function AuditPage({ searchParams }: { searchParams: Promise<{ action?: string; page?: string }> }) {
  const { action = "", page = "1" } = await searchParams;
  const pageNo = Math.max(1, parseInt(page, 10) || 1);
  const limit = 100;
  let items: AuditEvent[] = [];
  let total = 0;
  let error: string | null = null;
  try {
    const r = await getAudit(limit, (pageNo - 1) * limit, action || undefined);
    items = r.items;
    total = r.total;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }
  const pages = Math.max(1, Math.ceil(total / limit));
  const kinds = ["", "incident", "report", "sbom", "product", "feed", "settings", "package", "notification"];

  return (
    <div className="space-y-4">
      <PageHeader title="Audit Log" subtitle={<>Append-only and hash-chained. {total.toLocaleString()} rows.</>} actions={<VerifyButton />} />
      {error && <ErrorBox message={`API unreachable: ${error}`} />}

      <div className="flex flex-wrap items-center gap-1 text-xs">
        {kinds.map((k) => (
          <Link key={k || "all"} href={k ? `/audit?action=${k}` : "/audit"} className={`rounded-md border px-2 py-1 uppercase tracking-wide transition-colors ${action === k ? "border-border-strong bg-surface-3 text-fg" : "border-border bg-surface text-muted hover:text-fg"}`}>
            {k || "ALL"}
          </Link>
        ))}
        {pages > 1 && (
          <span className="ml-auto flex items-center gap-2 text-faint">
            Page {pageNo} / {pages}
            {pageNo > 1 && <Link className="text-accent hover:underline" href={`/audit?action=${action}&page=${pageNo - 1}`}>← Newer</Link>}
            {pageNo < pages && <Link className="text-accent hover:underline" href={`/audit?action=${action}&page=${pageNo + 1}`}>Older →</Link>}
          </span>
        )}
      </div>

      {!error && items.length === 0 && <Empty title="No audit rows match" />}
      {items.length > 0 && (
        <Card className="overflow-hidden">
          <div className="hidden grid-cols-[3.5rem_10.5rem_11rem_minmax(0,1fr)_9rem] gap-3 border-b border-border bg-surface-2 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-faint md:grid">
            <span>#</span><span>When</span><span>Action</span><span>Details</span><span className="text-right">Chain</span>
          </div>
          <ol>
            {items.map((e) => (
              <li key={e.id} className="grid grid-cols-1 gap-2 border-t border-border px-4 py-2.5 text-sm first:border-t-0 hover:bg-surface-2 md:grid-cols-[3.5rem_10.5rem_11rem_minmax(0,1fr)_9rem] md:items-start md:gap-3">
                <span className="font-mono text-xs text-faint">{e.id}</span>
                <span className="text-xs text-muted">{formatDateTime(e.ts)}</span>
                <span><Badge value={e.action.replace(".", " ")} tone={TONE[e.action] ?? "neutral"} /></span>
                <div className="min-w-0">
                  <div className="truncate"><span className="text-muted">{e.actor}</span>{detail(e) && <span className="text-fg"> · {detail(e)}</span>}</div>
                  <details className="text-xs text-faint">
                    <summary className="cursor-pointer select-none hover:text-fg">{e.entity_type}{e.entity_id ? ` ${e.entity_id.slice(0, 8)}…` : ""} · payload</summary>
                    <pre className="mt-1 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded-md bg-surface-2 p-2 text-[11px] text-muted">{JSON.stringify(e.payload, null, 1)}</pre>
                  </details>
                </div>
                <span className="font-mono text-[10px] leading-4 text-faint md:text-right" title={`hash ${e.hash}\nprev ${e.prev_hash}`}>
                  <span className="block">{e.hash.slice(0, 10)}…</span>
                  <span className="block">← {e.prev_hash.slice(0, 10)}…</span>
                </span>
              </li>
            ))}
          </ol>
        </Card>
      )}
    </div>
  );
}

function detail(e: AuditEvent): string {
  const p = e.payload as Record<string, unknown>;
  const parts: string[] = [];
  if (p.sku) parts.push(String(p.sku));
  if (p.cve_id) parts.push(String(p.cve_id));
  if (p.stage) parts.push(`${p.stage}/${p.language ?? ""} v${p.version ?? ""}`);
  if (p.source) parts.push(String(p.source));
  if (p.component_count != null) parts.push(`${p.component_count} components`);
  if (p.changed_fields && typeof p.changed_fields === "object") parts.push(`fields: ${Object.keys(p.changed_fields as object).join(", ")}`);
  if (p.changed && typeof p.changed === "object") parts.push(`settings: ${Object.keys(p.changed as object).join(", ")}`);
  if (p.note) parts.push(`"${String(p.note).slice(0, 60)}"`);
  if (p.synthetic_history) parts.push("demo history");
  return parts.join(" · ");
}
