# STATUS.md — Phase 0 verification pass (2026-09-21)

Scope of this pass: static verification on the development laptop plus the owner's confirmed container run on
2026-09-20. The development laptop has no Docker engine and, by the owner's instruction, no services are started
on it; the fresh-clone container verification therefore has to be re-run on the Docker laptop (commands below).

## Verdict
**Ready for live demo: YES, conditionally.** The full flow (real KEV incident → local-model early warning →
approval → audit → package) was exercised end to end on the Docker laptop on 2026-09-20 by the owner, on commit
`864f162` or later. Not independently re-verified from a fresh clone on 2026-09-21. Do the fresh-clone run below
before recording anything.

## What runs (verified how)
| Area | State | Verified |
|---|---|---|
| Compose stack: web, api, db, ollama, ollama-pull | runs | owner, Docker laptop, 2026-09-20 |
| `python -m app.cli demo` (seed → 5 real SBOMs, 87 SKUs → KEV/OSV/EPSS sync → ~207 real-rule incidents → staged history) | runs | owner report 2026-09-20 ("everything happened as expected") |
| Local LLM drafting EN + DE (llama3.1:8b, CPU 2–4 min per draft) | runs | live pytest + HTTP on 2026-09-18; owner UI 2026-09-20 |
| Template fallback, FACT re-stamping, retry | runs | pytest (fake LLM) |
| Append-only trigger + hash chain + verify | runs | pytest against Postgres 16 |
| Filing package zip (JSON + PDF, EN/DE) | runs | pytest |
| Editable settings (`app_settings`, migration 0002) | code complete | **not run against a DB by me**; owner saw the Settings page on 2026-09-20 |
| Webhook alerts | code complete | pytest (mocked httpx); never fired against a real endpoint |
| Web: overview, products (+detail), incidents (+detail), audit, settings, skeletons, pagination, light/dark | builds | `tsc` clean, vitest 4/4, `next build` clean on 2026-09-18 (later changes tsc-only) |

Test inventory: 22 API tests (17 need Postgres, 1 needs live Ollama, 1 needs live feeds), 4 web tests.
On this laptop today: tsc clean, vitest 4/4, DB-less API tests 5/5.

## What is mocked or staged
- Nothing in the vulnerability data. KEV, EPSS, OSV responses and SBOMs are real.
- **Staged:** the manufacturer identity, the product catalogue (85 generated SKUs sharing 5 real SBOMs), and the
  workflow history (aware_at dates 2024–2026, approvals/rejections by demo personas). All staged audit rows carry
  `synthetic_history: true`. `DEMO_HISTORY=false` disables it.
- The SPDX fixture is a hand-written 3-package document (format test only).
- `grep -rniE "TODO|FIXME|mock|skip"` over `api/app`, `web/app`, `web/lib`, `web/components`: 0 TODO/FIXME; the only
  "mock" hits are docstrings saying nothing is mocked; test skips are environment guards (no DB, offline, no Ollama).

## Known broken or weak (hours to fix)
| Issue | Impact | Est. |
|---|---|---|
| `notify.send_incident_alert` tries the DB for settings; without a DB each call waits for the 5 s connect timeout (tests took 75 s) | slow tests, slow alert path if DB down | 0.5 h |
| Feed sync rematches all ~60k components every run with 87 SKUs (≈1 min, competes with requests) | slower pages during sync; set `SYNC_INTERVAL_MINUTES=120` for demos | 3 h (incremental matching by SBOM sha) |
| Browser click-through of review UI only done by owner, no automated e2e | regression risk | 4 h (Playwright smoke) |
| German LLM output register; one observed severity hallucination in a TEXT field | reviewer must read carefully | roadmap (post-check) |
| Web container runs `next dev`; no production build image | slower first loads | 1 h |
| Single reviewer role, `X-Actor` header, no auth | fine for demo, blocker for SaaS | Phase 2 |
| Hardcoded CRA timeline (24h/72h/14d) in `services/incidents.py` | blocker for multi-jurisdiction | Phase 1 |
| Report schemas fixed in `schemas/reports.py` | blocker for per-pack fields | Phase 1 |

## Fresh-clone verification (run on the Docker laptop; paste output into this file)
```
git clone https://github.com/AmatyaJoshi/Frist24.git frist24-verify && cd frist24-verify
cp .env.example .env
docker compose up -d --build
docker compose logs -f ollama-pull          # until "done: llama3.1:8b"
docker compose exec api python -m app.cli demo
docker compose exec api pytest -q            # expect 22 passed (live tests need network + model)
docker compose exec web npm test
sh scripts/smoke.sh                          # SMOKE OK
```
Then in the UI: draft EN with Local AI on `HMI-4100 × CVE-2020-11023`, edit, approve, verify chain, download package.

## Name check for "Klaxon" (2026-09-21, live lookups)
| Namespace | Result |
|---|---|
| GitHub user `klaxon` | taken |
| GitHub org `klaxon` | free |
| GitHub repos named klaxon | 294; notable: `cbeust/klaxon` (Kotlin JSON library, 1.8k★), `themarshallproject/klaxon` (website change monitor, 682★) |
| PyPI `klaxon` | taken · `klaxon-app` free |
| npm `klaxon` | taken · `klaxon-app` free |
| Domains (RDAP) | `klaxon.io`, `klaxon.eu`, `klaxon.security`: no record (appear available) · `klaxon.dev`, `.app`, `.com`, `.ai`, `getklaxon.com`, `klaxonhq.com`: lookup inconclusive. Moot under COST.md: no purchased domains; platform subdomain or DuckDNS. |

Recommendation: "Klaxon" collides with an established Kotlin library and a well-known journalism tool; the bare
package names are gone. Usable as a product brand with a qualifier (`klaxon-app`, `klaxonhq`), not as a bare
package or GitHub user. Decision is the owner's.
