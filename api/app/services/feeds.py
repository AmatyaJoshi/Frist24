"""Feed loaders: CISA KEV, FIRST EPSS, OSV.dev. Real data only; nothing is mocked.

Outbound hosts are limited to app.config.OUTBOUND_ALLOWLIST (asserted here).
"""
from __future__ import annotations

import csv
import gzip
import io
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import OUTBOUND_ALLOWLIST, get_settings
from app.models import EpssScore, KevEntry, Vulnerability

log = logging.getLogger("frist24.feeds")
UA = {"User-Agent": "Frist24/0.1 (CRA Art.14 assistant; one-way public feed pull)"}


def _assert_allowed(url: str) -> None:
    host = urlparse(url).hostname or ""
    if host not in OUTBOUND_ALLOWLIST:
        raise RuntimeError(f"outbound host {host!r} is not on the allow-list")


def _client(timeout: float = 120) -> httpx.Client:
    return httpx.Client(timeout=timeout, follow_redirects=True, headers=UA)


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


# ----------------------------------------------------------------------------- KEV
def load_kev(db: Session) -> dict:
    """Upsert the whole KEV catalog. Returns {total, new, catalog_version, new_cves}."""
    url = get_settings().kev_url
    _assert_allowed(url)
    with _client() as c:
        data = c.get(url).json()
    existing = {k.cve_id: k for k in db.execute(select(KevEntry)).scalars()}
    now = datetime.now(UTC)
    new_cves: list[str] = []
    for v in data["vulnerabilities"]:
        cve = v["cveID"]
        fields = dict(
            vendor_project=v.get("vendorProject"),
            product=v.get("product"),
            vulnerability_name=v.get("vulnerabilityName"),
            date_added=_parse_date(v.get("dateAdded")) or now.date(),
            short_description=v.get("shortDescription"),
            required_action=v.get("requiredAction"),
            due_date=_parse_date(v.get("dueDate")),
            known_ransomware_campaign_use=v.get("knownRansomwareCampaignUse"),
            notes=v.get("notes"),
            cwes=v.get("cwes") or [],
            last_seen_at=now,
        )
        row = existing.get(cve)
        if row is None:
            db.add(KevEntry(cve_id=cve, first_seen_at=now, **fields))
            new_cves.append(cve)
        else:
            for k, val in fields.items():
                setattr(row, k, val)
    db.flush()
    log.info("KEV %s: %d entries, %d new", data.get("catalogVersion"), data["count"], len(new_cves))
    return {"total": data["count"], "new": len(new_cves), "catalog_version": data.get("catalogVersion"), "new_cves": new_cves}


# ----------------------------------------------------------------------------- EPSS
def load_epss(db: Session, keep: set[str]) -> dict:
    """Download the daily EPSS CSV and store rows for `keep` CVEs only (KEV + matched)."""
    url = get_settings().epss_csv_url
    _assert_allowed(url)
    with _client() as c:
        raw = c.get(url).content
    text = gzip.decompress(raw).decode("utf-8")
    lines = text.splitlines()
    score_date = None
    if lines and lines[0].startswith("#"):
        for part in lines[0].lstrip("#").split(","):
            if part.startswith("score_date:"):
                score_date = _parse_date(part.split(":", 1)[1])
        lines = lines[1:]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    existing = {e.cve_id: e for e in db.execute(select(EpssScore).where(EpssScore.cve_id.in_(keep))).scalars()} if keep else {}
    n = 0
    now = datetime.now(UTC)
    for row in reader:
        cve = row.get("cve")
        if cve not in keep:
            continue
        n += 1
        vals = dict(epss=float(row["epss"]), percentile=float(row["percentile"]) if row.get("percentile") else None, score_date=score_date, fetched_at=now)
        if cve in existing:
            for k, v in vals.items():
                setattr(existing[cve], k, v)
        else:
            db.add(EpssScore(cve_id=cve, **vals))
    db.flush()
    log.info("EPSS %s: stored %d of %d requested CVEs", score_date, n, len(keep))
    return {"stored": n, "requested": len(keep), "score_date": str(score_date)}


