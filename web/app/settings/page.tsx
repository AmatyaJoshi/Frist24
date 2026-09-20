import { getSettings, getSyncStatus } from "@/lib/api";
import { formatDateTime } from "@/lib/time";
import { Badge, Card, ErrorBox, PageHeader, SectionTitle } from "@/components/ui";
import type { FeedSync, Settings } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  let s: Settings | null = null;
  let syncs: FeedSync[] = [];
  let error: string | null = null;
  try {
    [s, syncs] = await Promise.all([getSettings(), getSyncStatus().catch(() => [])]);
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }
  if (error || !s) return <ErrorBox message={`API unreachable: ${error ?? "no settings"}`} />;

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Read-only view of the running configuration. Values come from environment variables (.env); change them there and restart the API."
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 stagger">
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Manufacturer (FACT fields in every report)</SectionTitle>
          <Row k="Name" v={s.manufacturer.name} env="FRIST24_MANUFACTURER_NAME" />
          <Row k="Contact" v={s.manufacturer.contact} env="FRIST24_MANUFACTURER_CONTACT" />
        </Card>
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Local model</SectionTitle>
          <Row k="Ollama" v={s.llm.url} env="OLLAMA_URL" />
          <Row k="Model" v={s.llm.model} env="OLLAMA_MODEL" />
          <Row k="Fallback" v={s.llm.fallback_model} env="OLLAMA_FALLBACK_MODEL" />
          <div className="flex justify-between gap-4"><span className="text-muted">Status</span>{s.llm.ready ? <Badge value="ok" /> : <Badge value="error" />}</div>
          <div className="text-xs text-faint">pulled: {s.llm.available_models.join(", ") || "none yet"}</div>
        </Card>
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Feeds and sync</SectionTitle>
          <Row k="CISA KEV" v={s.feeds.kev_url} env="KEV_URL" />
          <Row k="FIRST EPSS" v={s.feeds.epss_csv_url} env="EPSS_CSV_URL" />
          <Row k="OSV.dev" v={s.feeds.osv_api_url} env="OSV_API_URL" />
          <Row k="Interval" v={`${s.sync.interval_minutes} min · ${s.sync.enabled ? "enabled" : "disabled"}`} env="SYNC_INTERVAL_MINUTES / SYNC_ENABLED" />
          <div className="pt-2">
            <SectionTitle>Last runs</SectionTitle>
            <ul className="mt-1 space-y-1 text-xs">
              {syncs.slice(0, 8).map((r) => (
                <li key={r.id} className="flex items-center gap-2">
                  <Badge value={r.status} /> <span className="font-mono">{r.feed}</span>
                  <span className="text-faint">{formatDateTime(r.finished_at)}</span>
                  <span className="text-faint truncate" title={r.message ?? ""}>{r.message}</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Egress allow-list</SectionTitle>
          <p className="text-xs text-muted">The API refuses to contact any other host. Logged at startup, asserted before every feed call.</p>
          <ul className="font-mono text-xs space-y-0.5">
            {s.outbound_allowlist.map((h) => <li key={h}>{h}</li>)}
            <li className="text-faint">+ {s.llm.url} (local model)</li>
          </ul>
          <div className="pt-2">
            <SectionTitle>Alerts</SectionTitle>
            {s.notifications.webhook_configured ? (
              <p className="text-xs">New incidents are POSTed as JSON to <span className="font-mono">{s.notifications.webhook_host}</span> (NOTIFY_WEBHOOK_URL).</p>
            ) : (
              <p className="text-xs text-muted">No webhook configured. Set <span className="font-mono">NOTIFY_WEBHOOK_URL</span> (Slack, Teams, PagerDuty, your ticketing system) to be alerted the moment an incident opens.</p>
            )}
          </div>
        </Card>
      </div>
      <p className="mt-6 text-xs text-faint">Frist24 API {s.version}</p>
    </div>
  );
}

function Row({ k, v, env }: { k: string; v: string; env?: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted">{k}</span>
      <span className="text-right break-all">
        {v}
        {env && <span className="block text-[10px] font-mono text-faint">{env}</span>}
      </span>
    </div>
  );
}
