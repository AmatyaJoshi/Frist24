# Frist24 — poster content and video script (2026-09-20)

## Poster
**Frist24 — CRA Article 14 reporting, without the panic.**
Local-first compliance software that turns "a CVE just hit CISA KEV and it's in a product we shipped in 2021"
into an approved, filing-ready early warning inside 24 hours.

### The problem
Since 11 Sep 2026, Regulation (EU) 2024/2847 Art. 14 obliges every manufacturer of a product with digital elements
sold in the EU to report actively exploited vulnerabilities to ENISA and the national CSIRT: early warning 24 h,
notification 72 h, final report 14 d after a fix. Legacy products count. Fines up to EUR 15 M / 2.5 % turnover.

### What Frist24 does
1. Ingests SBOMs (CycloneDX, SPDX) per SKU. 2. Pulls CISA KEV, FIRST EPSS, OSV.dev every 15 min.
3. Deterministic rule: component matches a KEV-listed CVE -> incident opens, clock starts. No model involved.
4. Local LLM (Ollama, llama3.1:8b) drafts early warning + 72 h notification in EN and DE; facts from the DB, model
writes only TEXT fields. 5. Named human reviews, edits, approves; facts re-verified at approval.
6. Append-only, hash-chained audit log enforced by the database. 7. Filing package (JSON + PDF, EN + DE); the
human submits on the ENISA platform. 8. Webhook alerts the moment an incident opens.

### Why Europe
Achievable compliance for the Mittelstand. Digital sovereignty by design: unpatched-vulnerability details never
leave your infrastructure. Built the way regulators think: published deterministic trigger, structural human
oversight, attributable approvals, German output for the BSI.

### Real data
KEV 1,713 entries (2026-09-16) · OSV 644 records over 1,786 PURLs · unmodified public CycloneDX SBOMs (Keycloak,
Proton Mail web client, Dropwizard, Proton Bridge, Juice Shop) · 87 SKUs / 5 families / ~200 incidents 2024-2026,
all opened by the real rule. Only manufacturer identity and workflow timestamps are staged (flagged in the audit log).

### Architecture
Next.js 15 -> FastAPI + APScheduler -> Postgres 16 (append-only audit trigger) -> Ollama. One `docker compose up`.
Egress limited to five public hosts + the local model.

### Principles
Deterministic first. LLM second. Human always. Nothing leaves the machine.

### Numbers
24 h / 72 h / 14 d · 1,713 KEV entries · 87 SKUs · ~200 incidents · 0 cloud calls · 100 % of AI output pending review

### Limitations
No ENISA submission (no public API). Schemas are our reading of Art. 14. Exact-PURL matching. Single reviewer role.
KEV is a US catalogue; EUVD is roadmap.

## Video script (~2:45)
[0:00] Hook, Overview with ticking countdown. CRA duty live since 11 Sep; 24 h early warning; "This is Frist24."
[0:20] Products: 87 SKUs, five families, real public SBOMs; three real feeds; nothing mocked.
[0:45] Incidents: one rule (component matches a KEV CVE), jQuery in a discontinued panel added to KEV 2025;
       legacy products count; ~200 incidents since 2024 sorted by deadline.
[1:10] Incident detail: stepper; Draft EN with Local AI; spinner "no data leaves this machine"; green FACTs
       re-stamped and re-verified, amber TEXT editable; switch to DE (BSI); edit, save, approve under a name.
[1:50] Timeline, Audit page Verify Chain, Download Filing Package (JSON + PDF, EN + DE); the human submits.
[2:15] Settings: manufacturer, Member States, reviewer, webhook; audited; paged at 16:00 on a Friday.
[2:35] Close: Deterministic first, model second, human always. One docker compose up. Frist24.
