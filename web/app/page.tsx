import Link from "next/link";
import { getHealth, getIncidents, getProducts, getSyncStatus } from "@/lib/api";
import { formatDateTime } from "@/lib/time";
import { Badge, Card, SectionTitle } from "@/components/ui";
import Countdown from "@/components/Countdown";
import type { FeedSync, IncidentListItem, Product } from "@/lib/types";
import { STAGE_LABEL } from "@/lib/types";

export const dynamic = "force-dynamic";

function nextAction(i: IncidentListItem): { label: string; tone: "danger" | "warn" | "info" } {
  if (!i.next_stage) return { label: "Resolved", tone: "info" };
  if (i.reports_pending > 0) return { label: "Review & Approve Draft", tone: "warn" };
  return { label: `Draft ${STAGE_LABEL[i.next_stage].split(" (")[0]}`, tone: "danger" };
}

export default async function Home() {
  const health = await getHealth();
  let products: Product[] = [];
  let incidents: IncidentListItem[] = [];
  let syncs: FeedSync[] = [];
  if (health) {
    [products, incidents, syncs] = await Promise.all([getProducts().catch(() => []), getIncidents().catch(() => []), getSyncStatus().catch(() => [])]);
  }
  const open = incidents.filter((i) => i.next_deadline);
  const resolved = incidents.length - open.length;
  const needsAction = open.filter((i) => i.reports_pending > 0 || i.reports_approved === 0);
  const atRisk = new Set(open.map((i) => i.product_id)).size;
  const kev = syncs.find((s) => s.feed === "kev");
  const modelReady = (health?.ollama.models?.length ?? 0) > 0;
  const since = incidents.length ? new Date(Math.min(...incidents.map((i) => Date.parse(i.aware_at)))) : null;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Compliance Overview</h1>
          <p className="mt-1 text-sm text-muted">CRA Article 14. What needs your decision, and how long you have.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-faint">
          <span>KEV {kev ? formatDateTime(kev.finished_at) : "not synced"}</span>
          <Badge value={health ? "ok" : "error"} />
          {health && !modelReady && <span className="text-warn anim-pulse">model pulling…</span>}
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4 stagger">
        <Stat label="Needs Your Action" value={needsAction.length} sub="Drafts to write or approve" href="/incidents" accent={needsAction.length > 0} />
        <Stat label="Open Incidents" value={open.length} sub={`${atRisk} product${atRisk === 1 ? "" : "s"} affected`} href="/incidents" />
        <Stat label="Resolved" value={resolved} sub={since ? `since ${since.getFullYear()}` : "—"} href="/incidents" />
        <Stat label="Products Monitored" value={products.length} sub={`${products.reduce((a, p) => a + p.component_count, 0).toLocaleString()} components`} href="/products" />
      </section>

      <Card className="overflow-x-auto">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <SectionTitle>Action Queue · Sorted by Deadline</SectionTitle>
          <Link href="/incidents" className="text-xs text-accent hover:underline">All Incidents</Link>
        </div>
        {open.length === 0 ? (
          <div className="px-4 py-10 text-center text-sm text-muted">Nothing due. Feeds are checked every 15 minutes.</div>
        ) : (
          <table className="w-full text-sm">
            <tbody>
              {open.slice(0, 8).map((i) => {
                const a = nextAction(i);
                return (
                  <tr key={i.id} className="border-t border-border first:border-t-0 hover:bg-surface-2">
                    <td className="w-40 px-4 py-3">
                      <Countdown deadline={i.next_deadline} />
                      <div className="text-[11px] text-faint">{i.next_stage ? STAGE_LABEL[i.next_stage] : ""}</div>
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/incidents/${i.id}`} className="font-mono hover:underline">{i.sku}</Link>
                      <div className="hidden text-xs text-faint sm:block">{i.product_name}</div>
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/incidents/${i.id}`} className="font-mono text-accent hover:underline">{i.cve_id}</Link>
                      <div className="hidden max-w-xs truncate text-xs text-faint md:block">{i.vulnerability_name}</div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link href={`/incidents/${i.id}`}><Badge value={a.label} tone={a.tone} /></Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>

      <section className="grid grid-cols-1 gap-3 md:grid-cols-3 stagger text-sm">
        <Pill n="1" t="Detected by Rule" b="A component matches a CVE on CISA KEV. The incident and its 24h clock open automatically." />
        <Pill n="2" t="Drafted Locally" b="The local model fills the amber text fields. Green facts come from your database." />
        <Pill n="3" t="Approved by You" b="Review, approve, export the filing package. Every step is in the audit log." />
      </section>
    </div>
  );
}

function Stat({ label, value, sub, href, accent = false }: { label: string; value: number; sub?: string; href: string; accent?: boolean }) {
  return (
    <Link href={href}>
      <Card className="p-4 transition-colors hover:bg-surface-2">
        <SectionTitle>{label}</SectionTitle>
        <div className={`mt-1 text-3xl font-semibold tabular-nums ${accent ? "text-danger" : ""}`}>{value}</div>
        {sub && <div className="text-xs text-faint">{sub}</div>}
      </Card>
    </Link>
  );
}

function Pill({ n, t, b }: { n: string; t: string; b: string }) {
  return (
    <Card className="flex gap-3 p-4">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-soft font-mono text-xs text-accent">{n}</span>
      <div>
        <div className="font-medium">{t}</div>
        <p className="text-muted">{b}</p>
      </div>
    </Card>
  );
}
