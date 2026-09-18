# DECISIONS.md — non-obvious choices, newest last

Format: `YYYY-MM-DD — step — decision — why`.

- 2026-09-18 — step 1 — Moved the brief from repo root into `docs/` and `api/prompts/` — CLAUDE.md and BUILD_PLAN reference those paths; the files were delivered flat.
- 2026-09-18 — step 1 — `docs/SPEC.md` is referenced everywhere but was not delivered. Steps 1–2 do not need it. If it is still missing at step 3, the data model is derived from CLAUDE.md "Definitions", REPORT_SCHEMA.md and CONTEXT.md and documented in README.
- 2026-09-18 — step 1 — 14-day final-report clock: CRA anchors it to fix/workaround availability, not `aware_at`. We store a provisional `aware_at + 14d` labelled "provisional" and re-anchor when a fix date is recorded.
- 2026-09-18 — step 1 — `actively_exploited` is a boolean; the KEV `dateAdded` lives in `exploitation_evidence` (REPORT_SCHEMA already puts it there).
- 2026-09-18 — step 1 — Web container runs `next dev` (not a production build). Cold start in seconds on a clean clone matters more than bundle size for a demo; production build is a TODO.
- 2026-09-18 — step 1 — Tailwind v4 via `@tailwindcss/postcss` (zero-config) rather than v3 with `tailwind.config.js`. Less to scaffold; shadcn/ui supports v4.
- 2026-09-18 — step 1 — Model pull is a separate one-shot compose service (`ollama-pull`) that depends on `ollama` being healthy, instead of overriding the ollama image entrypoint. Keeps the upstream image untouched and lets `ollama` report healthy before the multi-GB pull finishes.
- 2026-09-18 — step 1 — Dev machine has no `make`; the Makefile is kept (teammates / judges on Linux/macOS) and every target is a thin wrapper around a `docker compose` command that is also documented in README.
- 2026-09-18 — step 1 — PDF export will use `reportlab` (pure Python) instead of WeasyPrint, to avoid system libs (cairo/pango) in the API image.
- 2026-09-18 — step 2 — Fixtures: protonmail-webclient-v4 (jquery@3.4.1 → CVE-2020-11023) and keycloak-10.0.2 (spring-beans → CVE-2022-22965, tomcat-embed-core → CVE-2025-24813 et al.) from CycloneDX/bom-examples, owner-approved. Files kept byte-identical to upstream; renamed to product-like names, provenance in fixtures/README.md.
- 2026-09-18 — step 2 — Both fixtures are CycloneDX **1.2**. If cyclonedx-python-lib refuses 1.2 input, the ingest falls back to a plain-JSON reader for `components[].{name,version,purl}` (same fields for 1.2–1.6).
- 2026-09-18 — step 2 — `docs/SPEC.md` still absent; owner said proceed. Data model for step 3 is derived from CLAUDE.md, REPORT_SCHEMA.md, CONTEXT.md and recorded in README "Data model".
- 2026-09-18 — step 2 — Container-level "Done when" checks are deferred until a machine with a working Docker engine is available (owner acknowledged). Local venv + npm used for verification.
- 2026-09-18 — step 3 — Audit chain: sha256(prev_hash || canonical JSON of {ts, actor, action, entity_type, entity_id, payload}); writers take `pg_advisory_xact_lock` so the chain cannot fork under concurrency. Append-only enforced by BEFORE UPDATE/DELETE/TRUNCATE triggers in migration 0001, not just by convention.
- 2026-09-18 — step 3 — Incident deadlines stored as columns (`deadline_early_warning`, `deadline_notification`, `deadline_final_report` + `final_report_anchor`) rather than computed on read, so the audit payload can carry the exact values shown to the reviewer.
- 2026-09-18 — step 3 — API container runs `alembic upgrade head` before uvicorn (compose `command`) so a clean clone needs no manual migration step.
- 2026-09-18 — step 3 — Local dev/test without Docker uses `pgserver` (embedded Postgres 16, pip-installable, no admin). `scripts/dev_pg.py` starts it; tests skip cleanly when DATABASE_URL is unreachable.
- 2026-09-18 — step 4 — Re-uploading a byte-identical SBOM to the same product is a no-op (matched by sha256) so `make demo` is idempotent. Different bytes create a new SBOM row; components of all SBOMs of a product are matched (no "current SBOM" concept yet).
- 2026-09-18 — step 4 — Single reviewer role: the `X-Actor` header names who acted (default "reviewer"). No auth in the prototype; documented as a limitation.
- 2026-09-18 — step 4 — SPDX parser covered by a hand-written 3-package SPDX 2.3 document built from the real KEV-hit PURLs (no published SPDX SBOM with a KEV hit was found in time). Clearly labelled in fixtures/README.md; not used by the demo.
