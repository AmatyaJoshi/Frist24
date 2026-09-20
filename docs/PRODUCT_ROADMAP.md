# From prototype to product — what Frist24 needs to be used in industry

Status on 2026-09-20: the vertical slice (SBOM → KEV match → incident → local draft → human approval →
audit → filing package) works end to end on real data. This document lists, honestly, what separates
that from something a manufacturer would run in production, in priority order.

## 1. Identity, access and tenancy
- **SSO (OIDC/SAML)** against the manufacturer's IdP; today a header names the actor.
- **Roles**: viewer, analyst (drafts, edits), approver (approves), admin (settings). CRA reports are legal
  statements; the approver role should be restricted and four-eyes approval configurable.
- **Multi-tenancy** for consultancies and notified bodies serving many manufacturers: tenant scoping on every
  table, per-tenant manufacturer identity and reviewer pool.

## 2. Getting SBOMs in, continuously
- Connectors for **build pipelines** (GitHub/GitLab release assets, Jenkins, Azure DevOps), **Dependency-Track**
  and artifact repositories, so SBOMs arrive per firmware release instead of by upload.
- **Product-version model**: today a product has SBOMs; production needs product → version/firmware → SBOM,
  with "in support" and "placed on market" dates per version so `product_versions_affected` can be exact.
- **VEX** ingest and export (CycloneDX VEX / OpenVEX): let engineering mark "not affected, code path not
  reachable" and carry that into the report and out to customers.

## 3. Matching coverage
- **Fuzzy path for components without PURL** (C/C++ firmware, vendored code): CPE and name+version
  matching with `rapidfuzz`, LLM-assisted *confirmation* only, always landing in `needs_review`.
- **EUVD** (ENISA EU Vulnerability Database) as a second exploitation source next to CISA KEV; both flags visible,
  either opens an incident (configurable).
- **NVD / vendor advisories** for richer descriptions and CVSS where OSV is thin.

## 4. Alerting and workflow
- Webhook alert exists (`NOTIFY_WEBHOOK_URL`); add **e-mail**, **Microsoft Teams/Slack** formatting, **PagerDuty**
  severity mapping, and **escalation** when a deadline is within N hours and nothing is approved.
- **Ticketing**: create/update Jira or ServiceNow tickets per incident; sync approval state back.
- **Assignment and comments** on incidents; SLA dashboard per product line.

## 5. Reporting quality
- **Official ENISA form mapping** as soon as the single reporting platform publishes field definitions; today
  the schema is our reading of Art. 14. Keep the FACT/TEXT split.
- Dedicated **final report** prompt and **severe incident** (Art. 14(3)) flow.
- **Model options**: larger local models on GPU hosts, German-tuned models, or an EN→DE pass; evaluation set of
  approved reports to regression-test prompt changes (prompt_version is already recorded).
- **Guardrail post-checks**: flag TEXT fields that introduce severity terms absent from the CVE text (observed
  once: an XSS described as RCE).

## 6. Evidence and compliance
- **Signed filing packages** (Sigstore or manufacturer PKI) and **audit log anchoring** (periodic hash publication
  or WORM storage) so the chain is verifiable by an auditor without trusting the database host.
- **Retention policies** and legal-hold; export of the full audit trail per incident for authority requests.
- **Regulatory clock rules**: business calendar options, time-zone of the competent CSIRT, and re-anchoring of
  the 14-day final-report clock on fix availability (implemented) with reminders.

## 7. Operations
- Production web build, health/metrics endpoints (Prometheus), structured logs, backup/restore for Postgres and
  the model volume, Helm chart or Kubernetes manifests, air-gapped install with pre-pulled feeds and model.
- Feed **staleness alarms** (KEV not refreshed in X hours) and feed **integrity checks** (schema drift).

## 8. Commercial packaging
- Single-tenant on-prem appliance (compose/Helm) for manufacturers; multi-tenant SaaS for consultancies where
  the LLM still runs in the customer's own tenancy; pricing per SKU under monitoring.

Everything above builds on what exists; nothing requires changing the core rule: deterministic first, LLM second,
human always.
