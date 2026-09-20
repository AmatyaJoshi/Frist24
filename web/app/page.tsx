import Link from "next/link";
import { getHealth, getIncidents, getProducts, getSyncStatus } from "@/lib/api";
import { formatDateTime } from "@/lib/time";
import { Badge, Card } from "@/components/ui";
import Countdown from "@/components/Countdown";
import type { FeedSync, IncidentListItem, Product } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  const health = await getHealth();
  let products: Product[] = [];
  let incidents: IncidentListItem[] = [];
  let syncs: FeedSync[] = [];
  if (health) {
    [products, incidents, syncs] = await Promise.all([getProducts().catch(() => []), getIncidents().catch(() => []), getSyncStatus().catch(() => [])]);
  }
  const open = incidents.filter((i) => i.next_deadline);
  const soonest = open[0];
  const kev = syncs.find((s) => s.feed === "kev");
  const modelReady = (health?.ollama.models?.length ?? 0) > 0;

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">CRA Article 14, without the panic.</h1>
        <p className="max-w-3xl text-muted leading-relaxed">
          Frist24 watches your SBOMs against CISA KEV, FIRST EPSS and OSV.dev, opens an incident the moment a component is listed as
          actively exploited, and starts the 24h / 72h / 14d clock. A local model drafts the ENISA reports. You approve. Everything is
          logged in a hash-chained audit trail. No vulnerability data leaves this machine.
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-4 gap-4 stagger">
        <Stat label="Products" value={String(products.length)} href="/products" sub={`${products.reduce((a, p) => a + p.component_count, 0)} components`} />
        <Stat label="Open incidents" value={String(open.length)} href="/incidents" sub={`${incidents.length - open.length} completed`} accent={open.length > 0} />
        <Card className="p-4">
          <div className="text-xs uppercase tracking-wide text-faint">Soonest deadline</div>
          {soonest ? (
            <Link href={`/incidents/${soonest.id}`} className="block mt-1">
              <Countdown deadline={soonest.next_deadline} />
              <div className="text-xs text-muted font-mono">{soonest.sku} · {soonest.cve_id}</div>
            </Link>
          ) : (
            <div className="mt-1 text-faint">—</div>
          )}
        </Card>
        <Card className="p-4 text-sm space-y-1">
          <div className="text-xs uppercase tracking-wide text-faint">System</div>
          <div className="flex justify-between"><span>API</span><Badge value={health ? "ok" : "error"} /></div>
          <div className="flex justify-between"><span>Database</span><Badge value={health?.db === "ok" ? "ok" : "error"} /></div>
          <div className="flex justify-between"><span>Local model</span>{modelReady ? <Badge value="ok" /> : <span className="text-xs text-warn">pulling…</span>}</div>
          <div className="text-[11px] text-faint">{health?.ollama.models?.join(", ") || health?.ollama.target}</div>
          <div className="text-[11px] text-faint">KEV sync: {kev ? formatDateTime(kev.finished_at) : "never"}</div>
        </Card>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm stagger">
        <Step n="1" title="Deterministic trigger" body="A component's PURL matches a CVE that CISA lists as actively exploited (KEV). That rule, and only that rule, opens an incident and sets aware_at." />
        <Step n="2" title="Local drafting" body="Ollama drafts the early warning and the 72h notification in EN and DE. FACT fields are stamped from the database; the model only writes TEXT fields." />
        <Step n="3" title="Human approval, hash-chained" body="Every draft is pending_review. You edit, approve, export the filing package and submit it yourself. Each step is an append-only audit row." />
      </section>
    </div>
  );
}

function Stat({ label, value, sub, href, accent = false }: { label: string; value: string; sub?: string; href: string; accent?: boolean }) {
  return (
    <Link href={href}>
      <Card className="p-4 hover:bg-surface-2">
        <div className="text-xs uppercase tracking-wide text-faint">{label}</div>
        <div className={`text-3xl font-semibold tabular-nums ${accent ? "text-danger" : ""}`}>{value}</div>
        {sub && <div className="text-xs text-faint">{sub}</div>}
      </Card>
    </Link>
  );
}

function Step({ n, title, body }: { n: string; title: string; body: string }) {
  return (
    <Card className="p-4">
      <div className="text-xs text-warn font-mono">step {n}</div>
      <div className="font-medium mt-1">{title}</div>
      <p className="text-muted mt-1">{body}</p>
    </Card>
  );
}
