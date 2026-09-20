"""Demo history: extra products with REAL public SBOMs and a staged multi-year workflow history.

What is real: every SBOM, component, PURL, OSV match, CVE and KEV entry. Incidents are opened by the
same deterministic rule as always (run_full_sync). What is staged: for a fixed list of (sku, cve)
pairs the incident's aware_at is set to the day after the CVE entered KEV, template reports are
created and approved by demo reviewer personas at plausible times, and the incident is advanced or
closed. Every staged audit row carries actor "demo:history" and payload synthetic_history=true, so the
audit trail itself tells the truth. Disable with DEMO_HISTORY=false or `demo --no-history`.
"""
from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from app.db import session_factory
from app.models import Incident, KevEntry, Product, Report
from app.schemas.reports import FACT_FIELDS
from app.services import audit
from app.services.facts import build_facts
from app.services.incidents import deadlines
from app.services.reports import template_content

log = logging.getLogger("frist24.history")
ACTOR = "demo:history"

HISTORY_PRODUCTS = [
    {
        "sku": "SCC-3300",
        "name": "SCC-3300 SCADA Connector",
        "description": "Java service (Dropwizard) bridging SCADA historians to the MES over HTTP/2. Installed on customer servers.",
        "lifecycle_status": "active",
        "placed_on_market_at": date(2020, 6, 1),
        "fixture": "scada-connector.cdx.json",
    },
    {
        "sku": "FLA-210",
        "name": "FLA-210 Fleet Agent",
        "description": "Go agent on field devices for telemetry and remote firmware update.",
        "lifecycle_status": "active",
        "placed_on_market_at": date(2021, 11, 15),
        "fixture": "fleet-agent.cdx.json",
    },
    {
        "sku": "WP-500",
        "name": "WP-500 Customer Web Portal",
        "description": "Node.js portal for device fleet management, deployed on-premises at customers. Sold 2019–2024.",
        "lifecycle_status": "discontinued",
        "placed_on_market_at": date(2019, 9, 1),
        "fixture": "web-portal.cdx.json",
    },
]

# Backdate placement of the gateway so the 2022 incidents fall inside its market life.
PRODUCT_DATES = {"EGW-7200": date(2021, 5, 10)}

REVIEWERS = ["m.brandt (PSIRT lead)", "s.keller (product security)", "j.novak (compliance)"]

# (sku, cve) -> scenario. aware_offset_days: days after KEV dateAdded. final: closed | final_approved | notification_approved
SCENARIOS: dict[tuple[str, str], dict] = {
    ("EGW-7200", "CVE-2020-1938"): {"aware_offset_days": 1, "final": "closed", "fix_days": 16, "reviewer": 0},
    ("EGW-7200", "CVE-2022-22965"): {"aware_offset_days": 1, "final": "closed", "fix_days": 14, "reviewer": 1},
    ("EGW-7200", "CVE-2023-44487"): {"aware_offset_days": 1, "final": "final_approved", "fix_days": 21, "reviewer": 0},
    ("SCC-3300", "CVE-2023-44487"): {"aware_offset_days": 1, "final": "closed", "fix_days": 22, "reviewer": 2},
    ("FLA-210", "CVE-2023-44487"): {"aware_offset_days": 2, "final": "closed", "fix_days": 9, "reviewer": 1},
}
# Live for the demo (left untouched): HMI-4100 x CVE-2020-11023, EGW-7200 x CVE-2025-24813.


def seed_history_products() -> int:
    from app.services.demo import fixtures_dir
    from app.services.ingest import ingest_sbom

    n = 0
    with session_factory()() as db:
        for spec in HISTORY_PRODUCTS:
            p = db.execute(select(Product).where(Product.sku == spec["sku"])).scalar_one_or_none()
            if p is None:
                p = Product(**{k: v for k, v in spec.items() if k != "fixture"})
                db.add(p)
                db.flush()
                audit.append(db, ACTOR, "product.created", "product", p.id, {"sku": p.sku, "name": p.name, "synthetic_history": True})
                n += 1
            path = fixtures_dir() / "sboms" / spec["fixture"]
            ingest_sbom(db, p, path.read_bytes(), spec["fixture"], ACTOR)
        for sku, d in PRODUCT_DATES.items():
            p = db.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()
            if p:
                p.placed_on_market_at = d
        db.commit()
    return n


