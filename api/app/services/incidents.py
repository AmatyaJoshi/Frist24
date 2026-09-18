"""The deterministic rule that opens incidents.

    for every match with in_kev = true and status != rejected:
        ensure exactly one Incident(product, cve) exists; aware_at = now (first time seen)

Nothing else opens an incident. The LLM is never consulted here.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, Incident, Match, Product
from app.services import audit

log = logging.getLogger("frist24.incidents")

EARLY_WARNING = timedelta(hours=24)
NOTIFICATION = timedelta(hours=72)
FINAL_REPORT = timedelta(days=14)  # provisional anchor: aware_at (re-anchored on fix availability)


def deadlines(aware_at: datetime) -> dict:
    return {
        "deadline_early_warning": aware_at + EARLY_WARNING,
        "deadline_notification": aware_at + NOTIFICATION,
        "deadline_final_report": aware_at + FINAL_REPORT,
    }


def open_incidents(db: Session, actor: str) -> list[Incident]:
    rows = db.execute(
        select(Match, Component)
        .join(Component, Match.component_id == Component.id)
        .where(Match.in_kev.is_(True), Match.status != "rejected", Match.cve_id.is_not(None))
    ).all()
    by_key: dict[tuple, list[tuple[Match, Component]]] = {}
    for m, c in rows:
        by_key.setdefault((c.product_id, m.cve_id), []).append((m, c))

    existing = {(i.product_id, i.cve_id) for i in db.execute(select(Incident)).scalars()}
    opened: list[Incident] = []
    now = datetime.now(UTC)
    for (product_id, cve), pairs in sorted(by_key.items(), key=lambda kv: kv[0][1]):
        if (product_id, cve) in existing:
            continue
        product = db.get(Product, product_id)
        inc = Incident(product_id=product_id, cve_id=cve, status="open", aware_at=now, final_report_anchor="provisional", **deadlines(now))
        db.add(inc)
        db.flush()
        comps = sorted({(c.purl or f"{c.name}@{c.version}") for _, c in pairs})
        audit.append(
            db,
            actor,
            "incident.opened",
            "incident",
            inc.id,
            {
                "rule": "cve_in_kev",
                "product_id": str(product_id),
                "sku": product.sku if product else None,
                "cve_id": cve,
                "aware_at": now.isoformat(),
                "deadline_early_warning": inc.deadline_early_warning.isoformat(),
                "deadline_notification": inc.deadline_notification.isoformat(),
                "deadline_final_report": inc.deadline_final_report.isoformat(),
                "final_report_anchor": "provisional",
                "matched_components": comps[:50],
                "match_ids": [str(m.id) for m, _ in pairs][:50],
            },
        )
        opened.append(inc)
        log.info("incident opened: %s x %s (%d components)", product.sku if product else product_id, cve, len(pairs))
    return opened


def incident_components(db: Session, inc: Incident) -> list[tuple[Match, Component]]:
    return db.execute(
        select(Match, Component)
        .join(Component, Match.component_id == Component.id)
        .where(Component.product_id == inc.product_id, Match.cve_id == inc.cve_id, Match.status != "rejected")
        .order_by(Component.name)
    ).all()
