# Devpost submission — Frist24

## Tagline
CRA Article 14, without the panic: real KEV data opens the incident, a local model drafts the ENISA report, a human approves, the audit log proves it.

## Inspiration
"A CVE lands on CISA KEV at 16:00 Friday. It's in a library used in a controller we shipped in 2021 and stopped
selling in 2023. We have 40 SKUs. Who is affected? By 16:00 Saturday I owe ENISA an early warning. Today that's a
spreadsheet and a panic." Since 11 September 2026 this is the daily reality of every European manufacturer of
connected products under the Cyber Resilience Act. The obligation applies to legacy products, to one-person
companies and to non-EU manufacturers selling into the EU. Most have no PSIRT.

## What it does
Frist24 ingests SBOMs per product SKU, matches components against OSV.dev, and treats CISA KEV membership as
the single deterministic trigger for "actively exploited". A hit opens an incident and starts the 24h / 72h /
14d clocks live on screen. A local LLM (Ollama, llama3.1:8b) drafts the early warning and the 72-hour
notification in English and German; FACT fields are stamped from the database, the model only writes TEXT
fields, and every draft is `pending_review` until a named human approves. Every step lands in an append-only,
hash-chained audit log. The result is exported as a filing-ready package (JSON + PDF) that the human submits on
the ENISA single reporting platform.

## Why it matters for Europe
- It makes a brand-new EU obligation (CRA Art. 14, applicable since 11 Sep 2026) achievable for the Mittelstand
  without a dedicated security team.
- **Digital sovereignty by design:** the most sensitive data a manufacturer holds — unpatched, actively exploited
  vulnerabilities in its own products — never leaves its infrastructure. The model runs locally; feeds are one-way
  pulls of public data.
- It is built for the EU regulator's expectations: deterministic trigger, human oversight, attributable approvals,
  German-language output for the BSI, and honest "under investigation" instead of invented facts.

## How we built it
- **web/** Next.js 15 (App Router, TypeScript, Tailwind v4), live countdowns, three-column review UI with FACT/TEXT
  colour coding, audit page with chain verification.
- **api/** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, httpx, APScheduler; `cyclonedx-python-lib`,
  `spdx-tools`, `packageurl`, `cvss`, `reportlab`.
- **Postgres 16** with `BEFORE UPDATE/DELETE/TRUNCATE` triggers on `audit_log`; sha256 hash chain with an advisory
  lock so the chain cannot fork.
- **Ollama** (`llama3.1:8b`, fallback `mistral`) via HTTP, JSON mode, temperature 0, one retry, template fallback.
- **Data:** CISA KEV (1,713 entries), FIRST EPSS, OSV.dev — all live, nothing mocked. SBOMs are unmodified public
  CycloneDX files (Proton Mail web client; Keycloak 10.0.2) chosen because they contain KEV-listed components
  (`jquery@3.4.1` → CVE-2020-11023; `spring-beans` → CVE-2022-22965; `tomcat-embed-core` → CVE-2025-24813 …).
- `docker compose up` brings up web, api, db, ollama and a one-shot model pull. `make demo` opens five real
  incidents in ~45 seconds.

## Challenges
- Finding *real* public SBOMs whose components are hit by *real* KEV CVEs: we wrote `scripts/find_fixtures.py`
  (resolves all KEV CVEs through OSV: 219 verified package pairs) and `scripts/scan_public_sboms.py` (OSV
  querybatch over public SBOMs ∩ KEV: 20 hits) instead of inventing data.
- Making an 8B model safe for regulatory text: FACT fields are re-stamped from the database after generation, so
  the model literally cannot alter a fact; deviations are counted in the audit trail.
- The CRA's 14-day final-report clock is anchored to fix availability, not awareness; we model it as provisional
  and re-anchor it.

## Accomplishments
Vertical slice complete: real SBOM → real KEV match → incident with live countdown → local EN/DE draft → human
edit and approval → hash-chained audit → filing package. 17 API tests (incl. live-feed and live-Ollama), web unit
tests, smoke script over all endpoints, conventional commits per build step, `DECISIONS.md` and `TODO.md`.

## What we learned
Deterministic gating of the LLM is not a limitation, it is the feature: regulators, CISOs and the AI Act all
prefer a rule they can read over a model they cannot. The hard part of CRA compliance is knowing your components
and moving fast, not writing prose.

## What's next
ENISA EUVD as EU-native second exploitation source; fuzzy matching with LLM-assisted *confirmation* (always
`needs_review`); dedicated final-report prompt; severe-incident flow; SSO/RBAC; notifications when a new KEV
entry hits an existing component; optional Kubernetes deployment.

## Built with
next.js · typescript · tailwind · python · fastapi · sqlalchemy · alembic · pydantic · postgresql · ollama ·
llama3.1 · docker · cyclonedx · spdx · osv.dev · cisa-kev · first-epss · reportlab

---

## Video script (2–3 min)

**0:00–0:20 — Hook.** Screen: the dashboard, one countdown ticking 23:5x:xx.
"On 11 September the Cyber Resilience Act's reporting duty went live. If a vulnerability in one of your
products is being actively exploited, you owe ENISA an early warning within 24 hours. For most manufacturers
that starts with a spreadsheet. This is Frist24."

**0:20–0:50 — Products and real data.** Screen: /products.
"Two products: an operator panel we stopped selling in 2023 and an edge gateway. Their SBOMs are real public
CycloneDX files with 883 and 903 components. Frist24 pulls three real public feeds: CISA's Known Exploited
Vulnerabilities, FIRST's EPSS scores, and OSV.dev. Nothing here is mocked."

**0:50–1:20 — The rule.** Screen: press *Sync now*, /incidents fills.
"One rule opens an incident: a component matches a CVE, and that CVE is on KEV. No model involved. jQuery 3.4.1
in the panel's web UI was added to KEV in January 2025 — that is the legacy-product case the CRA is about. The
clock starts at the moment we became aware. Sorted by deadline."

**1:20–2:00 — Local drafting and review.** Screen: incident detail, click *Draft EN with local LLM*.
"Drafting happens on this machine. No vulnerability data leaves it." (spinner) "Green fields are facts from our
database — the model cannot change them, we stamp them back after generation. Amber fields are the model's text.
Switch to German — the BSI is our CSIRT." Edit one amber field, Save, Approve. "Approval is by a named person."

**2:00–2:30 — Audit and package.** Screen: timeline, then /audit *Verify chain*, then download.
"Every step is an append-only row with a hash chained to the previous one. The database refuses updates and
deletes. Verify recomputes the chain. The filing package — JSON and PDF, English and German — is what a human
submits on the ENISA platform."

**2:30–2:50 — Close.** Screen: architecture diagram.
"Deterministic first, LLM second, human always. Docker compose, Postgres, FastAPI, Next.js, Ollama. Built for
what Europe needs now: sovereignty and a deadline you can actually meet. Frist24."
