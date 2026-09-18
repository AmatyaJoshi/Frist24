# BUILD_PLAN.md — Ordered steps, time budget, cut list

Commit after every step (`feat(step-N): ...`). Show the directory tree before each step.
Team hours available ≈ 90 (3 people × ~30h) before Sat 20 Sep 17:00 CEST. Plan uses ~40.

| # | Step | Est. | Done when |
|---|------|------|-----------|
| 1 | Scaffold: monorepo layout, `docker-compose.yml` (web, api, db, ollama + model-pull entrypoint), `Makefile` (up/down/demo/logs/reset), `.env.example`, `README.md` skeleton with Mermaid architecture, `DECISIONS.md`, `TODO.md` | 2h | `make up` brings all four containers healthy; `/health` returns ok; web renders a placeholder |
| 2 | **Pick real fixtures.** Script `scripts/find_fixtures.py`: pull KEV, take KEV CVEs, query OSV for which npm/PyPI/Maven packages+versions are affected, propose 3 candidates. Human picks. Download/construct real CycloneDX SBOMs into `fixtures/sboms/`, document CVE IDs in `fixtures/README.md` | 2h | Two SBOMs in repo, each with ≥1 PURL known to hit a KEV CVE via OSV |
| 3 | DB: SQLAlchemy models per SPEC §2, Alembic initial migration, append-only trigger on `audit_log`, hash-chain helper `audit.append(actor, action, entity, payload)`, seed script | 3h | `alembic upgrade head` clean; attempting `UPDATE audit_log` raises; seed inserts 2 products |
| 4 | SBOM ingest: `POST /products/{id}/sbom` parses CycloneDX + SPDX → components. Unit test on fixtures | 2h | Both fixtures parse; component counts logged; audit event emitted |
| 5 | Feed sync: KEV loader, EPSS loader, OSV batch matcher, incident-opening rule, APScheduler job + `POST /sync` | 5h | `make demo` opens ≥1 incident from a real KEV CVE; deadlines computed |
| 6 | Remaining API endpoints (incidents, reports edit/approve/reject, audit list/verify) with Pydantic schemas; OpenAPI clean | 3h | All endpoints exercised by a `scripts/smoke.sh` |
| 7 | Web: layout, `/products` (table + SBOM upload drawer), `/incidents` (deadline-sorted, live countdown component) | 5h | Incident list shows live countdown after `make demo` |
| 8 | Ollama drafting: prompt files `api/prompts/early_warning.md`, `notification.md`; `POST /draft/{stage}`; JSON mode + Pydantic validation + one retry + template fallback; record model/prompt_version | 4h | Early warning drafts in EN and DE validate against schema on the demo incident |
| 9 | Web: `/incidents/[id]` three-column view, fact/model colour coding, edit form, Approve/Reject, timeline; `/audit` with Verify | 6h | Full flow clickable: draft → edit → approve → audit row with hash |
| 10 | Export package: JSON + PDF (EN+DE) via WeasyPrint or reportlab; `GET /incidents/{id}/package` | 2h | Zip downloads and opens |
| 11 | Polish: empty/loading/error states, "drafting locally" messaging, deadline colour thresholds, seed reset, `make demo` < 60s | 3h | Cold `make demo` run passes on a teammate's machine |
| 12 | README final: problem, architecture, quickstart, data sources, real-vs-simulated, limitations, EU AI Act & GDPR notes, roadmap. Devpost text + video script in `docs/DEVPOST.md` | 3h | Someone unfamiliar can run it from README alone |

## Freeze rule
**Feature freeze at Sat 20 Sep 09:00 CEST.** After that only bug fixes, README, video.
Video recording 10:00–13:00. Devpost submission by 15:00 (two-hour buffer).

## Cut list (in this order if behind schedule)
1. Final report stage (schema only, no UI)
2. German language (keep EN; note DE as roadmap)
3. PDF in export (ship JSON only)
4. SPDX support (CycloneDX only)
5. Fuzzy/LLM-confirmed matching path (PURL exact only — but keep the "needs review" UI stub)
6. Second product SKU in demo
7. Countdown colour thresholds / polish

## Never cut
- Real KEV data and real OSV matching
- Deterministic gating of the LLM
- Human approval step
- Append-only hash-chained audit log
- `docker compose up` working from a clean clone
