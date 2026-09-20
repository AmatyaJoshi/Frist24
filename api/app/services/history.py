"""Demo history: product families on REAL public SBOMs and a staged multi-year workflow history.

Real: every SBOM, component, PURL, OSV match, CVE and KEV entry. Incidents are opened by the same
deterministic rule as always (run_full_sync). Staged: aware_at, report approvals/rejections and
status transitions for the resulting incidents, chosen deterministically per (sku, cve) so the
portfolio shows closed, final-approved, in-progress and needs-action incidents. Every staged audit
row carries payload synthetic_history=true; staged actors are demo reviewer personas.
Two incidents stay untouched and live for the countdown demo. Disable with DEMO_HISTORY=false.
"""
from __future__ import annotations

import hashlib
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
LIVE = {("HMI-4100", "CVE-2020-11023"), ("EGW-7200", "CVE-2025-24813")}

# Product families sharing a platform SBOM (real, from CycloneDX/bom-examples). Variants are generated so
# the catalogue looks like a Mittelstand manufacturer's (~85 SKUs); every incident is still opened by the real rule.
def _variants(prefix: str, base_names: list[str], suffixes: list[str], start_year: int, count: int) -> list[tuple]:
    out: list[tuple] = []
    i = 0
    for n, base in enumerate(base_names):
        for k, suf in enumerate(suffixes):
            if i >= count:
                return out
            sku = f"{prefix}-{(n + 1) * 100 + k * 10 + 10}"
            placed = date(start_year + (i * 7) // count, 1 + (i * 5) % 12, 1 + (i * 11) % 27)
            lifecycle = "discontinued" if (n == 0 and k < 2) or (i % 9 == 4) else "active"
            out.append((sku, f"{sku} {base} {suf}".strip(), placed, lifecycle))
            i += 1
    return out


FAMILIES: list[dict] = [
    {
        "fixture": "edge-gateway.cdx.json",
        "desc": "Industrial edge gateway platform (Java runtime, embedded identity service) bridging fieldbus data to the plant network.",
        "skus": _variants("EGW", ["Edge Gateway", "Remote Terminal Unit", "MES Link Controller", "Cell Controller", "Line Gateway"],
                          ["2-port", "4-port", "PoE", "5G", "Rugged", "Redundant", "Compact", "Rack"], 2019, 40),
    },
    {
        "fixture": "hmi-web-ui.cdx.json",
        "desc": "Operator panel with embedded web UI served to service laptops and plant browsers.",
        "skus": _variants("HMI", ["Operator Panel", "Multi-touch Panel", "Compact Panel"],
                          ["7in", "10in", "12in", "15in", "IP66", "Wide", "Mobile", "Marine"], 2019, 24),
    },
    {
        "fixture": "scada-connector.cdx.json",
        "desc": "Java service (Dropwizard) bridging SCADA historians to the MES over HTTP/2; installed on customer servers.",
        "skus": _variants("SCC", ["SCADA Connector", "OPC UA Bridge"], ["Standard", "HA", "Cloud Edge", "Historian", "Lite"], 2019, 9),
    },
    {
        "fixture": "fleet-agent.cdx.json",
        "desc": "Go agent on field devices for telemetry and remote firmware update.",
        "skus": _variants("FLA", ["Fleet Agent"], ["Standard", "LTE", "Secure Element", "Satellite", "Rail", "Marine", "Mining", "Utility", "Pharma"], 2020, 9),
    },
    {
        "fixture": "web-portal.cdx.json",
        "desc": "Node.js portal for device fleet management, deployed on-premises at customers.",
        "skus": _variants("WP", ["Customer Web Portal"], ["Standard", "Enterprise", "MSP"], 2019, 3),
    },
]
PRODUCT_DATES = {"EGW-7200": date(2021, 5, 10)}  # gateway must predate its 2022 incidents

REVIEWERS = ["m.brandt (PSIRT lead)", "s.keller (product security)", "j.novak (compliance)", "a.fischer (firmware)"]
REJECT_NOTES = ["affected product versions not yet confirmed; redraft", "mitigation wording too vague for customers", "German register: use formal 'Sie' consistently"]

# Target distribution across the portfolio (per 20): 10 closed, 3 final approved, 3 notification approved,
# 2 early-warning approved (notification pending), 2 open (draft pending or nothing yet).
MIX = ["closed", "closed", "closed", "closed", "closed", "closed", "closed", "closed_rejected_v1", "closed", "closed_rejected_v1",
       "final_approved", "final_approved", "final_approved", "notification_approved", "notification_approved", "notification_approved",
       "early_warning_pending_notification", "early_warning_pending_notification", "open_pending_draft", "open_no_draft"]
HISTORY_START = date(2024, 1, 1)


def _h(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


def seed_history_products() -> int:
    from app.services.demo import fixtures_dir
    from app.services.ingest import ingest_sbom

    n = 0
    with session_factory()() as db:
        for fam in FAMILIES:
            raw = (fixtures_dir() / "sboms" / fam["fixture"]).read_bytes()
            for sku, name, placed, lifecycle in fam["skus"]:
                p = db.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()
                if p is None:
                    p = Product(sku=sku, name=name, description=fam["desc"], lifecycle_status=lifecycle, placed_on_market_at=placed)
                    db.add(p)
                    db.flush()
                    audit.append(db, ACTOR, "product.created", "product", p.id, {"sku": sku, "name": name, "synthetic_history": True})
                    n += 1
                ingest_sbom(db, p, raw, fam["fixture"], ACTOR)
        for sku, d in PRODUCT_DATES.items():
            p = db.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()
            if p:
                p.placed_on_market_at = d
        db.commit()
    log.info("history: %d products created", n)
    return n


def _report(db, inc: Incident, stage: str, lang: str, version: int, status: str, when: datetime, reviewer: str, note: str | None) -> Report:
    bundle = build_facts(db, inc, lang)
    rep = Report(
        incident_id=inc.id, stage=stage, language=lang, version=version, status=status, content=template_content(stage, bundle, lang),
        fact_fields=FACT_FIELDS[stage], source="template", model=None, prompt_version="history",
        generated_at=when - timedelta(minutes=25 + (version * 7)), reviewed_by=reviewer if status != "pending_review" else None,
        reviewed_at=when if status != "pending_review" else None, review_note=note,
    )
    db.add(rep)
    db.flush()
    common = {"incident_id": str(inc.id), "stage": stage, "language": lang, "version": version, "synthetic_history": True}
    audit.append(db, ACTOR, "report.drafted", "report", rep.id, {**common, "source": "template"}, ts=rep.generated_at)
    if status == "approved":
        audit.append(db, reviewer, "report.approved", "report", rep.id, {**common, "note": note}, ts=when)
    elif status == "rejected":
        audit.append(db, reviewer, "report.rejected", "report", rep.id, {**common, "note": note}, ts=when)
    return rep


def _approve_stage(db, inc: Incident, stage: str, when: datetime, reviewer: str, reject_first: bool = False) -> None:
    for lang in ("en", "de"):
        v = 1
        if reject_first:
            _report(db, inc, stage, lang, 1, "rejected", when - timedelta(hours=3), reviewer, REJECT_NOTES[_h(inc.cve_id, stage, lang) % len(REJECT_NOTES)])
            v = 2
        _report(db, inc, stage, lang, v, "approved", when, reviewer, "approved")


def stage_history(now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    staged = 0
    with session_factory()() as db:
        incs = db.execute(select(Incident).join(Product).order_by(Product.sku, Incident.cve_id)).scalars().all()
        for inc in incs:
            sku = inc.product.sku
            key = (sku, inc.cve_id)
            if key in LIVE or inc.status != "open" or inc.reports:
                continue
            kev = db.get(KevEntry, inc.cve_id)
            h = _h(sku, inc.cve_id)
            scenario = MIX[h % len(MIX)]
            reviewer = REVIEWERS[(h // 10) % len(REVIEWERS)]
            reject_first = scenario.endswith("_rejected_v1")
            fix_days = 7 + (h // 100) % 38

            if scenario in ("early_warning_pending_notification", "notification_approved", "open_pending_draft", "open_no_draft"):
                # in-progress: became aware recently (the rule fired on a recent sync)
                hours_ago = {"open_no_draft": 1 + h % 12, "open_pending_draft": 2 + h % 18, "early_warning_pending_notification": 8 + h % 40, "notification_approved": 56 + h % 30}[scenario]
                aware = now - timedelta(hours=hours_ago, minutes=h % 60)
                origin = "recent sync"
            else:
                # historical: spread between max(2024-01-01, KEV listing, product placement) and 45 days ago
                lo = max(HISTORY_START, kev.date_added + timedelta(days=1), inc.product.placed_on_market_at or HISTORY_START)
                hi = now.date() - timedelta(days=45)
                span = max(1, (hi - lo).days)
                aware = datetime.combine(lo + timedelta(days=h % span), datetime.min.time(), tzinfo=UTC) + timedelta(hours=6 + h % 11, minutes=h % 60)
                origin = "onboarding/sync between 2024 and 2026"
            inc.aware_at = aware
            for k, v in deadlines(aware).items():
                setattr(inc, k, v)
            db.flush()
            audit.append(db, ACTOR, "incident.opened", "incident", inc.id, {"rule": "cve_in_kev", "sku": sku, "cve_id": inc.cve_id, "aware_at": aware.isoformat(), "synthetic_history": True, "note": f"aware_at staged from {origin}"}, ts=aware)

            if scenario == "open_no_draft":
                pass
            elif scenario == "open_pending_draft":
                _report(db, inc, "early_warning", "en", 1, "pending_review", aware + timedelta(hours=1), reviewer, None)
            else:
                _approve_stage(db, inc, "early_warning", aware + timedelta(hours=4 + h % 14), reviewer, reject_first)
                inc.status = "early_warning_approved"
                if scenario == "early_warning_pending_notification":
                    if now - aware > timedelta(hours=7):
                        _report(db, inc, "notification", "en", 1, "pending_review", aware + timedelta(hours=6), reviewer, None)
                else:
                    _approve_stage(db, inc, "notification", aware + timedelta(hours=40 + h % 28), reviewer)
                    inc.status = "notification_approved"
                    if scenario in ("closed", "closed_rejected_v1", "final_approved"):
                        fix_at = aware + timedelta(days=fix_days)
                        inc.fix_available_at = fix_at
                        inc.deadline_final_report = fix_at + timedelta(days=14)
                        inc.final_report_anchor = "fix_available"
                        audit.append(db, reviewer, "incident.fix_available", "incident", inc.id, {"fix_available_at": fix_at.isoformat(), "synthetic_history": True}, ts=fix_at)
                        _approve_stage(db, inc, "final_report", fix_at + timedelta(days=2 + h % 9, hours=3), reviewer)
                        inc.status = "final_approved"
                        if scenario.startswith("closed"):
                            inc.status = "closed"
                            inc.closed_at = fix_at + timedelta(days=3 + h % 10)
                            audit.append(db, reviewer, "incident.closed", "incident", inc.id, {"synthetic_history": True}, ts=inc.closed_at)
            db.commit()
            staged += 1
            log.info("history: %s x %s -> %s (%s, aware %s)", sku, inc.cve_id, inc.status, scenario, aware.date())
    return staged
