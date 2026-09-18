# Paste everything below this line into Claude Code, from the repo root

---

We are building **Frist24** for the MunichTech EXPO hackathon. Hard deadline for the Devpost
submission: Saturday 20 September 2026, 17:00 CEST. Today is Friday 18 September.

The repo already contains the full brief. Before you write a single line of code, read these
files completely and in this order:

1. `CLAUDE.md`
2. `docs/CONTEXT.md`
3. `docs/SPEC.md`
4. `docs/DATA_SOURCES.md`
5. `docs/REPORT_SCHEMA.md`
6. `docs/BUILD_PLAN.md`
7. `api/prompts/early_warning.md` (a starter prompt; you'll write `notification.md` in the same style)

Then, before coding, reply with:
- a 5-line summary of what we are building and the one rule you consider most important,
- any contradiction or ambiguity you found between the docs (there may be none),
- the directory tree you intend to create for step 1.

Then execute `docs/BUILD_PLAN.md` step by step, in order. After each step:
- run whatever verifies the step's "Done when" column,
- commit with a conventional commit message,
- append any non-obvious choice to `DECISIONS.md` and any cut scope to `TODO.md`,
- tell me in two lines what you did and what's next, then continue without waiting unless blocked.

Constraints you must not violate (also in CLAUDE.md): deterministic KEV rule opens incidents,
LLM only drafts and confirms; every AI output is `pending_review`; real KEV/EPSS/OSV data only;
`docker compose up` from a clean clone must work; audit log is append-only and hash-chained;
no ENISA submission integration.

Step 2 (fixtures) is the one step where you MUST stop and ask me: present three candidate
component+CVE pairs that you have verified live against KEV and OSV, with the package ecosystem
and the public SBOM source you'd use, and let me pick.

Ask me only for blocking decisions. Prefer the simplest thing that works. Begin with step 1.
