"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { approveReport, createTemplateDraft, draftWithLlm, editReport, packageUrl, rejectReport } from "@/lib/api";
import { Badge, Card, btnDanger, btnGhost, btnPrimary, btnSuccess } from "@/components/ui";
import { formatDateTime } from "@/lib/time";
import { STAGE_FIELDS, STAGE_LABEL, type IncidentDetail, type Language, type Report, type Stage } from "@/lib/types";
import { Spinner } from "../SyncButton";

const STAGES: Stage[] = ["early_warning", "notification", "final_report"];

export default function ReviewPanel({ incident }: { incident: IncidentDetail }) {
  const router = useRouter();
  const reports = incident.reports;
  const defaultStage: Stage = incident.next_stage ?? "early_warning";
  const [stage, setStage] = useState<Stage>(defaultStage);
  const [lang, setLang] = useState<Language>("en");
  const candidates = useMemo(() => reports.filter((r) => r.stage === stage && r.language === lang).sort((a, b) => b.version - a.version), [reports, stage, lang]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const report = candidates.find((r) => r.id === selectedId) ?? candidates[0] ?? null;
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const dirty = Object.keys(edits).length > 0;

  async function run(label: string, fn: () => Promise<unknown>, okText?: string) {
    setBusy(label);
    setMsg(null);
    try {
      const r = await fn();
      if (okText) setMsg({ ok: true, text: okText });
      setEdits({});
      router.refresh();
      return r;
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(null);
    }
  }

  const draftLlm = () =>
    run("llm", async () => {
      const r = await draftWithLlm(incident.id, stage, lang);
      setSelectedId(r.id);
      setMsg({ ok: true, text: r.source === "llm" ? `Drafted locally by ${r.model} (prompt ${r.prompt_version}). Review the amber fields.` : "Local model unavailable — template draft created instead. Review the amber fields." });
    });
  const draftTemplate = () => run("template", async () => { const r = await createTemplateDraft(incident.id, stage, lang); setSelectedId(r.id); }, "Template draft created (no model involved).");
  const save = () => report && run("save", () => editReport(report.id, edits, "edited in review UI"), "Edits saved to the pending draft. Audit entry written.");
  const approve = () => report && run("approve", () => approveReport(report.id, "approved in review UI"), "Approved. FACT fields re-verified against the database; audit entry written.");
  const reject = () => report && run("reject", () => rejectReport(report.id, "rejected in review UI"), "Rejected. Draft a new version.");

  const fields = STAGE_FIELDS[stage];
  const isFact = (k: string) => report?.fact_fields.includes(k) ?? false;
  const editable = report?.status === "pending_review";

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          {STAGES.map((s) => (
            <button key={s} onClick={() => { setStage(s); setSelectedId(null); setEdits({}); }} className={`${btnGhost} ${stage === s ? "bg-white/10 border-white/30" : ""}`}>{STAGE_LABEL[s]}</button>
          ))}
          <span className="mx-1 text-white/20">|</span>
          {(["en", "de"] as Language[]).map((l) => (
            <button key={l} onClick={() => { setLang(l); setSelectedId(null); setEdits({}); }} className={`${btnGhost} uppercase ${lang === l ? "bg-white/10 border-white/30" : ""}`}>{l}</button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button className={btnPrimary} onClick={draftLlm} disabled={!!busy}>
            {busy === "llm" ? <><Spinner /> drafting locally — no data leaves this machine…</> : `Draft ${lang.toUpperCase()} with local LLM`}
          </button>
          <button className={btnGhost} onClick={draftTemplate} disabled={!!busy}>{busy === "template" ? <Spinner /> : "Template draft (no LLM)"}</button>
          {candidates.length > 1 && (
            <select className="ml-auto rounded border border-white/15 bg-black/30 px-2 py-1 text-xs" value={report?.id ?? ""} onChange={(e) => { setSelectedId(e.target.value); setEdits({}); }}>
              {candidates.map((r) => <option key={r.id} value={r.id}>v{r.version} · {r.status} · {r.source}</option>)}
            </select>
          )}
        </div>
        {msg && <div className={`mt-3 rounded border px-3 py-2 text-sm ${msg.ok ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200" : "border-red-500/30 bg-red-500/10 text-red-200"}`}>{msg.text}</div>}
      </Card>

      {!report && (
        <Card className="p-8 text-center text-sm text-white/50">
          No {STAGE_LABEL[stage]} draft in {lang.toUpperCase()} yet. Draft one with the local model or start from the template.
          <div className="mt-3 text-xs text-white/30">Every draft is <span className="text-amber-300">pending_review</span> until you approve it.</div>
        </Card>
      )}

      {report && (
        <Card className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3 text-xs text-white/50">
            <div className="flex items-center gap-2">
              <Badge value={report.status} />
              <span>v{report.version} · source <span className="text-white/80">{report.source}</span>{report.model && <> · model <span className="font-mono text-white/80">{report.model}</span></>}{report.prompt_version && <> · prompt <span className="font-mono">{report.prompt_version}</span></>}</span>
            </div>
            <span>generated {formatDateTime(report.generated_at)}{report.reviewed_at && <> · reviewed by {report.reviewed_by} {formatDateTime(report.reviewed_at)}</>}</span>
          </div>
          <div className="flex gap-3 text-[11px] mb-3">
            <span className="flex items-center gap-1"><i className="inline-block h-2.5 w-2.5 rounded-sm bg-emerald-400/70" /> FACT — from database, read-only</span>
            <span className="flex items-center gap-1"><i className="inline-block h-2.5 w-2.5 rounded-sm bg-amber-400/70" /> TEXT — written by the model or template, edit freely</span>
          </div>
          <div className="space-y-3">
            {fields.map((k) => {
              const value = report.content[k];
              const fact = isFact(k);
              const current = edits[k] ?? (value == null ? "" : typeof value === "string" ? value : JSON.stringify(value));
              return (
                <div key={k} className={`rounded border-l-4 pl-3 ${fact ? "border-emerald-400/70" : "border-amber-400/70"}`}>
                  <div className="flex justify-between text-[11px] text-white/50"><span className="font-mono">{k}</span><span>{fact ? "FACT" : "TEXT"}</span></div>
                  {fact || !editable ? (
                    <div className={`text-sm whitespace-pre-wrap ${fact ? "text-white/80" : "text-white"}`}>{String(value ?? "—")}</div>
                  ) : (
                    <textarea
                      className={`mt-1 w-full rounded border bg-black/30 px-2 py-1.5 text-sm ${edits[k] !== undefined ? "border-amber-400/60" : "border-white/10"}`}
                      rows={Math.min(8, Math.max(2, Math.ceil(current.length / 90)))}
                      value={current}
                      onChange={(e) => setEdits((d) => ({ ...d, [k]: e.target.value }))}
                    />
                  )}
                </div>
              );
            })}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {editable && (
              <>
                <button className={btnGhost} onClick={save} disabled={!dirty || !!busy}>{busy === "save" ? <Spinner /> : "Save edits"}</button>
                <button className={btnSuccess} onClick={approve} disabled={dirty || !!busy} title={dirty ? "Save edits first" : "Approve this draft"}>{busy === "approve" ? <Spinner /> : "Approve"}</button>
                <button className={btnDanger} onClick={reject} disabled={!!busy}>{busy === "reject" ? <Spinner /> : "Reject"}</button>
              </>
            )}
            {report.status === "approved" && <a className={btnPrimary} href={packageUrl(incident.id)}>Download filing package (JSON + PDF)</a>}
          </div>
        </Card>
      )}
    </div>
  );
}
