# Fixtures — real public SBOMs used by the demo

Both files are **unmodified CycloneDX 1.2 JSON SBOMs** published by the CycloneDX project in
<https://github.com/CycloneDX/bom-examples> (master, fetched 2026-09-18). They describe real open-source
applications. Frist24's demo pretends a manufacturer embeds them in two product SKUs; that
product mapping is the only simulated part. Every component, PURL, CVE and KEV entry is real.

Selection method: `scripts/find_fixtures.py` resolved all 1,713 live KEV CVEs through OSV.dev
(219 verified package pairs); `scripts/scan_public_sboms.py` then ran OSV `querybatch` over the
public example SBOMs and intersected the results with KEV. Chosen by the project owner on 2026-09-18.

| Demo SKU | File | Source SBOM | Components | KEV-listed component(s) | CVE | KEV dateAdded |
|---|---|---|---|---|---|---|
| `HMI-4100` HMI web UI | `sboms/hmi-web-ui.cdx.json` | `SBOM/protonmail-webclient-v4-0912dff/bom.json` | 883 | `pkg:npm/jquery@3.4.1` | CVE-2020-11023 (XSS) | 2025-01-23 |
| `EGW-7200` edge gateway | `sboms/edge-gateway.cdx.json` | `SBOM/keycloak-10.0.2/bom.json` | 903 | `pkg:maven/org.springframework/spring-beans@5.0.9.RELEASE` (+ 4.3.x, 3.2.13, spring-webmvc, spring-boot-starter-web) | CVE-2022-22965 (Spring4Shell RCE) | 2022-04-04 |
| | | | | `pkg:maven/org.apache.tomcat.embed/tomcat-embed-core@8.5.39` (+ 8.5.34, tomcat-catalina 8.5.38) | CVE-2025-24813 (path equivalence RCE) | 2025-04-01 |
| | | | | `pkg:maven/org.apache.tomcat.embed/tomcat-embed-core@8.5.39` | CVE-2020-1938 (Ghostcat AJP) | 2022-03-03 |
| | | | | `tomcat-embed-core`, `tomcat-coyote@8.5.38` | CVE-2023-44487 (HTTP/2 Rapid Reset) | 2023-10-10 |

SHA-256 (first 16 hex): `hmi-web-ui.cdx.json` = `a2e17be40185098c`, `edge-gateway.cdx.json` = `445136956fe11725`.

Why these two: the jQuery case is the CRA "legacy product" story (component shipped years ago,
added to KEV in 2025). The Keycloak SBOM opens several incidents from one upload, which shows
deadline-sorted triage. Ecosystems npm + Maven both have excellent OSV coverage (PURL exact match).

Regenerate the candidate lists any time (needs network, ~2 min):
```bash
python scripts/find_fixtures.py --top 40
python scripts/scan_public_sboms.py
```
