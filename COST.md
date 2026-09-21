# COST.md — zero-cost policy ledger

Rule: this project costs the team **$0**. Every external service, hosted dependency, cloud resource, model API,
domain or analytics tool is listed here with its free-tier limit, the in-code guard, and what happens when the
limit is hit. Anything not listed is not allowed. Never add a payment card. Stripe in test mode only.

## In use today (2026-09-21)
| Service | Purpose | Free-tier limit | In-code guard | When the limit is hit |
|---|---|---|---|---|
| CISA KEV JSON (`www.cisa.gov`) | exploited-vulnerability oracle | free, unauthenticated, ~2 MB per pull | pulled once per `SYNC_INTERVAL_MINUTES` (default 15; 120 for demos); egress allow-list | n/a (static file) |
| FIRST EPSS CSV (`epss.cyentia.com`) | triage scores | free, ~2.6 MB gz daily file | once per sync; rows filtered to KEV ∪ matched CVEs | n/a |
| OSV.dev API (`api.osv.dev`) | PURL → vulnerability matching | free, unauthenticated; batch 500/queries; no published hard quota | querybatch in chunks of 500; vulnerability details cached in DB and refetched only when `modified` changes; 12 concurrent | HTTP 429 → step recorded as `error` in `feed_syncs`, next scheduled sync retries; no paid path exists |
| NVD API (`services.nvd.nist.gov`) | reserved, **not called** | 5 req / 30 s unauthenticated | on allow-list only | n/a |
| Ollama (self-hosted, `llama3.1:8b`, fallback `mistral`) | local drafting | free (own CPU/GPU) | 300 s timeout, one retry, template fallback | template draft, `source=template`, UI says so |
| GitHub raw (`raw.githubusercontent.com`) | fixture SBOMs, fetched once at build time by scripts | free | fixtures are committed; runtime never calls GitHub | n/a |
| Docker Hub images (postgres, ollama, python, node) | compose base images | free anonymous pulls (rate-limited 100 / 6 h per IP) | pulled once; cached locally | wait or log in with a free Docker account |
| GitHub (public repo) | source hosting | free | — | — |

Phase 0 cost check: GitHub API, PyPI, npm and RDAP lookups for the name check (≈15 requests, free). Credits used: 0.

## Planned for Phase 1–3 (each must be confirmed free before use)
| Service | Purpose | Free tier | Planned guard |
|---|---|---|---|
| ENISA EUVD API | second exploited-source | free, unauthenticated (verify quota at integration) | cache, one pull per sync, allow-list |
| Oracle Cloud Always Free ARM VM | hosted demo (Docker Compose) | 4 OCPU / 24 GB / 200 GB block, always free | retention/GC job keeps Postgres small; no paid shapes |
| Vercel Hobby | hosted web frontend | free for non-commercial hobby use; check terms for demo use | static + SSR within limits; fall back to serving web from the VM via Caddy |
| DuckDNS + Caddy (Let's Encrypt) | hostname + TLS | free | — |
| Umami (self-hosted on VM) | analytics | free | — |
| Stripe | monetization blueprint | **test mode only** | no live keys in repo or env; guard refuses `sk_live_*` |
| GitHub Actions | CI | free minutes on public repos | jobs < 10 min |
| Gemini free tier / Groq free tier | optional cloud drafting fallback for hosted mode (org opt-in only) | free tiers without card | `BUDGET_LLM_CALLS_PER_RUN`, `BUDGET_LLM_TOKENS_PER_DAY`; on cap → `cost_mode=degraded`, template path, UI badge |

## Guards to implement (Phase 1)
- `BUDGET_LLM_CALLS_PER_RUN` (default 4), `BUDGET_LLM_TOKENS_PER_DAY` (default 200k), `BUDGET_OSV_QUERIES_PER_SYNC`
  (default 10,000 PURLs) as env vars with free-tier-safe defaults.
- `/health` gains `cost_mode: normal | degraded`; the UI shows a badge when degraded.
- Tests assert that reaching a cap switches to the template path and never raises or retries a paid call.
- Startup log already lists every outbound host; a request to a host off the allow-list raises (fail closed).

## Not allowed
Fly.io, Railway, Hetzner, DigitalOcean, purchased domains, Plausible, any model API that requires a card, Bedrock
without confirmed credits.
