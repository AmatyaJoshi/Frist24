import { getIncidents, getSyncStatus } from "@/lib/api";
import { formatDateTime } from "@/lib/time";
import { Badge, Empty, ErrorBox, PageHeader } from "@/components/ui";
import SyncButton from "./SyncButton";
import IncidentTable from "./IncidentTable";
import type { FeedSync, IncidentListItem } from "@/lib/types";

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

  return (
    <div>
      <PageHeader
        title="Incidents"
        subtitle={
          <>
            One incident is one product and one CVE listed in CISA KEV. Opened by rule, never by the model. Clocks start at <span className="font-mono">aware_at</span>.
            {lastKev && (
              <span className="ml-2 text-faint">
                Last KEV sync {formatDateTime(lastKev.finished_at)} <Badge value={lastKev.status} className="ml-1" />
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
      {incidents.length > 0 && <IncidentTable rows={incidents} />}
    </div>
  );
}
