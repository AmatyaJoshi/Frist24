from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import AuditLog, Component, EpssScore, Incident, KevEntry, Match, Product, Report, Vulnerability
from app.routers.products import actor_from_header
from app.schemas.incidents import FixAvailable, IncidentDetail, IncidentListItem, MatchedComponent, TimelineEvent
from app.schemas.reports import ReportOut
from app.services import audit, export, reports
from app.services.facts import build_facts

router = APIRouter(prefix="/incidents", tags=["incidents"])


def report_out(r: Report) -> ReportOut:
    return ReportOut(
        id=str(r.id),
        incident_id=str(r.incident_id),
        stage=r.stage,
        language=r.language,
        version=r.version,
        status=r.status,
        content=r.content,
        fact_fields=r.fact_fields,
        source=r.source,
        model=r.model,
        prompt_version=r.prompt_version,
        generated_at=r.generated_at.isoformat(),
        reviewed_by=r.reviewed_by,
        reviewed_at=r.reviewed_at.isoformat() if r.reviewed_at else None,
        review_note=r.review_note,
    )


def _next(inc: Incident) -> tuple[datetime | None, str | None]:
    if inc.status == "open":
        return inc.deadline_early_warning, "early_warning"
    if inc.status == "early_warning_approved":
        return inc.deadline_notification, "notification"
    if inc.status == "notification_approved":
        return inc.deadline_final_report, "final_report"
    return None, None


def _list_items(db: Session, incs: list[Incident]) -> list[IncidentListItem]:
    if not incs:
        return []
    ids = [i.id for i in incs]
    cves = {i.cve_id for i in incs}
    epss = dict(db.execute(select(EpssScore.cve_id, EpssScore.epss).where(EpssScore.cve_id.in_(cves))).all())
    cvss = dict(
        db.execute(select(Vulnerability.cve_id, func.max(Vulnerability.cvss_score)).where(Vulnerability.cve_id.in_(cves)).group_by(Vulnerability.cve_id)).all()
    )
    comp_counts = {
        (p, c): n
        for p, c, n in db.execute(
            select(Component.product_id, Match.cve_id, func.count(func.distinct(Component.id)))
            .join(Match, Match.component_id == Component.id)
            .where(Match.cve_id.in_(cves), Match.status != "rejected")
            .group_by(Component.product_id, Match.cve_id)
        ).all()
    }
    rep_counts: dict[tuple, int] = {
        (iid, st): n
        for iid, st, n in db.execute(select(Report.incident_id, Report.status, func.count()).where(Report.incident_id.in_(ids)).group_by(Report.incident_id, Report.status)).all()
    }
    out = []
    for i in incs:
        nd, ns = _next(i)
        out.append(
            IncidentListItem(
                id=i.id,
                product_id=i.product_id,
                sku=i.product.sku,
                product_name=i.product.name,
                cve_id=i.cve_id,
                vulnerability_name=i.kev.vulnerability_name,
                kev_date_added=i.kev.date_added,
                known_ransomware_campaign_use=i.kev.known_ransomware_campaign_use,
                epss=epss.get(i.cve_id),
                cvss_score=cvss.get(i.cve_id),
                status=i.status,
                aware_at=i.aware_at,
                deadline_early_warning=i.deadline_early_warning,
                deadline_notification=i.deadline_notification,
                deadline_final_report=i.deadline_final_report,
                final_report_anchor=i.final_report_anchor,
                next_deadline=nd,
                next_stage=ns,
                component_count=comp_counts.get((i.product_id, i.cve_id), 0),
                reports_pending=rep_counts.get((i.id, "pending_review"), 0),
                reports_approved=rep_counts.get((i.id, "approved"), 0),
            )
        )
    # deadline-sorted: soonest next deadline first; closed/complete last
    out.sort(key=lambda x: (x.next_deadline is None, x.next_deadline or datetime.max.replace(tzinfo=UTC), -(x.epss or 0)))
    return out


@router.get("", response_model=list[IncidentListItem])
def list_incidents(status: str | None = Query(default=None), db: Session = Depends(get_db)):
    stmt = select(Incident).options(selectinload(Incident.product), selectinload(Incident.kev))
    if status:
        stmt = stmt.where(Incident.status == status)
    return _list_items(db, db.execute(stmt).scalars().all())


