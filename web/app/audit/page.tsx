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
        subtitle={<>Append-only (database trigger) and hash-chained: each row&apos;s hash covers its content plus the previous hash. {total} rows.</>}
        actions={<VerifyButton />}
      />
      {error && <ErrorBox message={`API unreachable: ${error}`} />}
      {!error && items.length === 0 && <Empty title="Empty audit log" />}
      {items.length > 0 && (
        <Card>
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-white/40">
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
                <tr key={e.id} className="border-t border-white/5 hover:bg-white/[0.03] align-top">
                  <td className="px-4 py-2 font-mono text-white/40">{e.id}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-white/70">{formatDateTime(e.ts)}</td>
                  <td className="px-4 py-2">{e.actor}</td>
                  <td className="px-4 py-2 font-medium">{e.action}</td>
                  <td className="px-4 py-2 text-xs text-white/60">{e.entity_type}{e.entity_id && <div className="font-mono text-white/30 truncate max-w-[10rem]" title={e.entity_id}>{e.entity_id}</div>}</td>
                  <td className="px-4 py-2 text-xs text-white/60 max-w-md">
                    <details><summary className="cursor-pointer truncate">{shortPayload(e.payload)}</summary><pre className="mt-1 whitespace-pre-wrap break-all text-[11px] text-white/50">{JSON.stringify(e.payload, null, 1)}</pre></details>
                  </td>
                  <td className="px-4 py-2 font-mono text-[10px] text-white/40">
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
