"""Step 2 helper: scan real public CycloneDX SBOMs for components hit by a KEV-listed CVE.

Downloads the JSON SBOMs from github.com/CycloneDX/bom-examples, extracts PURLs, runs OSV
querybatch (exactly what the app will do in step 5), resolves OSV ids to CVE aliases and
intersects with the live CISA KEV catalog. Writes scripts/out/public_sbom_hits.json.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

RAW = "https://raw.githubusercontent.com/CycloneDX/bom-examples/master/"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
OSV = "https://api.osv.dev/v1"
OUT = Path(__file__).parent / "out"
CACHE = OUT / "osv_cache.json"

SBOMS = [
    "SBOM/cern-lhc-vdm-editor-e564943/bom.json",
    "SBOM/dropwizard-1.3.15/bom.json",
    "SBOM/juice-shop/v11.1.2/bom.json",
    "SBOM/keycloak-10.0.2/bom.json",
    "SBOM/laravel-7.12.0/bom.1.4.json",
    "SBOM/proton-bridge/proton-bridge-v1.8.0.bom.json",
    "SBOM/protonmail-webclient-v4-0912dff/bom.json",
]


async def main() -> int:
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    async with httpx.AsyncClient(follow_redirects=True, timeout=60, headers={"User-Agent": "frist24"}) as c:
        kev = {v["cveID"]: v for v in (await c.get(KEV_URL)).json()["vulnerabilities"]}
        print(f"KEV: {len(kev)} CVEs", file=sys.stderr)
        hits = []
        for path in SBOMS:
            bom = (await c.get(RAW + path)).json()
            comps = [x for x in bom.get("components", []) if x.get("purl")]
            purls = sorted({x["purl"] for x in comps})
            print(f"{path}: {len(bom.get('components', []))} components, {len(purls)} purls", file=sys.stderr)
            id_by_purl: dict[str, list[str]] = {}
            for i in range(0, len(purls), 500):
                chunk = purls[i : i + 500]
                r = await c.post(f"{OSV}/querybatch", json={"queries": [{"package": {"purl": p}} for p in chunk]})
                r.raise_for_status()
                for p, res in zip(chunk, r.json()["results"]):
                    ids = [v["id"] for v in res.get("vulns", [])]
                    if ids:
                        id_by_purl[p] = ids
            # resolve every OSV id to its CVE aliases
            all_ids = sorted({i for ids in id_by_purl.values() for i in ids})
            sem = asyncio.Semaphore(12)

            async def fetch(vid: str):
                if vid in cache:
                    return
                async with sem:
                    r = await c.get(f"{OSV}/vulns/{vid}")
                cache[vid] = r.json() if r.status_code == 200 else None

            await asyncio.gather(*(fetch(v) for v in all_ids))
            for purl, ids in id_by_purl.items():
                comp = next(x for x in comps if x["purl"] == purl)
                cves = set()
                for vid in ids:
                    rec = cache.get(vid) or {}
                    for a in [vid] + rec.get("aliases", []):
                        if a.startswith("CVE-"):
                            cves.add(a)
                kev_cves = sorted(cv for cv in cves if cv in kev)
                if kev_cves:
                    hits.append({
                        "sbom": path, "purl": purl, "name": comp.get("name"), "version": comp.get("version"),
                        "osv_ids": ids, "all_cves": len(cves), "kev_cves": kev_cves,
                        "kev": [{"cve": cv, "dateAdded": kev[cv]["dateAdded"], "name": kev[cv]["vulnerabilityName"],
                                 "ransomware": kev[cv].get("knownRansomwareCampaignUse")} for cv in kev_cves],
                    })
    CACHE.write_text(json.dumps(cache))
    (OUT / "public_sbom_hits.json").write_text(json.dumps(hits, indent=2))
    print(f"\n{len(hits)} components in public SBOMs hit a KEV CVE:\n")
    for h in hits:
        print(f"- {h['sbom']}\n    {h['purl']}\n    KEV: " + "; ".join(f"{k['cve']} (added {k['dateAdded']}, {k['name'][:60]})" for k in h["kev"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
