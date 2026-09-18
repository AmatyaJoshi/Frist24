# CLAUDE.md — Frist24

You are the lead engineer on **Frist24**, a hackathon project for MunichTech EXPO
(Devpost deadline: **Saturday 20 September 2026, 17:00 CEST**).

Read these before writing any code, in this order:
1. `docs/CONTEXT.md` — why this exists, who judges it, what wins
2. `docs/SPEC.md` — product, architecture, data model, API, UI
3. `docs/DATA_SOURCES.md` — the real public feeds we rely on
4. `docs/REPORT_SCHEMA.md` — the report fields the LLM must produce
5. `docs/BUILD_PLAN.md` — the ordered build steps and time budget

## One-paragraph summary
Frist24 helps European manufacturers of products with digital elements meet the
EU Cyber Resilience Act (CRA) **Article 14** reporting duty, in force since
11 Sep 2026. It ingests SBOMs, matches components against live public
vulnerability feeds, detects "actively exploited" vulnerabilities via CISA KEV,
starts the 24h / 72h / 14d countdown, has a **local** LLM draft the ENISA
reports, requires human approval, and writes everything to a hash-chained
audit log. No vulnerability data leaves the machine.

## Non-negotiable rules
- **Deterministic first, LLM second.** KEV membership decides "actively exploited".
  The LLM drafts text and confirms fuzzy matches; it never overrides a rule.
- **Every AI output is a draft** with `status = pending_review` until a human approves.
- **Real data only.** CISA KEV, FIRST EPSS, OSV.dev. No mocked vulnerability data anywhere.
- **`docker compose up` must bring up everything.** No external SaaS, no cloud LLM.
- **Audit log is append-only and hash-chained.** Never update or delete rows in it.
- Do not implement submission to the ENISA platform (no public API). We produce a
  filing-ready package; the human submits.

## Working style
- Vertical slice over breadth. A flawless 24h + 72h flow beats a half-built everything.
- Commit after every build step in `docs/BUILD_PLAN.md`, conventional commits.
- Ask only when a decision is blocking. Otherwise pick the simplest option and note it in `DECISIONS.md`.
- Show the directory tree before writing code for a new step.
- Keep a `TODO.md` of cut scope so we can write honest "Limitations" in the README.

## Stack (fixed — do not switch)
- `web/` Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui allowed
- `api/` Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, httpx, APScheduler
- Postgres 16
- Ollama (`llama3.1:8b`, fallback `mistral`), called via HTTP from `api/`
- SBOM: `cyclonedx-python-lib`, `spdx-tools`; fuzzy matching: `rapidfuzz`
- Tests: `pytest` for api, `vitest` for web (smoke-level only; time is short)

## Definitions
- **PURL** — package URL, e.g. `pkg:npm/lodash@4.17.20`. Primary matching key.
- **KEV** — CISA Known Exploited Vulnerabilities catalog. Presence = "actively exploited".
- **EPSS** — probability (0–1) a CVE is exploited in the next 30 days. Used for triage ordering only.
- **Incident** — one product × one KEV-listed CVE. Owns the deadlines and the reports.
- **aware_at** — timestamp the incident was created. All CRA clocks start here.
