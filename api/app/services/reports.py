"""Report lifecycle: create (template or LLM), edit TEXT fields, approve, reject. Every step is audited."""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Incident, Report
from app.schemas.reports import FACT_FIELDS, STAGE_MODELS, text_fields
from app.services import audit
from app.services.facts import build_facts

log = logging.getLogger("frist24.reports")

STAGE_TO_STATUS = {"early_warning": "early_warning_approved", "notification": "notification_approved", "final_report": "final_approved"}

# Honest, regulator-facing placeholder text for the template fallback (no LLM involved).
TEMPLATE_TEXT = {
    "en": {
        "initial_assessment": (
            "The affected component {component} is embedded in {product}. If the vulnerability is reachable in this "
            "product, the impact described in the public advisory may apply. Whether the vulnerable code path is exposed "
            "in this product, and which product versions are affected, is under investigation."
        ),
        "corrective_measures_status": "Investigation started; a fixed upstream version is referenced in the public advisory where available.",
        "vulnerability_description": "{summary} (Source: public vulnerability record for {cve}.) Further analysis for this product is under investigation.",
        "severity_assessment": "Manufacturer assessment for this product is under investigation. Public severity indicators are listed in the FACT fields.",
        "attack_prerequisites": "under investigation",
        "corrective_measures_taken": "Internal investigation opened; affected product builds are being identified.",
        "mitigations_for_users": "1. Restrict network exposure of the product to trusted networks until an update is available.\n2. Monitor for the security update announced through the manufacturer's advisory channel.",
        "security_update_availability": "under investigation",
        "user_notification_plan": "Users will be informed through the manufacturer's security advisory channel once affected versions are confirmed.",
        "affected_user_estimate": "under investigation",
        "cross_border_impact": "Yes; the product is placed on the market in more than one Member State (to be confirmed by reviewer).",
        "root_cause": "under investigation",
        "fix_description": "under investigation",
        "verification_performed": "under investigation",
        "lessons_learned": "under investigation",
        "residual_risk": "under investigation",
    },
    "de": {
        "initial_assessment": (
            "Die betroffene Komponente {component} ist in {product} enthalten. Sofern die Schwachstelle in diesem Produkt "
            "erreichbar ist, kann die im öffentlichen Advisory beschriebene Auswirkung zutreffen. Ob der anfällige Codepfad "
            "in diesem Produkt exponiert ist und welche Produktversionen betroffen sind, wird untersucht."
        ),
        "corrective_measures_status": "Die Untersuchung wurde eingeleitet; eine korrigierte Upstream-Version ist, soweit vorhanden, im öffentlichen Advisory referenziert.",
        "vulnerability_description": "{summary} (Quelle: öffentlicher Schwachstelleneintrag zu {cve}.) Die weitere Analyse für dieses Produkt wird untersucht.",
        "severity_assessment": "Die Herstellerbewertung für dieses Produkt wird untersucht. Öffentliche Schweregrad-Indikatoren sind in den FACT-Feldern aufgeführt.",
        "attack_prerequisites": "wird untersucht",
        "corrective_measures_taken": "Interne Untersuchung eingeleitet; betroffene Produktstände werden identifiziert.",
        "mitigations_for_users": "1. Netzwerkzugriff auf das Produkt bis zur Bereitstellung eines Updates auf vertrauenswürdige Netze beschränken.\n2. Das über den Sicherheitshinweis-Kanal des Herstellers angekündigte Sicherheitsupdate beobachten.",
        "security_update_availability": "wird untersucht",
        "user_notification_plan": "Nutzer werden über den Sicherheitshinweis-Kanal des Herstellers informiert, sobald betroffene Versionen bestätigt sind.",
        "affected_user_estimate": "wird untersucht",
        "cross_border_impact": "Ja; das Produkt wird in mehr als einem Mitgliedstaat in Verkehr gebracht (durch Prüfer zu bestätigen).",
        "root_cause": "wird untersucht",
        "fix_description": "wird untersucht",
        "verification_performed": "wird untersucht",
        "lessons_learned": "wird untersucht",
        "residual_risk": "wird untersucht",
    },
}


def template_content(stage: str, bundle: dict, language: str) -> dict:
    facts, ctx, defaults = bundle["facts"], bundle["context"], bundle["defaults"]
    tmpl = TEMPLATE_TEXT.get(language, TEMPLATE_TEXT["en"])
    comp = ctx["components"][0] if ctx["components"] else {"name": "the component", "version": ""}
    fill = {
        "component": f"{comp['name']} {comp.get('version') or ''}".strip(),
        "product": facts["product_name"],
        "summary": ctx["vulnerability"].get("summary") or ctx["kev"].get("vulnerability_name") or "",
        "cve": facts["vulnerability_id"],
    }
    content = {"report_type": stage}
    for k in FACT_FIELDS[stage]:
        if k in facts:
            content[k] = facts[k]
    for k in text_fields(stage):
        if k == "member_states_affected":
            content[k] = defaults["member_states_affected"]
        elif k in tmpl:
            content[k] = tmpl[k].format(**fill)
        else:
            content[k] = defaults["unknown"]
    if stage == "final_report":
        content["fix_release_identifier"] = defaults["unknown"]
    return content


