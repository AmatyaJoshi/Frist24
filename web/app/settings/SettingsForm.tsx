"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { updateSettings } from "@/lib/api";
import { Card, SectionTitle, Spinner, btnGhost, btnPrimary, input } from "@/components/ui";
import type { EditableSettings } from "@/lib/types";

export default function SettingsForm({ initial, memberStates }: { initial: EditableSettings; memberStates: Record<string, string> }) {
  const router = useRouter();
  const [form, setForm] = useState<EditableSettings>(initial);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const dirty = JSON.stringify(form) !== JSON.stringify(initial);

  function set<K extends keyof EditableSettings>(k: K, v: EditableSettings[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }
  function toggleState(code: string) {
    set("member_states", form.member_states.includes(code) ? form.member_states.filter((c) => c !== code) : [...form.member_states, code].sort());
  }
  async function save() {
    setBusy(true);
    setMsg(null);
    try {
      await updateSettings(form, form.default_reviewer);
      setMsg({ ok: true, text: "Saved. Change recorded in the audit log; reports use the new values immediately." });
      router.refresh();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-5 space-y-6">
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Field label="Manufacturer Name" hint="Appears as a FACT field in every report and PDF.">
          <input className={input} value={form.manufacturer_name} onChange={(e) => set("manufacturer_name", e.target.value)} />
        </Field>
        <Field label="Security Contact" hint="PSIRT mailbox the CSIRT may contact.">
          <input className={input} value={form.manufacturer_contact} onChange={(e) => set("manufacturer_contact", e.target.value)} />
        </Field>
        <Field label="Default Reviewer" hint="Name recorded as approver unless the request names someone else.">
          <input className={input} value={form.default_reviewer} onChange={(e) => set("default_reviewer", e.target.value)} />
        </Field>
        <Field label="Default Report Language">
          <div className="flex gap-2">
            {(["en", "de"] as const).map((l) => (
              <button key={l} type="button" onClick={() => set("default_language", l)} className={`${btnGhost} uppercase ${form.default_language === l ? "bg-surface-3 border-border-strong" : ""}`}>{l}</button>
            ))}
          </div>
        </Field>
        <Field label="Alert Webhook URL" hint="Slack, Teams, PagerDuty or ticketing endpoint. One JSON summary per sync when incidents open. Leave empty to disable.">
          <input className={input} placeholder="https://hooks.example.com/…" value={form.notify_webhook_url ?? ""} onChange={(e) => set("notify_webhook_url", e.target.value || null)} />
        </Field>
        <Field label="Public URL of This UI" hint="Used for links inside alerts.">
          <input className={input} value={form.public_web_url} onChange={(e) => set("public_web_url", e.target.value)} />
        </Field>
      </div>

      <div>
        <SectionTitle hint={`${form.member_states.length} selected · fills member_states_affected in reports`}>Member States Where Products Are Placed on the Market</SectionTitle>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {Object.entries(memberStates).map(([code, name]) => {
            const on = form.member_states.includes(code);
            return (
              <button
                key={code}
                type="button"
                onClick={() => toggleState(code)}
                title={name}
                className={`rounded-md border px-2 py-1 text-xs transition-colors ${on ? "border-accent bg-accent-soft text-accent font-medium" : "border-border bg-surface text-muted hover:text-fg"}`}
              >
                {code}
              </button>
            );
          })}
          <button type="button" onClick={() => set("member_states", Object.keys(memberStates).sort())} className={`${btnGhost} text-xs py-1`}>All 27</button>
          <button type="button" onClick={() => set("member_states", [])} className={`${btnGhost} text-xs py-1`}>None</button>
        </div>
      </div>

      {msg && <div className={`rounded-md border px-3 py-2 text-sm ${msg.ok ? "border-ok bg-ok-soft text-ok" : "border-danger bg-danger-soft text-danger"}`}>{msg.text}</div>}
      <div className="flex items-center gap-2">
        <button className={btnPrimary} onClick={save} disabled={!dirty || busy}>{busy ? <><Spinner /> Saving…</> : "Save Settings"}</button>
        <button className={btnGhost} onClick={() => setForm(initial)} disabled={!dirty || busy}>Reset</button>
        {dirty && <span className="text-xs text-warn">Unsaved changes</span>}
      </div>
    </Card>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="font-medium">{label}</span>
      <div className="mt-1">{children}</div>
      {hint && <span className="mt-1 block text-xs text-faint">{hint}</span>}
    </label>
  );
}
