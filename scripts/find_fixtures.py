"""Step 2 helper: find KEV-listed CVEs that OSV maps to a package in a mainstream ecosystem.

Usage:  python scripts/find_fixtures.py [--top 15] [--ecosystems npm,PyPI,Maven]

1. Download the live CISA KEV catalog.
2. For every KEV CVE, GET https://api.osv.dev/v1/vulns/{cve}; follow GHSA/PYSEC/GO/RUSTSEC aliases.
3. Keep entries whose `affected[].package.ecosystem` is in the target set and derive one
   concrete vulnerable version (from `versions`, else the range `introduced` event).
4. Verify each candidate the way the app will: POST /v1/query with the PURL and check the
   CVE (or its alias) comes back.
5. Print a ranked table and write scripts/out/fixture_candidates.json.

Only real data. Nothing is mocked. Responses are cached in scripts/out/osv_cache.json.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
OSV = "https://api.osv.dev/v1"
OUT = Path(__file__).parent / "out"
CACHE = OUT / "osv_cache.json"
ALIAS_PREFIXES = ("GHSA-", "PYSEC-", "GO-", "RUSTSEC-", "OSV-", "MAL-")
PURL_TYPE = {"npm": "npm", "PyPI": "pypi", "Maven": "maven", "Go": "golang", "crates.io": "cargo", "NuGet": "nuget"}


def purl_for(eco: str, name: str, version: str) -> str:
    t = PURL_TYPE[eco]
    if eco == "Maven":
        group, artifact = name.split(":", 1)
        return f"pkg:maven/{group}/{artifact}@{version}"
    if eco == "PyPI":
        name = name.lower().replace("_", "-")
    return f"pkg:{t}/{name}@{version}"


def pick_version(affected: dict) -> str | None:
    versions = affected.get("versions") or []
    if versions:
        return versions[-1]  # highest listed vulnerable version
    for rng in affected.get("ranges", []):
        if rng.get("type") in ("ECOSYSTEM", "SEMVER"):
            intro = [e["introduced"] for e in rng.get("events", []) if e.get("introduced") not in (None, "0")]
            if intro:
                return intro[0]
    return None


def range_text(affected: dict) -> str:
    parts = []
    for rng in affected.get("ranges", []):
        if rng.get("type") not in ("ECOSYSTEM", "SEMVER"):
            continue
        ev = rng.get("events", [])
        intro = next((e["introduced"] for e in ev if "introduced" in e), "0")
        fixed = next((e.get("fixed") or e.get("last_affected") for e in ev if "fixed" in e or "last_affected" in e), None)
        parts.append(f">={intro}" + (f",<{fixed}" if fixed else ""))
    return " || ".join(parts) or "unspecified"


class Osv:
    def __init__(self, client: httpx.AsyncClient, cache: dict):
        self.c, self.cache, self.sem = client, cache, asyncio.Semaphore(12)

    async def vuln(self, vid: str) -> dict | None:
        if vid in self.cache:
            return self.cache[vid]
        async with self.sem:
            for attempt in range(3):
                try:
                    r = await self.c.get(f"{OSV}/vulns/{vid}", timeout=30)
                    break
                except httpx.HTTPError:
                    await asyncio.sleep(1.5 * (attempt + 1))
            else:
                return None
        data = r.json() if r.status_code == 200 else None
        self.cache[vid] = data
        return data

    async def query_purl(self, purl: str) -> list[str]:
        async with self.sem:
            r = await self.c.post(f"{OSV}/query", json={"package": {"purl": purl}}, timeout=30)
        r.raise_for_status()
        return [v["id"] for v in r.json().get("vulns", [])]


async def resolve(osv: Osv, kev: dict, ecos: set[str]) -> list[dict]:
    cve = kev["cveID"]
    root = await osv.vuln(cve)
    if not root:
        return []
    ids = [cve] + [a for a in root.get("aliases", []) if a.startswith(ALIAS_PREFIXES)]
    records = [root] + [r for r in await asyncio.gather(*(osv.vuln(a) for a in ids[1:])) if r]
    out, seen = [], set()
    for rec in records:
        for aff in rec.get("affected", []):
            pkg = aff.get("package") or {}
            eco, name = pkg.get("ecosystem", "").split(":")[0], pkg.get("name")
            if eco not in ecos or not name or (eco, name) in seen:
                continue
            ver = pick_version(aff)
            if not ver:
                continue
            seen.add((eco, name))
            sev = next((s.get("score") for s in rec.get("severity", []) if s.get("type") == "CVSS_V3"), None)
            out.append({
                "cve": cve, "osv_id": rec["id"], "ecosystem": eco, "package": name,
                "vulnerable_version": ver, "affected_range": range_text(aff),
                "purl": purl_for(eco, name, ver), "cvss_v3_vector": sev,
                "kev_date_added": kev["dateAdded"], "kev_vendor": kev["vendorProject"],
                "kev_product": kev["product"], "kev_name": kev["vulnerabilityName"],
                "ransomware": kev.get("knownRansomwareCampaignUse"),
                "summary": (rec.get("summary") or kev["shortDescription"])[:140],
            })
    return out


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--ecosystems", default="npm,PyPI,Maven,Go,crates.io,NuGet")
    args = ap.parse_args()
    ecos = set(args.ecosystems.split(","))
    OUT.mkdir(exist_ok=True)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": "frist24-fixture-finder"}) as c:
        kev = (await c.get(KEV_URL, timeout=60)).json()
        print(f"KEV catalog {kev['catalogVersion']}: {kev['count']} entries", file=sys.stderr)
        osv = Osv(c, cache)
        results = await asyncio.gather(*(resolve(osv, v, ecos) for v in kev["vulnerabilities"]))
        cands = [x for group in results for x in group]
        print(f"{len(cands)} (CVE, package) pairs in {sorted(ecos)}; verifying PURL queries...", file=sys.stderr)
        for cand in cands:
            try:
                hits = await osv.query_purl(cand["purl"])
            except httpx.HTTPError as e:
                hits, cand["verify_error"] = [], str(e)
            cand["purl_query_hits"] = hits
            cand["verified"] = cand["cve"] in hits or cand["osv_id"] in hits
    CACHE.write_text(json.dumps(cache))

    cands.sort(key=lambda x: (not x["verified"], x["kev_date_added"]), reverse=False)
    verified = [x for x in cands if x["verified"]]
    verified.sort(key=lambda x: x["kev_date_added"], reverse=True)
    (OUT / "fixture_candidates.json").write_text(json.dumps(verified, indent=2))

    by_eco: dict[str, int] = {}
    for x in verified:
        by_eco[x["ecosystem"]] = by_eco.get(x["ecosystem"], 0) + 1
    print(f"\n{len(verified)} verified candidates by ecosystem: {by_eco}\n")
    print(f"{'CVE':<16}{'eco':<9}{'package':<48}{'version':<14}{'KEV added':<12}{'RW':<4}vendor/product")
    for x in verified[: args.top]:
        print(f"{x['cve']:<16}{x['ecosystem']:<9}{x['package'][:47]:<48}{x['vulnerable_version'][:13]:<14}{x['kev_date_added']:<12}{(x['ransomware'] or '')[:3]:<4}{x['kev_vendor']} / {x['kev_product']}")
    print(f"\nfull list: {OUT / 'fixture_candidates.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
