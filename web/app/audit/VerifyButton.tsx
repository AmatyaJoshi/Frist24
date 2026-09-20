"use client";

import { useState } from "react";
import { verifyAudit } from "@/lib/api";
import { btnPrimary } from "@/components/ui";
import { Spinner } from "../incidents/SyncButton";

export default function VerifyButton() {
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<{ ok: boolean; rows: number; reason: string | null; first_bad_id: number | null; head?: string } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  async function go() {
    setBusy(true);
    setErr(null);
    try {
      setRes(await verifyAudit());
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="flex items-center gap-3">
      {res && (
        <span className={`text-sm ${res.ok ? "text-ok" : "text-danger"}`}>
          {res.ok ? `✓ chain intact over ${res.rows} rows` : `✗ broken at row ${res.first_bad_id}: ${res.reason}`}
          {res.head && <span className="ml-2 font-mono text-[10px] text-faint" title={res.head}>head {res.head.slice(0, 12)}…</span>}
        </span>
      )}
      {err && <span className="text-sm text-danger">{err}</span>}
      <button className={btnPrimary} onClick={go} disabled={busy}>{busy ? <><Spinner /> verifying…</> : "Verify chain"}</button>
    </div>
  );
}