def _approve_stage(db, inc: Incident, stage: str, when: datetime, reviewer: str) -> None:
    for lang in ("en", "de"):
        bundle = build_facts(db, inc, lang)
        content = template_content(stage, bundle, lang)
        rep = Report(
            incident_id=inc.id,
            stage=stage,
            language=lang,
            version=1,
            status="approved",
            content=content,
            fact_fields=FACT_FIELDS[stage],
            source="template",
            model=None,
            prompt_version="history",
            generated_at=when - timedelta(minutes=35),
            reviewed_by=reviewer,
            reviewed_at=when,
            review_note="approved (demo history)",
        )
        db.add(rep)
        db.flush()
        common = {"incident_id": str(inc.id), "stage": stage, "language": lang, "version": 1, "synthetic_history": True}
        audit.append(db, ACTOR, "report.drafted", "report", rep.id, {**common, "source": "template"}, ts=rep.generated_at)
        audit.append(db, reviewer, "report.approved", "report", rep.id, {**common, "note": rep.review_note}, ts=when)


def stage_history() -> int:
    staged = 0
    with session_factory()() as db:
        for (sku, cve), sc in SCENARIOS.items():
            inc = db.execute(select(Incident).join(Product).where(Product.sku == sku, Incident.cve_id == cve)).scalar_one_or_none()
            if inc is None:
                log.info("history: incident %s x %s not present (rule did not open it); skipping", sku, cve)
                continue
            if inc.status != "open" or inc.reports:
                continue
            kev = db.get(KevEntry, cve)
            aware = datetime.combine(kev.date_added, datetime.min.time(), tzinfo=UTC) + timedelta(days=sc["aware_offset_days"], hours=7, minutes=42)
            inc.aware_at = aware
            for k, v in deadlines(aware).items():
                setattr(inc, k, v)
            db.flush()
            reviewer = REVIEWERS[sc["reviewer"]]
            audit.append(db, ACTOR, "incident.opened", "incident", inc.id, {"rule": "cve_in_kev", "sku": sku, "cve_id": cve, "aware_at": aware.isoformat(), "synthetic_history": True, "note": "aware_at restaged to KEV listing date for demo history"}, ts=aware)

            _approve_stage(db, inc, "early_warning", aware + timedelta(hours=6, minutes=10), reviewer)
            inc.status = "early_warning_approved"
            _approve_stage(db, inc, "notification", aware + timedelta(hours=51, minutes=20), reviewer)
            inc.status = "notification_approved"
            fix_at = aware + timedelta(days=sc["fix_days"])
            inc.fix_available_at = fix_at
            inc.deadline_final_report = fix_at + timedelta(days=14)
            inc.final_report_anchor = "fix_available"
            audit.append(db, reviewer, "incident.fix_available", "incident", inc.id, {"fix_available_at": fix_at.isoformat(), "synthetic_history": True}, ts=fix_at)
            if sc["final"] in ("final_approved", "closed"):
                _approve_stage(db, inc, "final_report", fix_at + timedelta(days=5, hours=3), reviewer)
                inc.status = "final_approved"
            if sc["final"] == "closed":
                inc.status = "closed"
                inc.closed_at = fix_at + timedelta(days=6)
                audit.append(db, reviewer, "incident.closed", "incident", inc.id, {"synthetic_history": True}, ts=inc.closed_at)
            db.commit()
            staged += 1
            log.info("history: %s x %s -> %s (aware %s)", sku, cve, inc.status, aware.date())
    return staged
