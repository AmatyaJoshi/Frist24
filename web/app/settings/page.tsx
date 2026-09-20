import { getSettings, getSyncStatus } from "@/lib/api";
import { formatDateTime } from "@/lib/time";
import { Badge, Card, ErrorBox, PageHeader, SectionTitle } from "@/components/ui";
import SettingsForm from "./SettingsForm";
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
  if (error || !s)
    return (
      <div className="space-y-3">
        <PageHeader title="Settings" />
        <ErrorBox message={error?.includes("Not Found") ? "The running API is older than this UI. Rebuild the api container: docker compose up -d --build" : `API unreachable: ${error ?? "no settings"}`} />
      </div>
    );

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" subtitle="Organisation settings are saved in the database and audited. Infrastructure values come from .env." />

      <SettingsForm initial={s.editable} memberStates={s.eu_member_states} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 stagger">
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Local model</SectionTitle>
          <Row k="Endpoint" v={s.llm.url} />
          <Row k="Model" v={s.llm.model} />
          <Row k="Fallback" v={s.llm.fallback_model} />
          <div className="flex justify-between gap-4"><span className="text-muted">Status</span><Badge value={s.llm.ready ? "ok" : "error"} /></div>
          <div className="text-xs text-faint">pulled: {s.llm.available_models.join(", ") || "none yet"}</div>
        </Card>
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Feeds · every {s.sync.interval_minutes} min{s.sync.enabled ? "" : " (disabled)"}</SectionTitle>
          <Row k="CISA KEV" v={host(s.feeds.kev_url)} />
          <Row k="FIRST EPSS" v={host(s.feeds.epss_csv_url)} />
          <Row k="OSV.dev" v={host(s.feeds.osv_api_url)} />
          <SectionTitle>Last runs</SectionTitle>
          <ul className="space-y-1 text-xs">
            {syncs.slice(0, 5).map((r) => (
              <li key={r.id} className="flex items-center gap-2">
                <Badge value={r.status} /> <span className="font-mono w-16">{r.feed}</span>
                <span className="text-faint">{formatDateTime(r.finished_at)}</span>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Egress allow-list</SectionTitle>
          <p className="text-xs text-muted">The API refuses any other host.</p>
          <ul className="font-mono text-xs space-y-0.5">
            {s.outbound_allowlist.map((h) => <li key={h}>{h}</li>)}
            <li className="text-faint">{host(s.llm.url)} (local model)</li>
            {s.notifications.webhook_host && <li className="text-faint">{s.notifications.webhook_host} (alerts, operator-configured)</li>}
          </ul>
          <div className="pt-1 text-xs text-faint">Frist24 API {s.version}</div>
        </Card>
      </div>
    </div>
  );
}

function host(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted">{k}</span>
      <span className="text-right break-all font-mono text-xs">{v}</span>
    </div>
  );
}