def validate_content(stage: str, content: dict) -> dict:
    model = STAGE_MODELS[stage]
    try:
        return model.model_validate(content).model_dump()
    except ValidationError as e:
        raise HTTPException(422, f"report content invalid for {stage}: {e.errors()[:5]}") from e


def check_facts_untouched(stage: str, content: dict, facts: dict) -> list[str]:
    """Return FACT keys whose value differs from the deterministic facts (report_type excluded)."""
    bad = []
    for k in FACT_FIELDS[stage]:
        if k == "report_type" or k not in facts:
            continue
        if content.get(k) != facts[k]:
            bad.append(k)
    return bad


def next_version(db: Session, incident_id, stage: str, language: str) -> int:
    v = db.execute(
        select(func.max(Report.version)).where(Report.incident_id == incident_id, Report.stage == stage, Report.language == language)
    ).scalar()
    return (v or 0) + 1


def create_report(
    db: Session, inc: Incident, stage: str, language: str, content: dict, source: str, actor: str, model: str | None = None, prompt_version: str | None = None, extra_audit: dict | None = None
) -> Report:
    if stage not in STAGE_MODELS:
        raise HTTPException(400, f"unknown stage {stage}")
    content = validate_content(stage, content)
    rep = Report(
        incident_id=inc.id,
        stage=stage,
        language=language,
        version=next_version(db, inc.id, stage, language),
        status="pending_review",
        content=content,
        fact_fields=FACT_FIELDS[stage],
        source=source,
        model=model,
        prompt_version=prompt_version,
        generated_at=datetime.now(UTC),
    )
    db.add(rep)
    db.flush()
    audit.append(
        db,
        actor,
        "report.drafted",
        "report",
        rep.id,
        {"incident_id": str(inc.id), "stage": stage, "language": language, "version": rep.version, "source": source, "model": model, "prompt_version": prompt_version, **(extra_audit or {})},
    )
    return rep


def create_template_report(db: Session, inc: Incident, stage: str, language: str, actor: str) -> Report:
    bundle = build_facts(db, inc, language)
    return create_report(db, inc, stage, language, template_content(stage, bundle, language), source="template", actor=actor)


def edit_report(db: Session, rep: Report, changes: dict, actor: str, note: str | None) -> Report:
    if rep.status != "pending_review":
        raise HTTPException(409, f"report is {rep.status}; only pending_review reports can be edited")
    facts = build_facts(db, rep.incident, rep.language)["facts"]
    touched = [k for k in changes if k in FACT_FIELDS[rep.stage] and k in facts and changes[k] != facts[k]]
    if touched:
        raise HTTPException(422, f"FACT fields cannot be edited: {touched}")
    unknown = [k for k in changes if k not in STAGE_MODELS[rep.stage].model_fields]
    if unknown:
        raise HTTPException(422, f"unknown fields for {rep.stage}: {unknown}")
    before = dict(rep.content)
    merged = {**before, **changes}
    rep.content = validate_content(rep.stage, merged)
    rep.source = "human" if rep.source == "human" else f"{rep.source}+human"
    diff = {k: {"before": before.get(k), "after": rep.content.get(k)} for k in changes if before.get(k) != rep.content.get(k)}
    audit.append(db, actor, "report.edited", "report", rep.id, {"incident_id": str(rep.incident_id), "stage": rep.stage, "language": rep.language, "version": rep.version, "changed_fields": diff, "note": note})
    return rep


def approve_report(db: Session, rep: Report, actor: str, note: str | None) -> Report:
    if rep.status != "pending_review":
        raise HTTPException(409, f"report is {rep.status}")
    facts = build_facts(db, rep.incident, rep.language)["facts"]
    bad = check_facts_untouched(rep.stage, rep.content, facts)
    if bad:
        raise HTTPException(422, f"cannot approve: FACT fields differ from database facts: {bad}")
    now = datetime.now(UTC)
    rep.status, rep.reviewed_by, rep.reviewed_at, rep.review_note = "approved", actor, now, note
    inc = rep.incident
    new_status = STAGE_TO_STATUS[rep.stage]
    order = ["open", "early_warning_approved", "notification_approved", "final_approved", "closed"]
    if order.index(new_status) > order.index(inc.status if inc.status in order else "open"):
        inc.status = new_status
    audit.append(
        db,
        actor,
        "report.approved",
        "report",
        rep.id,
        {"incident_id": str(inc.id), "stage": rep.stage, "language": rep.language, "version": rep.version, "note": note, "content_sha256": _sha(rep.content), "incident_status": inc.status},
    )
    return rep


def reject_report(db: Session, rep: Report, actor: str, note: str | None) -> Report:
    if rep.status != "pending_review":
        raise HTTPException(409, f"report is {rep.status}")
    rep.status, rep.reviewed_by, rep.reviewed_at, rep.review_note = "rejected", actor, datetime.now(UTC), note
    audit.append(db, actor, "report.rejected", "report", rep.id, {"incident_id": str(rep.incident_id), "stage": rep.stage, "language": rep.language, "version": rep.version, "note": note})
    return rep


def _sha(content: dict) -> str:
    import hashlib
    import json

    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
