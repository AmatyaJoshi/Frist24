"""Deterministic FACT fields + context for one incident. This is the only source of truth the
LLM sees; it must copy FACT fields verbatim and may only write TEXT fields."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings  # noqa: F401
from app.services import app_settings
from app.models import EpssScore, Incident, Product, Report, Vulnerability
from app.schemas.reports import UNKNOWN
from app.services.incidents import incident_components

DEFAULT_MEMBER_STATES = {
    "en": "EU-wide; product is placed on the market in the following Member States: [to be confirmed by reviewer]",
    "de": "EU-weit; das Produkt wird in folgenden Mitgliedstaaten in Verkehr gebracht: [durch Prüfer zu bestätigen]",
}


def _best_vuln(db: Session, cve: str) -> Vulnerability | None:
    vulns = db.execute(select(Vulnerability).where(Vulnerability.cve_id == cve)).scalars().all()
    if not vulns:
        return None
    vulns.sort(key=lambda v: (v.cvss_score is None, not (v.details or ""), v.id))
    return vulns[0]


def build_facts(db: Session, inc: Incident, language: str = "en") -> dict:
    """Returns {"facts": {...FACT fields...}, "context": {...for the prompt only...}, "defaults": {...TEXT defaults...}}."""
    s = app_settings.load(db)
    product: Product = inc.product
    kev = inc.kev
    pairs = incident_components(db, inc)
    vuln = _best_vuln(db, inc.cve_id)
    epss = db.get(EpssScore, inc.cve_id)
    unknown = UNKNOWN.get(language, UNKNOWN["en"])

    comps = []
    for m, c in pairs:
        comps.append({"name": c.name, "version": c.version, "purl": c.purl, "affected_range": m.affected_range, "match_type": m.match_type})
    ranges = sorted({f"{c['name']}@{c['version']} (upstream affected: {c['affected_range']})" for c in comps if c["affected_range"]})
    if ranges:
        versions_affected = "Product builds embedding " + "; ".join(ranges) + ". Exact product firmware/software versions: under investigation."
    else:
        versions_affected = "under investigation"

    aware_iso = inc.aware_at.isoformat()
    evidence = f"Listed in CISA KEV on {kev.date_added.isoformat()}; {kev.short_description or kev.vulnerability_name}"

    facts = {
        "manufacturer_name": s.manufacturer_name,
        "manufacturer_contact": s.manufacturer_contact,
        "product_name": product.name,
        "product_identifier": product.sku,
        "product_versions_affected": versions_affected,
        "vulnerability_id": inc.cve_id,
        "actively_exploited": True,
        "exploitation_evidence": evidence,
        "aware_at": aware_iso,
        "potentially_malicious": True,
        "request_confidentiality": True,
    }

    # Notification-stage FACTs
    ew = db.execute(
        select(Report)
        .where(Report.incident_id == inc.id, Report.stage == "early_warning", Report.status == "approved")
        .order_by(Report.reviewed_at.desc())
    ).scalars().first()
    facts["reference_to_early_warning"] = (
        f"Early warning report {ew.id} approved {ew.reviewed_at.isoformat()} by {ew.reviewed_by}" if ew and ew.reviewed_at else None
    )
    facts["affected_component"] = "; ".join(f"{c['name']} {c['version'] or ''} ({c['purl']})".strip() for c in comps) or unknown
    facts["cvss_score"] = vuln.cvss_score if vuln else None
    facts["cvss_vector"] = vuln.cvss_vector if vuln else None
    if epss:
        pct = f", percentile {epss.percentile:.1%}" if epss.percentile is not None else ""
        facts["epss_score"] = (
            f"{epss.epss:.3f}{pct} (FIRST EPSS as of {epss.score_date}: estimated probability of exploitation "
            f"in the next 30 days; used for triage ordering only)"
        )
    else:
        facts["epss_score"] = "not available"

    if s.member_states:
        ms = ", ".join(s.member_states)
        member_states_text = (f"Product is placed on the market in the following Member States: {ms}." if language == "en"
                              else f"Das Produkt wird in folgenden Mitgliedstaaten in Verkehr gebracht: {ms}.")
    else:
        member_states_text = DEFAULT_MEMBER_STATES.get(language, DEFAULT_MEMBER_STATES["en"])
    defaults = {
        "member_states_affected": member_states_text,
        "unknown": unknown,
    }

    context = {
        "language": language,
        "product_description": product.description,
        "product_lifecycle_status": product.lifecycle_status,
        "product_placed_on_market_at": product.placed_on_market_at.isoformat() if product.placed_on_market_at else None,
        "kev": {
            "vendor_project": kev.vendor_project,
            "product": kev.product,
            "vulnerability_name": kev.vulnerability_name,
            "date_added": kev.date_added.isoformat(),
            "short_description": kev.short_description,
            "required_action": kev.required_action,
            "known_ransomware_campaign_use": kev.known_ransomware_campaign_use,
            "cwes": kev.cwes,
        },
        "vulnerability": {
            "osv_id": vuln.id if vuln else None,
            "summary": vuln.summary if vuln else None,
            "details": (vuln.details or "")[:2500] if vuln else None,
            "cvss_score": vuln.cvss_score if vuln else None,
            "cvss_vector": vuln.cvss_vector if vuln else None,
        },
        "components": comps,
        "deadlines": {
            "early_warning": inc.deadline_early_warning.isoformat(),
            "notification": inc.deadline_notification.isoformat(),
            "final_report": inc.deadline_final_report.isoformat() + " (provisional)",
        },
    }
    return {"facts": facts, "context": context, "defaults": defaults}