def _get(db: Session, incident_id: uuid.UUID) -> Incident:
    inc = db.execute(
        select(Incident).options(selectinload(Incident.product), selectinload(Incident.kev), selectinload(Incident.reports)).where(Incident.id == incident_id)
    ).scalar_one_or_none()
    if not inc:
        raise HTTPException(404, "incident not found")
    return inc


def _timeline(db: Session, inc: Incident) -> list[TimelineEvent]:
    rows = db.execute(
        select(AuditLog)
        .where(
            or_(
                (AuditLog.entity_type == "incident") & (AuditLog.entity_id == str(inc.id)),
                AuditLog.payload["incident_id"].as_string() == str(inc.id),
            )
        )
        .order_by(AuditLog.id.asc())
    ).scalars().all()
    return [TimelineEvent(id=r.id, ts=r.ts, actor=r.actor, action=r.action, entity_type=r.entity_type, entity_id=r.entity_id, payload=r.payload, hash=r.hash, prev_hash=r.prev_hash) for r in rows]


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    inc = _get(db, incident_id)
    base = _list_items(db, [inc])[0]
    pairs = db.execute(
        select(Match, Component)
        .join(Component, Match.component_id == Component.id)
        .where(Component.product_id == inc.product_id, Match.cve_id == inc.cve_id)
        .order_by(Component.name, Component.version)
    ).all()
    comps = [
        MatchedComponent(
            match_id=m.id, component_id=c.id, name=c.name, version=c.version, purl=c.purl, ecosystem=c.ecosystem,
            match_type=m.match_type, confidence=m.confidence, affected_range=m.affected_range, status=m.status, osv_id=m.vulnerability_id,
        )
        for m, c in pairs
    ]
    vulns = db.execute(select(Vulnerability).where(Vulnerability.cve_id == inc.cve_id).order_by(Vulnerability.id)).scalars().all()
    reps = sorted(inc.reports, key=lambda r: (r.stage, r.language, r.version))
    return IncidentDetail(
        **base.model_dump(),
        product_description=inc.product.description,
        lifecycle_status=inc.product.lifecycle_status,
        kev=inc.kev,
        vulnerabilities=vulns,
        components=comps,
        reports=[report_out(r) for r in reps],
        timeline=_timeline(db, inc),
        facts=build_facts(db, inc, "en")["facts"],
    )


@router.post("/{incident_id}/reports/template", response_model=ReportOut, status_code=201, summary="Create a template (non-LLM) draft")
def create_template(
    incident_id: uuid.UUID,
    stage: str = Query(pattern="^(early_warning|notification|final_report)$"),
    language: str = Query(default="en", pattern="^(en|de)$"),
    db: Session = Depends(get_db),
    actor: str = Depends(actor_from_header),
):
    inc = _get(db, incident_id)
    rep = reports.create_template_report(db, inc, stage, language, actor)
    db.commit()
    db.refresh(rep)
    return report_out(rep)


@router.post("/{incident_id}/fix-available", response_model=IncidentListItem, summary="Record fix availability; re-anchors the 14-day final-report clock")
def fix_available(incident_id: uuid.UUID, body: FixAvailable, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)):
    inc = _get(db, incident_id)
    when = body.fix_available_at or datetime.now(UTC)
    inc.fix_available_at = when
    inc.deadline_final_report = when + timedelta(days=14)
    inc.final_report_anchor = "fix_available"
    audit.append(db, actor, "incident.fix_available", "incident", inc.id, {"fix_available_at": when.isoformat(), "deadline_final_report": inc.deadline_final_report.isoformat()})
    db.commit()
    return _list_items(db, [inc])[0]


@router.post("/{incident_id}/close", response_model=IncidentListItem)
def close_incident(incident_id: uuid.UUID, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)):
    inc = _get(db, incident_id)
    if inc.status == "closed":
        raise HTTPException(409, "already closed")
    inc.status, inc.closed_at = "closed", datetime.now(UTC)
    audit.append(db, actor, "incident.closed", "incident", inc.id, {})
    db.commit()
    return _list_items(db, [inc])[0]


@router.get("/{incident_id}/package", summary="Filing package (zip: manifest, facts, reports JSON+PDF, audit trail)")
def download_package(incident_id: uuid.UUID, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)):
    inc = _get(db, incident_id)
    data, fname = export.build_package(db, inc)
    audit.append(db, actor, "package.exported", "incident", inc.id, {"filename": fname, "bytes": len(data)})
    db.commit()
    return Response(content=data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{fname}"'})
