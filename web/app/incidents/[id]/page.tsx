import Link from "next/link";
import { notFound } from "next/navigation";
import { getIncident, ApiError } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/time";
import { Badge, Card, ErrorBox } from "@/components/ui";
import Countdown from "@/components/Countdown";
import ReviewPanel from "./ReviewPanel";
import Timeline from "./Timeline";
import type { IncidentDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function IncidentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let inc: IncidentDetail;
  try {
    inc = await getIncident(id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    return <ErrorBox message={`API error: ${e instanceof Error ? e.message : String(e)}`} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs text-faint"><Link href="/incidents" className="hover:underline">Incidents</Link> / {inc.sku}</div>
          <h1 className="text-2xl font-semibold tracking-tight mt-1">
            <span className="font-mono text-warn">{inc.cve_id}</span> in <span className="font-mono">{inc.sku}</span>
          </h1>
          <div className="text-sm text-muted mt-1">{inc.vulnerability_name}</div>
          <div className="mt-2 flex items-center gap-2"><Badge value={inc.status} /><span className="text-xs text-faint">aware_at {formatDateTime(inc.aware_at)}</span></div>
        </div>
        <Card className="p-4 grid grid-cols-3 gap-6 text-center">
          <Deadline label="Early warning · 24h" deadline={inc.deadline_early_warning} done={inc.status !== "open"} />
          <Deadline label="Notification · 72h" deadline={inc.deadline_notification} done={["notification_approved", "final_approved", "closed"].includes(inc.status)} />
          <Deadline label={`Final report · 14d${inc.final_report_anchor === "provisional" ? " (provisional)" : ""}`} deadline={inc.deadline_final_report} done={["final_approved", "closed"].includes(inc.status)} />
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)_minmax(0,0.9fr)] gap-6">
        {/* Column 1: deterministic facts */}
        <div className="space-y-4">
          <Card className="p-4 space-y-3 text-sm">
            <h2 className="text-xs uppercase tracking-wide text-faint">Product</h2>
            <div className="font-medium">{inc.product_name}</div>
            <div className="text-muted text-xs">{inc.product_description}</div>
            <div className="flex gap-2 items-center text-xs"><Badge value={inc.lifecycle_status} /><span className="text-faint">{inc.component_count} matched component(s)</span></div>
          </Card>
          <Card className="p-4 space-y-2 text-sm">
            <h2 className="text-xs uppercase tracking-wide text-faint">CISA KEV entry <span className="text-ok/70 normal-case">· deterministic trigger</span></h2>
            <div><span className="text-faint">Added</span> {formatDate(inc.kev.date_added)} · <span className="text-faint">vendor</span> {inc.kev.vendor_project} · <span className="text-faint">product</span> {inc.kev.product}</div>
            <p className="text-fg">{inc.kev.short_description}</p>
            {inc.kev.required_action && <p className="text-muted text-xs"><span className="text-faint">Required action:</span> {inc.kev.required_action}</p>}
            <div className="text-xs text-faint">Ransomware use: {inc.kev.known_ransomware_campaign_use ?? "–"} · CWE {inc.kev.cwes?.join(", ") || "–"}</div>
          </Card>
          <Card className="p-4 space-y-2 text-sm">
            <h2 className="text-xs uppercase tracking-wide text-faint">Scores (triage only)</h2>
            <div className="grid grid-cols-2 gap-2">
              <div><div className="text-faint text-xs">EPSS (30-day exploit probability)</div><div className="font-mono text-lg">{inc.epss != null ? inc.epss.toFixed(3) : "–"}</div></div>
              <div><div className="text-faint text-xs">CVSS base</div><div className="font-mono text-lg">{inc.cvss_score != null ? inc.cvss_score.toFixed(1) : "–"}</div></div>
            </div>
            {inc.vulnerabilities[0]?.cvss_vector && <div className="font-mono text-[11px] text-faint break-all">{inc.vulnerabilities.find((v) => v.cvss_vector)?.cvss_vector}</div>}
          </Card>
          <Card className="p-4 space-y-2 text-sm">
            <h2 className="text-xs uppercase tracking-wide text-faint">Matched components (OSV, exact PURL)</h2>
            <ul className="space-y-2">
              {inc.components.map((c) => (
                <li key={c.match_id} className="border-l-2 border-ok pl-2">
                  <div className="font-mono text-xs break-all">{c.purl ?? `${c.name}@${c.version}`}</div>
                  <div className="text-[11px] text-faint">{c.osv_id} · {c.match_type} · confidence {c.confidence.toFixed(2)}{c.affected_range ? ` · ${c.affected_range}` : ""}</div>
                </li>
              ))}
            </ul>
          </Card>
          {inc.vulnerabilities.length > 0 && (
            <Card className="p-4 space-y-2 text-sm">
              <h2 className="text-xs uppercase tracking-wide text-faint">Vulnerability record (OSV)</h2>
              {inc.vulnerabilities.slice(0, 2).map((v) => (
                <div key={v.id}>
                  <div className="font-mono text-xs text-muted">{v.id}</div>
                  <div className="text-fg">{v.summary}</div>
                  {v.details && <details className="text-xs text-muted mt-1"><summary className="cursor-pointer">details</summary><pre className="whitespace-pre-wrap font-sans mt-1">{v.details.slice(0, 2000)}</pre></details>}
                </div>
              ))}
            </Card>
          )}
        </div>

        {/* Column 2: review panel (client) */}
        <ReviewPanel incident={inc} />

        {/* Column 3: timeline */}
        <div className="space-y-4">
          <Timeline events={inc.timeline} />
        </div>
      </div>
    </div>
  );
}

function Deadline({ label, deadline, done }: { label: string; deadline: string; done: boolean }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-faint">{label}</div>
      {done ? <div className="text-ok font-mono text-lg">done ✓</div> : <Countdown deadline={deadline} />}
      <div className="text-[11px] text-faint">{formatDateTime(deadline)}</div>
    </div>
  );
}
