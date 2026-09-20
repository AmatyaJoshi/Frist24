"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import Countdown from "@/components/Countdown";
import { Badge, Card, Empty, input } from "@/components/ui";
import { formatDate } from "@/lib/time";
import { STAGE_LABEL, type IncidentListItem, type IncidentStatus } from "@/lib/types";

const STATUSES: (IncidentStatus | "all")[] = ["all", "open", "early_warning_approved", "notification_approved", "final_approved", "closed"];

export default function IncidentTable({ rows }: { rows: IncidentListItem[] }) {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<(typeof STATUSES)[number]>("all");
  const [showDone, setShowDone] = useState(false);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter((i) => {
      if (status !== "all" && i.status !== status) return false;
      if (!showDone && status === "all" && !i.next_deadline) return false;
      if (!needle) return true;
      return [i.sku, i.product_name, i.cve_id, i.vulnerability_name ?? ""].some((s) => s.toLowerCase().includes(needle));
    });
  }, [rows, q, status, showDone]);

  const doneCount = rows.filter((i) => !i.next_deadline).length;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <input className={`${input} max-w-xs`} placeholder="Search SKU, product, CVE…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search incidents" />
        <div className="flex flex-wrap gap-1 text-xs">
          {STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`rounded-md border px-2 py-1 transition-colors ${status === s ? "border-border-strong bg-surface-3 text-fg" : "border-border bg-surface text-muted hover:text-fg"}`}
            >
              {s === "all" ? "All" : s.replace(/_/g, " ")}
            </button>
          ))}
        </div>
        {doneCount > 0 && status === "all" && (
          <label className="ml-auto flex items-center gap-2 text-xs text-muted">
            <input type="checkbox" checked={showDone} onChange={(e) => setShowDone(e.target.checked)} /> show {doneCount} completed
          </label>
        )}
      </div>

      {filtered.length === 0 ? (
        <Empty title="No incidents match" hint="Adjust the search or status filter." />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-[11px] uppercase">
              <tr>
                <th className="px-4 py-2.5">Next deadline</th>
                <th className="px-4 py-2.5">Product</th>
                <th className="px-4 py-2.5">CVE</th>
                <th className="px-4 py-2.5">KEV since</th>
                <th className="px-4 py-2.5 text-right">EPSS</th>
                <th className="px-4 py-2.5 text-right">CVSS</th>
                <th className="px-4 py-2.5 text-right">Components</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Drafts</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((i) => (
                <tr key={i.id} className="border-t border-border hover:bg-surface-2">
                  <td className="px-4 py-3">
                    <Link href={`/incidents/${i.id}`} className="block">
                      <Countdown deadline={i.next_deadline} />
                      <div className="text-xs text-faint">{i.next_stage ? STAGE_LABEL[i.next_stage] : "no open deadline"}</div>
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/products/${i.product_id}`} className="font-mono hover:underline">{i.sku}</Link>
                    <div className="text-xs text-faint">{i.product_name}</div>
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/incidents/${i.id}`} className="font-mono text-accent hover:underline">{i.cve_id}</Link>
                    <div className="text-xs text-faint max-w-xs truncate" title={i.vulnerability_name ?? ""}>{i.vulnerability_name}</div>
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {formatDate(i.kev_date_added)}
                    {i.known_ransomware_campaign_use === "Known" && <div className="text-[11px] text-danger">ransomware use known</div>}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{i.epss != null ? i.epss.toFixed(3) : "–"}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{i.cvss_score != null ? i.cvss_score.toFixed(1) : "–"}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{i.component_count}</td>
                  <td className="px-4 py-3"><Badge value={i.status} /></td>
                  <td className="px-4 py-3 text-xs">
                    {i.reports_pending > 0 && <div className="text-warn">{i.reports_pending} pending review</div>}
                    {i.reports_approved > 0 && <div className="text-ok">{i.reports_approved} approved</div>}
                    {i.reports_pending + i.reports_approved === 0 && <span className="text-faint">none</span>}
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