# ----------------------------------------------------------------------------- OSV
def osv_querybatch(purls: list[str]) -> dict[str, list[dict]]:
    """purl -> [{id, modified}] using POST /querybatch in chunks of 500."""
    base = get_settings().osv_api_url
    _assert_allowed(base)
    out: dict[str, list[dict]] = {}
    with _client() as c:
        for i in range(0, len(purls), 500):
            chunk = purls[i : i + 500]
            r = c.post(f"{base}/querybatch", json={"queries": [{"package": {"purl": p}} for p in chunk]})
            r.raise_for_status()
            for p, res in zip(chunk, r.json().get("results", [])):
                vulns = res.get("vulns") or []
                if vulns:
                    out[p] = vulns
    return out


def _cve_alias(rec: dict) -> str | None:
    if rec["id"].startswith("CVE-"):
        return rec["id"]
    cves = sorted(a for a in rec.get("aliases", []) if a.startswith("CVE-"))
    return cves[0] if cves else None


def _cvss(rec: dict) -> tuple[float | None, str | None]:
    vec = None
    for s in rec.get("severity") or []:
        if s.get("type") in ("CVSS_V4", "CVSS_V3") and s.get("score"):
            vec = s["score"]
            if s["type"] == "CVSS_V3":
                break
    if not vec:
        return None, None
    try:
        from cvss import CVSS3, CVSS4

        if vec.startswith("CVSS:4"):
            return float(CVSS4(vec).base_score), vec
        return float(CVSS3(vec).scores()[0]), vec
    except Exception:  # noqa: BLE001
        return None, vec


def affected_range_for(rec: dict, purl: str) -> str | None:
    """Human-readable affected range for the package named in `purl`, from the OSV record."""
    try:
        from packageurl import PackageURL

        p = PackageURL.from_string(purl)
        name = f"{p.namespace}:{p.name}" if p.type == "maven" and p.namespace else (f"{p.namespace}/{p.name}" if p.namespace else p.name)
    except ValueError:
        return None
    parts = []
    for aff in rec.get("affected", []):
        pkg = aff.get("package") or {}
        if (pkg.get("name") or "").lower() != name.lower():
            continue
        for rng in aff.get("ranges", []):
            if rng.get("type") not in ("ECOSYSTEM", "SEMVER"):
                continue
            ev = rng.get("events", [])
            intro = next((e["introduced"] for e in ev if "introduced" in e), "0")
            fixed = next((e.get("fixed") for e in ev if "fixed" in e), None)
            last = next((e.get("last_affected") for e in ev if "last_affected" in e), None)
            s = f">= {intro}"
            if fixed:
                s += f", fixed in {fixed}"
            elif last:
                s += f", <= {last}"
            parts.append(s)
    return "; ".join(dict.fromkeys(parts)) or None


def fetch_vulns(db: Session, ids_modified: dict[str, str | None]) -> dict[str, dict]:
    """Ensure every OSV id is in `vulnerabilities` (refetch if `modified` changed). Returns id -> raw record."""
    base = get_settings().osv_api_url
    _assert_allowed(base)
    have = {v.id: v for v in db.execute(select(Vulnerability).where(Vulnerability.id.in_(list(ids_modified)))).scalars()}
    need = [i for i, m in ids_modified.items() if i not in have or (m and have[i].modified and _parse_dt(m) != have[i].modified)]
    records: dict[str, dict] = {}

    def get(vid: str) -> tuple[str, dict | None]:
        with _client(60) as c:
            for attempt in range(3):
                try:
                    r = c.get(f"{base}/vulns/{vid}")
                    return vid, (r.json() if r.status_code == 200 else None)
                except httpx.HTTPError:
                    if attempt == 2:
                        return vid, None
        return vid, None

    if need:
        with ThreadPoolExecutor(max_workers=12) as ex:
            for vid, rec in ex.map(get, need):
                if not rec:
                    continue
                records[vid] = rec
                score, vec = _cvss(rec)
                vals = dict(
                    cve_id=_cve_alias(rec),
                    summary=rec.get("summary"),
                    details=(rec.get("details") or "")[:20000] or None,
                    aliases=rec.get("aliases") or [],
                    severity=rec.get("severity") or [],
                    cvss_score=score,
                    cvss_vector=vec,
                    published=_parse_dt(rec.get("published")),
                    modified=_parse_dt(rec.get("modified")),
                    fetched_at=datetime.now(UTC),
                )
                if vid in have:
                    for k, v in vals.items():
                        setattr(have[vid], k, v)
                else:
                    row = Vulnerability(id=vid, **vals)
                    db.add(row)
                    have[vid] = row
        db.flush()
    log.info("OSV: %d vulns referenced, %d fetched", len(ids_modified), len(need))
    return records
