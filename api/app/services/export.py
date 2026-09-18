"""Filing package: zip with JSON + PDF per approved report (EN and DE), incident facts, audit excerpt.

The human submits this on the ENISA single reporting platform; Frist24 does not submit.
PDF via reportlab (pure Python; no system libraries).
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import AuditLog, Incident, Report
from app.schemas.reports import STAGE_MODELS
from app.services.facts import build_facts

TITLES = {
    "early_warning": {"en": "CRA Article 14(1) — Early warning of an actively exploited vulnerability", "de": "CRA Artikel 14 Abs. 1 — Frühwarnung zu einer aktiv ausgenutzten Schwachstelle"},
    "notification": {"en": "CRA Article 14(2) — Vulnerability notification", "de": "CRA Artikel 14 Abs. 2 — Schwachstellenmeldung"},
    "final_report": {"en": "CRA Article 14(2)(c) — Final report", "de": "CRA Artikel 14 Abs. 2 lit. c — Abschlussbericht"},
}
FOOTER = {
    "en": "Prepared with Frist24 (local-first). Schema is the manufacturer's working interpretation of Regulation (EU) 2024/2847 Art. 14; not the official ENISA form. FACT fields were copied from the manufacturer's database; TEXT fields were drafted locally and approved by a human reviewer.",
    "de": "Erstellt mit Frist24 (lokal). Das Schema ist die Arbeitsinterpretation des Herstellers zu Art. 14 Verordnung (EU) 2024/2847 und nicht das amtliche ENISA-Formular. FACT-Felder wurden aus der Herstellerdatenbank übernommen; TEXT-Felder wurden lokal entworfen und durch einen menschlichen Prüfer freigegeben.",
}


def _esc(s: object) -> str:
    t = "" if s is None else str(s)
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")


def report_pdf(rep: Report, inc: Incident, chain_hash: str | None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=f"{rep.stage} {inc.cve_id} {inc.product.sku}")
    ss = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=ss["Title"], fontSize=14, leading=18, spaceAfter=4)
    small = ParagraphStyle("s", parent=ss["Normal"], fontSize=8, leading=10, textColor=colors.grey)
    key = ParagraphStyle("k", parent=ss["Normal"], fontSize=8.5, leading=11, fontName="Helvetica-Bold")
    val = ParagraphStyle("v", parent=ss["Normal"], fontSize=9, leading=12)
    lang = rep.language
    story = [
        Paragraph(_esc(TITLES[rep.stage][lang]), h),
        Paragraph(_esc(f"{inc.product.name} ({inc.product.sku}) · {inc.cve_id} · report {rep.id} v{rep.version} · {rep.status}"), small),
        Paragraph(_esc(f"aware_at {inc.aware_at.isoformat()} · generated {rep.generated_at.isoformat()} · source {rep.source}" + (f" · model {rep.model} · prompt {rep.prompt_version}" if rep.model else "") + (f" · approved by {rep.reviewed_by} at {rep.reviewed_at.isoformat()}" if rep.reviewed_at else "")), small),
        Spacer(1, 6),
    ]
    rows = []
    for k in STAGE_MODELS[rep.stage].model_fields:
        kind = "FACT" if k in rep.fact_fields else "TEXT"
        rows.append([Paragraph(_esc(k), key), Paragraph(_esc(kind), small), Paragraph(_esc(rep.content.get(k)), val)])
    t = Table(rows, colWidths=[48 * mm, 12 * mm, 114 * mm], repeatRows=0)
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    for i, k in enumerate(STAGE_MODELS[rep.stage].model_fields):
        color = colors.Color(0.85, 0.95, 0.88) if k in rep.fact_fields else colors.Color(1.0, 0.95, 0.8)
        t.setStyle(TableStyle([("BACKGROUND", (1, i), (1, i), color)]))
    story += [t, Spacer(1, 8), Paragraph(_esc(FOOTER[lang]), small)]
    if chain_hash:
        story.append(Paragraph(_esc(f"Audit chain head at export: {chain_hash}"), small))
    doc.build(story)
    return buf.getvalue()


def build_package(db: Session, inc: Incident) -> tuple[bytes, str]:
    reports = db.execute(select(Report).where(Report.incident_id == inc.id).order_by(Report.stage, Report.language, Report.version)).scalars().all()
    approved = [r for r in reports if r.status == "approved"]
    timeline = db.execute(
        select(AuditLog)
        .where(or_((AuditLog.entity_type == "incident") & (AuditLog.entity_id == str(inc.id)), AuditLog.payload["incident_id"].as_string() == str(inc.id)))
        .order_by(AuditLog.id)
    ).scalars().all()
    head = timeline[-1].hash if timeline else None
    now = datetime.now(UTC)
    facts = build_facts(db, inc, "en")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        manifest = {
            "generated_at": now.isoformat(),
            "tool": "Frist24 0.1 (local-first CRA Art. 14 assistant)",
            "disclaimer": "Filing-ready package for manual submission on the ENISA single reporting platform. Not an official form.",
            "incident": {
                "id": str(inc.id),
                "product": {"sku": inc.product.sku, "name": inc.product.name},
                "cve_id": inc.cve_id,
                "status": inc.status,
                "aware_at": inc.aware_at.isoformat(),
                "deadline_early_warning": inc.deadline_early_warning.isoformat(),
                "deadline_notification": inc.deadline_notification.isoformat(),
                "deadline_final_report": inc.deadline_final_report.isoformat(),
                "final_report_anchor": inc.final_report_anchor,
            },
            "reports_included": [{"file": f"reports/{r.stage}.{r.language}.v{r.version}.json", "status": r.status, "stage": r.stage, "language": r.language, "version": r.version} for r in (approved or reports)],
            "audit_chain_head": head,
        }
        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        z.writestr("facts.json", json.dumps(facts["facts"], indent=2, ensure_ascii=False, default=str))
        z.writestr("kev_entry.json", json.dumps(facts["context"]["kev"], indent=2, ensure_ascii=False))
        z.writestr("matched_components.json", json.dumps(facts["context"]["components"], indent=2, ensure_ascii=False))
        for r in approved or reports:
            base = f"reports/{r.stage}.{r.language}.v{r.version}"
            z.writestr(base + ".json", json.dumps({"report": r.content, "meta": {"id": str(r.id), "status": r.status, "source": r.source, "model": r.model, "prompt_version": r.prompt_version, "generated_at": r.generated_at.isoformat(), "reviewed_by": r.reviewed_by, "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None, "fact_fields": r.fact_fields}}, indent=2, ensure_ascii=False))
            z.writestr(base + ".pdf", report_pdf(r, inc, head))
        z.writestr(
            "audit_trail.json",
            json.dumps([{"id": e.id, "ts": e.ts.isoformat(), "actor": e.actor, "action": e.action, "entity_type": e.entity_type, "entity_id": e.entity_id, "payload": e.payload, "prev_hash": e.prev_hash, "hash": e.hash} for e in timeline], indent=2, ensure_ascii=False, default=str),
        )
    fname = f"frist24_{inc.product.sku}_{inc.cve_id}_{now.strftime('%Y%m%dT%H%M%SZ')}.zip"
    return buf.getvalue(), fname
