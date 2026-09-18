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
