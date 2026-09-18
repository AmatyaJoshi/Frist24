# REPORT_SCHEMA.md — What each CRA Article 14 report must contain

These schemas are our working interpretation of Article 14(2)–(4) CRA and the Article 16
single reporting platform. They are **not** the official ENISA form (the platform's exact
form fields are not publicly specified as a machine schema). State this in the README.
Implement each as a Pydantic model in `api/app/schemas/reports.py` and mirror it as a
TypeScript type in `web/lib/types.ts`.

Each field is tagged **FACT** (filled deterministically from DB; LLM must copy verbatim)
or **TEXT** (LLM writes it; human reviews). The UI colours them green / amber.

## Stage 1 — Early warning (due ≤ 24h after aware_at)
Purpose: minimal notification that an actively exploited vulnerability affects a product.
```
EarlyWarning
  report_type            FACT  "early_warning"
  manufacturer_name      FACT  from settings (env FRIST24_MANUFACTURER_NAME)
  manufacturer_contact   FACT  from settings
  product_name           FACT
  product_identifier     FACT  sku
  product_versions_affected  FACT  from matches.affected_range if known, else "under investigation"
  vulnerability_id       FACT  CVE id
  actively_exploited     FACT  true (KEV date_added included)
  exploitation_evidence  FACT  "Listed in CISA KEV on {date}; {kev.shortDescription}"
  member_states_affected TEXT  default "EU-wide; product is placed on the market in the following Member States: [to be confirmed by reviewer]"
  aware_at               FACT  ISO timestamp
  initial_assessment     TEXT  2–3 sentences: what the component does in the product, plausible impact, what is NOT yet known
  potentially_malicious  FACT  true (definition: actively exploited)
  corrective_measures_status TEXT  one sentence, honest ("investigation started", "patch available upstream since X")
  request_confidentiality  FACT  true (Art. 14 allows manufacturers to request)
```

## Stage 2 — Vulnerability notification (due ≤ 72h after aware_at)
Purpose: fuller information including nature, severity, mitigations, user guidance.
```
Notification
  report_type            FACT  "notification"
  reference_to_early_warning  FACT  early_warning report id + timestamp (if approved)
  ...all EarlyWarning FACT fields...
  vulnerability_description   TEXT  plain-language, 3–5 sentences, cite CVE description
  affected_component     FACT  name, version, purl
  cvss_score, cvss_vector  FACT  if available, else null
  epss_score             FACT  with one-line explanation of what EPSS is
  severity_assessment    TEXT  manufacturer's own assessment for THIS product context, 2–4 sentences
  attack_prerequisites   TEXT  what an attacker needs (network access, auth, physical) — from CVE text
  corrective_measures_taken  TEXT  list
  mitigations_for_users  TEXT  numbered, actionable, avoid vague "update when possible"
  security_update_availability  TEXT  available / planned date / not planned + justification
  user_notification_plan TEXT  how and when users are told
  affected_user_estimate TEXT  rough order of magnitude or "under investigation"
  cross_border_impact    TEXT  yes/no + reasoning
```

## Stage 3 — Final report (due ≤ 14 days after fix/workaround available)
Not required for the demo. Implement the schema and endpoint only if time permits.
```
FinalReport
  ...Notification fields...
  root_cause             TEXT
  fix_description        TEXT
  fix_release_identifier FACT  free text from reviewer
  verification_performed TEXT
  lessons_learned        TEXT
  residual_risk          TEXT
```

## Language
Every stage is generated in **EN** and **DE** on request. Prompts must instruct the model to
keep FACT fields byte-identical across languages and to use formal register in German
("Sie", Behördendeutsch-clean, no marketing tone). Terminology anchors for DE:
- actively exploited vulnerability → aktiv ausgenutzte Schwachstelle
- early warning → Frühwarnung
- notification → Meldung
- manufacturer → Hersteller
- product with digital elements → Produkt mit digitalen Elementen
- corrective measures → Abhilfemaßnahmen
- competent CSIRT → zuständiges CSIRT (Deutschland: BSI)

## Generation contract (put this in every prompt)
- Output **only** a JSON object matching the schema. No prose, no code fences.
- Copy FACT fields verbatim from the provided facts. Never invent versions, dates, CVSS scores or affected counts.
- If something is unknown, write "under investigation" (DE: "wird untersucht"), never a guess.
- Do not claim exploitation details beyond the KEV entry and CVE description.
- Write for a regulator, not a customer: precise, neutral, no reassurance language.
