import { getAudit } from "@/lib/api";
import { formatDateTime } from "@/lib/time";
import { Card, Empty, ErrorBox, PageHeader } from "@/components/ui";
import VerifyButton from "./VerifyButton";
import type { AuditEvent } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function AuditPage() {
  let items: AuditEvent[] = [];
  let total = 0;
  let error: string | null = null;
  try {
    const r = await getAudit(300);
    items = r.items;
    total = r.total;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }
  return (
    <div>
      <PageHeader
        title="Audit log"
        subtitle={<>Append-only and hash-chained. {total} rows.</>}
        actions={<VerifyButton />}
      />
      {error && <ErrorBox message={`API unreachable: ${error}`} />}
      {!error && items.length === 0 && <Empty title="Empty audit log" />}
      {items.length > 0 && (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-faint">
              <tr>
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">When (CE(S)T)</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Payload</th>
                <th className="px-4 py-3">Chain</th>
              </tr>
            </thead>
            <tbody>
              {items.map((e) => (
                <tr key={e.id} className="border-t border-border hover:bg-surface-2 align-top">
                  <td className="px-4 py-2 font-mono text-faint">{e.id}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-muted">{formatDateTime(e.ts)}</td>
                  <td className="px-4 py-2">{e.actor}</td>
                  <td className="px-4 py-2 font-medium">{e.action}</td>
                  <td className="px-4 py-2 text-xs text-muted">{e.entity_type}{e.entity_id && <div className="font-mono text-faint truncate max-w-[10rem]" title={e.entity_id}>{e.entity_id}</div>}</td>
                  <td className="px-4 py-2 text-xs text-muted max-w-md">
                    <details><summary className="cursor-pointer truncate">{shortPayload(e.payload)}</summary><pre className="mt-1 whitespace-pre-wrap break-all text-[11px] text-muted">{JSON.stringify(e.payload, null, 1)}</pre></details>
                  </td>
                  <td className="px-4 py-2 font-mono text-[10px] text-faint">
                    <div title={e.hash}>hash {e.hash.slice(0, 12)}…</div>
                    <div title={e.prev_hash}>prev {e.prev_hash.slice(0, 12)}…</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function shortPayload(p: Record<string, unknown>): string {
  const keys = Object.keys(p);
  if (keys.length === 0) return "{}";
  return keys.slice(0, 4).map((k) => `${k}: ${typeof p[k] === "object" ? "…" : String(p[k]).slice(0, 40)}`).join(" · ");
}
