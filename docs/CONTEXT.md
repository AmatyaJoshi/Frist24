# CONTEXT.md — Why Frist24 exists and what "winning" means

## The regulation (facts we build on)
- **Regulation (EU) 2024/2847 — Cyber Resilience Act (CRA).** Entered into force 10 Dec 2024.
- **Article 14 — Reporting obligations of manufacturers.** Applies from **11 September 2026**.
  Manufacturers must report *actively exploited vulnerabilities* and *severe incidents*
  affecting their products with digital elements to ENISA and their national CSIRT
  (Germany: BSI) via the single reporting platform (Article 16).
- **Deadlines, measured from the moment the manufacturer becomes aware:**
  - **24 hours** — early warning (minimal: that exploitation is happening, member states affected)
  - **72 hours** — vulnerability notification (nature, severity, mitigations, user guidance)
  - **14 days** — final report for a vulnerability (once a fix/workaround is available)
  - **1 month** — final report for a severe incident
- Applies to **legacy products already on the market**, not just new ones.
- Applies to any manufacturer selling into the EU, including non-EU and one-person companies.
- Full CRA obligations (secure-by-design, SBOM, CE marking) apply from **11 Dec 2027**.
  Fines up to **€15M or 2.5% of worldwide turnover**.
- The European Commission published practical CRA guidance on 27 Jul 2026.
- SBOMs are not legally mandatory until Dec 2027, but you cannot meet the 24h duty
  without knowing your components — so in practice SBOM + monitoring is required now.

## The problem, in the user's words
"A CVE lands on CISA KEV at 16:00 Friday. It's in a library used in a controller we
shipped in 2021 and stopped selling in 2023. We have 40 SKUs. Who is affected? By
16:00 Saturday I owe ENISA an early warning. Today that's a spreadsheet and a panic."

## Target user
- Primary: Head of Product Security / Compliance Officer at a European manufacturer of
  connected products (machine builders, IoT, medical devices, embedded software).
  Typical: German Mittelstand, 200–2000 employees, 10–100 SKUs, no dedicated PSIRT.
- Secondary: consultancies and notified bodies serving many such manufacturers.

## Why local-first (design choice, not legal requirement)
Details of an unpatched, actively exploited vulnerability in your own product are
among the most sensitive data a manufacturer holds. Sending them to a third-party
cloud LLM is a security and export-control objection any CISO will raise. Frist24
runs the LLM on the manufacturer's own infrastructure. This also fits the hackathon's
"digital sovereignty" theme. Feed downloads (KEV, EPSS, OSV) are one-way pulls of
public data — that is fine.

## The hackathon
- **MunichTech EXPO Hackathon**, theme "Build What Europe Needs." Judging criteria:
  1. Problem Relevance & Impact
  2. Technical Excellence & Feasibility
  3. Innovation & Originality
  4. Practical Applicability & Scalability
  5. Presentation & Communication
- Required on Devpost: working prototype, description (problem, solution, target users,
  *why it matters for Europe*), architecture + stack + models/datasets, repo + live link,
  2–3 min demo video. Optional but encouraged: deployment, ethical/regulatory, next steps.
- Awards we target: Grand Challenge, Best Applied AI, Best Industry & Enterprise Use Case.

## Competing submissions (what we must beat)
- **AgentCrashLab** — strongest engineering (React/TS, Express, Postgres, BullMQ, Gemini
  gated by deterministic rules). Weakness: no European angle. **We must match its
  engineering discipline** — typed API, migrations, deterministic gating of the LLM.
- **UrbanGuard AI** — best European story (Munich, EU AI Act, local Ollama). Weakness:
  *simulated* data, Streamlit UI. **We must use real data and a real frontend.**
- Others are not contenders.

## What the demo must show (drives every scope decision)
1. Product inventory with two SKUs, SBOMs uploaded (real CycloneDX from public projects).
2. `make demo` → feed sync → a **real** KEV CVE matches a component → incident opens →
   countdown starts live on screen (23:59:xx).
3. "Draft early warning" → local LLM (spinner: "drafting locally — no data leaves this
   machine") → structured draft appears in EN and DE.
4. Human edits one field, clicks Approve → audit log shows the hash-chained entry.
5. "Draft 72h notification" → same flow. Export filing package (JSON + PDF).
6. Audit page: aware_at, who approved what, when, with hash chain visible.

## What we explicitly do NOT build (say so in README "Limitations")
- Submission to the ENISA platform (no public API). We export a filing-ready package.
- Severe-incident (non-vulnerability) flow beyond the data model.
- Multi-tenancy, SSO, RBAC beyond a single "reviewer" role.
- Firmware scanning / SBOM generation. We consume SBOMs.
