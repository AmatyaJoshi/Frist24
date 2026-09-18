# DATA_SOURCES.md — Real public feeds Frist24 depends on

All sources are free, unauthenticated, and one-way downloads. Verify each URL still
works before relying on it; if a URL has moved, find the current one on the
publisher's site and note the change in `DECISIONS.md`.

## 1. CISA Known Exploited Vulnerabilities (KEV) — the "actively exploited" oracle
- JSON: `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
- Fields per entry: `cveID`, `vendorProject`, `product`, `vulnerabilityName`,
  `dateAdded`, `shortDescription`, `requiredAction`, `dueDate`, `knownRansomwareCampaignUse`, `notes`, `cwes`.
- ~1,400+ entries, ~2 MB. Refresh every 15 min is polite enough; CISA updates a few times a week.
- **Rule:** `cveID in KEV` ⇒ `in_kev = true`. This is the only thing that opens an incident.
- Note: KEV is a US catalog. State in README that ENISA's EU Vulnerability Database (EUVD)
  exploitation flags are the natural EU-native second source; EUVD has an API but coverage
  and stability vary — treat it as a stretch goal, not a dependency.

## 2. FIRST EPSS — exploitation probability (triage ordering only)
- Daily CSV: `https://epss.cyentia.com/epss_scores-current.csv.gz`
- Columns: `cve`, `epss` (0–1 probability of exploitation in next 30 days), `percentile`.
- ~250k rows, ~10 MB gz. Load once per day; store only for CVEs we have matches for
  plus all KEV CVEs to keep the table small.
- Also has an API: `https://api.first.org/data/v1/epss?cve=CVE-XXXX-YYYY` (use for
  single lookups if the CSV load is slow to implement).

## 3. OSV.dev — component → vulnerability matching by PURL
- Single: `POST https://api.osv.dev/v1/query` body `{"package": {"purl": "pkg:npm/lodash@4.17.20"}}`
- Batch: `POST https://api.osv.dev/v1/querybatch` body `{"queries": [{"package": {"purl": ...}}, ...]}`
  (returns only IDs + modified; fetch details with `GET https://api.osv.dev/v1/vulns/{id}`)
- IDs may be `GHSA-*`, `PYSEC-*`, `OSV-*`, `CVE-*`. Details include `aliases` — extract the
  `CVE-*` alias. Also `affected[].ranges` for version ranges → store in `matches.affected_range`.
- Coverage is excellent for npm, PyPI, Maven, Go, crates.io, NuGet; weak for C/C++ firmware
  components. That is why the fuzzy path exists — but pick fixtures where PURL matching works.

## 4. NVD (optional, for CVSS scores and descriptions)
- `GET https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-XXXX-YYYY`
- Unauthenticated rate limit is low (~5 req / 30 s). Only fetch for CVEs that have matches.
  OSV details often already include severity; prefer OSV and treat NVD as enrichment.

## 5. SBOM formats
- **CycloneDX** JSON 1.4–1.6: components under `components[]` with `name`, `version`,
  `purl`, `cpe`, `supplier`. Parse with `cyclonedx-python-lib`.
- **SPDX** JSON 2.3: `packages[]` with `name`, `versionInfo`, `externalRefs[]` where
  `referenceType == "purl"`. Parse with `spdx-tools`.
- Public example SBOMs: the CycloneDX project publishes examples on GitHub; many popular
  OSS projects attach CycloneDX/SPDX SBOMs to their GitHub releases. Build step 2 must
  find real ones whose components include a KEV-listed CVE (check with OSV first).

## 6. Regulatory reference texts (for README and prompts, not for code)
- CRA text: Regulation (EU) 2024/2847, OJ L 20.11.2024. Article 14 (reporting), Article 16
  (single reporting platform), Article 71 (application dates), Article 64 (penalties), Annex I
  Part II (SBOM requirement).
- German competent authority: BSI. EU coordinator: ENISA.
- Commission practical guidance on the CRA: published 27 Jul 2026.

## Outbound hosts allow-list (log at startup, document in README)
`www.cisa.gov`, `epss.cyentia.com`, `api.first.org`, `api.osv.dev`, `services.nvd.nist.gov`,
plus the Ollama service. Nothing else.
