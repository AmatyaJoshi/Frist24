import Link from "next/link";
import { getIncidents, getSyncStatus } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/time";
import { Badge, Card, Empty, ErrorBox, PageHeader } from "@/components/ui";
import Countdown from "@/components/Countdown";
import SyncButton from "./SyncButton";
import type { FeedSync, IncidentListItem } from "@/lib/types";
import { STAGE_LABEL } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function IncidentsPage() {
  let incidents: IncidentListItem[] = [];
  let syncs: FeedSync[] = [];
  let error: string | null = null;
  try {
    [incidents, syncs] = await Promise.all([getIncidents(), getSyncStatus().catch(() => [])]);
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }
  const lastKev = syncs.find((s) => s.feed === "kev");
  const open = incidents.filter((i) => i.next_deadline);
  const done = incidents.filter((i) => !i.next_deadline);

  return (
    <div>
      <PageHeader
        title="Incidents"
        subtitle={
          <>
            One incident = one product × one CVE listed in CISA KEV. Opened by rule, never by the model. Clocks start at <span className="font-mono">aware_at</span>.
            {lastKev && (
              <span className="ml-2 text-white/40">
                Last KEV sync {formatDateTime(lastKev.finished_at)} · <Badge value={lastKev.status} />
              </span>
            )}
          </>
        }
        actions={<SyncButton />}
      />
      {error && <ErrorBox message={`API unreachable: ${error}`} />}
      {!error && incidents.length === 0 && (
        <Empty title="No incidents" hint={<>Nothing in your SBOMs is currently listed in CISA KEV. Press “Sync now” or run <code>make demo</code>.</>} />
      )}
      {open.length > 0 && <IncidentTable rows={open} />}
      {done.length > 0 && (
        <>
          <h2 className="mt-8 mb-2 text-sm uppercase tracking-wide text-white/40">Completed / closed</h2>
          <IncidentTable rows={done} />
        </>
      )}
    </div>
  );
}

function IncidentTable({ rows }: { rows: IncidentListItem[] }) {
  return (
    <Card>
      <table className="w-full text-sm">
        <thead className="text-left text-xs uppercase tracking-wide text-white/40">
          <tr>
            <th className="px-4 py-3">Next deadline</th>
            <th className="px-4 py-3">Product</th>
            <th className="px-4 py-3">CVE</th>
            <th className="px-4 py-3">KEV since</th>
            <th className="px-4 py-3 text-right">EPSS</th>
            <th className="px-4 py-3 text-right">CVSS</th>
            <th className="px-4 py-3 text-right">Components</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Drafts</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((i) => (
            <tr key={i.id} className="border-t border-white/5 hover:bg-white/[0.03]">
              <td className="px-4 py-3">
                <Link href={`/incidents/${i.id}`} className="block">
                  <Countdown deadline={i.next_deadline} />
                  <div className="text-xs text-white/40">{i.next_stage ? STAGE_LABEL[i.next_stage] : "no open deadline"}</div>
                </Link>
              </td>
              <td className="px-4 py-3">
                <div className="font-mono">{i.sku}</div>
                <div className="text-xs text-white/40">{i.product_name}</div>
              </td>
              <td className="px-4 py-3">
                <Link href={`/incidents/${i.id}`} className="font-mono text-amber-200 hover:underline">{i.cve_id}</Link>
                <div className="text-xs text-white/40 max-w-xs truncate" title={i.vulnerability_name ?? ""}>{i.vulnerability_name}</div>
              </td>
              <td className="px-4 py-3 text-white/60">
                {formatDate(i.kev_date_added)}
                {i.known_ransomware_campaign_use === "Known" && <div className="text-[11px] text-red-300">ransomware use known</div>}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">{i.epss != null ? i.epss.toFixed(3) : "–"}</td>
              <td className="px-4 py-3 text-right tabular-nums">{i.cvss_score != null ? i.cvss_score.toFixed(1) : "–"}</td>
              <td className="px-4 py-3 text-right tabular-nums">{i.component_count}</td>
              <td className="px-4 py-3"><Badge value={i.status} /></td>
              <td className="px-4 py-3 text-xs text-white/60">
                {i.reports_pending > 0 && <div className="text-amber-300">{i.reports_pending} pending review</div>}
                {i.reports_approved > 0 && <div className="text-emerald-300">{i.reports_approved} approved</div>}
                {i.reports_pending + i.reports_approved === 0 && <span className="text-white/30">none</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
