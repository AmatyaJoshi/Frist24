"""Component x vulnerability matching by exact PURL (OSV querybatch).

The fuzzy/LLM-confirmed path (name+version without PURL) is a stub: such components get no match
today and are counted so the UI can show "N components could not be matched by PURL".
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, EpssScore, KevEntry, Match, Vulnerability
from app.services import feeds

log = logging.getLogger("frist24.matching")


def match_by_purl(db: Session, product_ids: list[uuid.UUID] | None = None) -> dict:
    stmt = select(Component)
    if product_ids:
        stmt = stmt.where(Component.product_id.in_(product_ids))
    components = db.execute(stmt).scalars().all()
    with_purl = [c for c in components if c.purl]
    purls = sorted({c.purl for c in with_purl})
    log.info("matching %d components (%d distinct purls, %d without purl)", len(components), len(purls), len(components) - len(with_purl))

    hits = feeds.osv_querybatch(purls)  # purl -> [{id, modified}]
    ids_modified: dict[str, str | None] = {}
    for vulns in hits.values():
        for v in vulns:
            ids_modified[v["id"]] = v.get("modified")
    fresh_records = feeds.fetch_vulns(db, ids_modified)
    vulns_by_id = {v.id: v for v in db.execute(select(Vulnerability).where(Vulnerability.id.in_(list(ids_modified)))).scalars()} if ids_modified else {}

    kev_cves = set(db.execute(select(KevEntry.cve_id)).scalars())
    epss = dict(db.execute(select(EpssScore.cve_id, EpssScore.epss)).all())

    existing = {
        (m.component_id, m.vulnerability_id): m
        for m in db.execute(select(Match).where(Match.component_id.in_([c.id for c in with_purl]))).scalars()
    } if with_purl else {}

    created = 0
    kev_matches = 0
    for comp in with_purl:
        for v in hits.get(comp.purl, []):
            vuln = vulns_by_id.get(v["id"])
            if vuln is None:
                continue
            key = (comp.id, vuln.id)
            in_kev = bool(vuln.cve_id and vuln.cve_id in kev_cves)
            m = existing.get(key)
            if m is None:
                rec = fresh_records.get(vuln.id)
                m = Match(
                    component_id=comp.id,
                    vulnerability_id=vuln.id,
                    cve_id=vuln.cve_id,
                    match_type="purl_exact",
                    confidence=1.0,
                    affected_range=feeds.affected_range_for(rec, comp.purl) if rec else None,
                    status="auto",
                )
                db.add(m)
                existing[key] = m
                created += 1
            m.cve_id = vuln.cve_id
            m.in_kev = in_kev
            m.epss = epss.get(vuln.cve_id) if vuln.cve_id else None
            if in_kev:
                kev_matches += 1
    db.flush()
    summary = {
        "components": len(components),
        "components_without_purl": len(components) - len(with_purl),
        "distinct_purls": len(purls),
        "purls_with_vulns": len(hits),
        "vulns": len(ids_modified),
        "matches_created": created,
        "kev_matches": kev_matches,
    }
    log.info("matching done: %s", summary)
    return summary


def refresh_kev_flags(db: Session) -> int:
    """After KEV/EPSS reloads: flip in_kev and copy EPSS onto existing matches. Returns matches now in KEV."""
    kev_cves = set(db.execute(select(KevEntry.cve_id)).scalars())
    epss = dict(db.execute(select(EpssScore.cve_id, EpssScore.epss)).all())
    n = 0
    for m in db.execute(select(Match).where(Match.cve_id.is_not(None))).scalars():
        m.in_kev = m.cve_id in kev_cves
        m.epss = epss.get(m.cve_id)
        n += int(m.in_kev)
    db.flush()
    return n


def matched_cves(db: Session) -> set[str]:
    return set(db.execute(select(Match.cve_id).where(Match.cve_id.is_not(None)).distinct()).scalars())
