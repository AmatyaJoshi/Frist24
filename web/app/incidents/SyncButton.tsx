"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { runSync } from "@/lib/api";
import { btnPrimary } from "@/components/ui";

export default function SyncButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  async function go() {
    setBusy(true);
    setMsg(null);
    try {
      const r = (await runSync()) as { incidents?: { opened?: number }; kev?: { total?: number; catalog_version?: string }; skipped?: string };
      setMsg(r.skipped ? r.skipped : `KEV ${r.kev?.catalog_version ?? ""} (${r.kev?.total ?? "?"} entries) · ${r.incidents?.opened ?? 0} new incident(s)`);
      router.refresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="flex items-center gap-3">
      {msg && <span className="text-xs text-white/50 max-w-xs truncate" title={msg}>{msg}</span>}
      <button className={btnPrimary} onClick={go} disabled={busy}>
        {busy ? <><Spinner /> Syncing KEV · OSV · EPSS…</> : "Sync now"}
      </button>
    </div>
  );
}

export function Spinner() {
  return <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />;
}
