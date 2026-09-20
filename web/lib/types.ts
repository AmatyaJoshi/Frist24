// Mirrors api/app/schemas/*.py. Keep in sync by hand (time-boxed hackathon; no codegen).

export type Health = {
  status: string;
  service: string;
  version: string;
  db: string;
  ollama: { status: string; models: string[]; target: string };
};

export type Sbom = {
  id: string;
  format: string;
  spec_version: string | null;
  filename: string | null;
  sha256: string;
  component_count: number;
  uploaded_at: string;
};

export type Product = {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  lifecycle_status: "active" | "discontinued";
  placed_on_market_at: string | null;
  created_at: string;
  sboms: Sbom[];
  component_count: number;
  open_incidents: number;
};

export type Component = {
  id: string;
  name: string;
  version: string | null;
  purl: string | null;
  ecosystem: string | null;
  cpe: string | null;
  supplier: string | null;
};

export type IncidentStatus =
  | "open"
  | "early_warning_approved"
  | "notification_approved"
  | "final_approved"
  | "closed";

export type Stage = "early_warning" | "notification" | "final_report";
export type Language = "en" | "de";

export type IncidentListItem = {
  id: string;
  product_id: string;
  sku: string;
  product_name: string;
  cve_id: string;
  vulnerability_name: string | null;
  kev_date_added: string;
  known_ransomware_campaign_use: string | null;
  epss: number | null;
  cvss_score: number | null;
  status: IncidentStatus;
  aware_at: string;
  deadline_early_warning: string;
  deadline_notification: string;
  deadline_final_report: string;
  final_report_anchor: "provisional" | "fix_available";
  next_deadline: string | null;
  next_stage: Stage | null;
  component_count: number;
  reports_pending: number;
  reports_approved: number;
};

export type Kev = {
  cve_id: string;
  vendor_project: string | null;
  product: string | null;
  vulnerability_name: string | null;
  date_added: string;
  short_description: string | null;
  required_action: string | null;
  due_date: string | null;
  known_ransomware_campaign_use: string | null;
  notes: string | null;
  cwes: string[] | null;
};

export type MatchedComponent = {
  match_id: string;
  component_id: string;
  name: string;
  version: string | null;
  purl: string | null;
  ecosystem: string | null;
  match_type: "purl_exact" | "fuzzy";
  confidence: number;
  affected_range: string | null;
  status: string;
  osv_id: string;
};

export type Vuln = {
  id: string;
  cve_id: string | null;
  summary: string | null;
  details: string | null;
  cvss_score: number | null;
  cvss_vector: string | null;
  aliases: string[] | null;
  published: string | null;
  modified: string | null;
};

export type AuditEvent = {
  id: number;
  ts: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  payload: Record<string, unknown>;
  hash: string;
  prev_hash: string;
};

export type ReportStatus = "pending_review" | "approved" | "rejected";

export type Report = {
  id: string;
  incident_id: string;
  stage: Stage;
  language: Language;
  version: number;
  status: ReportStatus;
  content: Record<string, unknown>;
  fact_fields: string[];
  source: string;
  model: string | null;
  prompt_version: string | null;
  generated_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string | null;
};

export type IncidentDetail = IncidentListItem & {
  product_description: string | null;
  lifecycle_status: string;
  kev: Kev;
  vulnerabilities: Vuln[];
  components: MatchedComponent[];
  reports: Report[];
  timeline: AuditEvent[];
  facts: Record<string, unknown>;
};

export type FeedSync = {
  id: number;
  feed: string;
  started_at: string;
  finished_at: string | null;
  status: "running" | "ok" | "error";
  items: number | null;
  message: string | null;
};

// Report field schemas (docs/REPORT_SCHEMA.md) — order used for rendering.
export const EARLY_WARNING_FIELDS = [
  "report_type",
  "manufacturer_name",
  "manufacturer_contact",
  "product_name",
  "product_identifier",
  "product_versions_affected",
  "vulnerability_id",
  "actively_exploited",
  "exploitation_evidence",
  "member_states_affected",
  "aware_at",
  "initial_assessment",
  "potentially_malicious",
  "corrective_measures_status",
  "request_confidentiality",
] as const;

export const NOTIFICATION_FIELDS = [
  "report_type",
  "reference_to_early_warning",
  "manufacturer_name",
  "manufacturer_contact",
  "product_name",
  "product_identifier",
  "product_versions_affected",
  "vulnerability_id",
  "actively_exploited",
  "exploitation_evidence",
  "aware_at",
  "potentially_malicious",
  "request_confidentiality",
  "vulnerability_description",
  "affected_component",
  "cvss_score",
  "cvss_vector",
  "epss_score",
  "severity_assessment",
  "attack_prerequisites",
  "corrective_measures_taken",
  "mitigations_for_users",
  "security_update_availability",
  "user_notification_plan",
  "affected_user_estimate",
  "cross_border_impact",
] as const;

export const FINAL_REPORT_FIELDS = [
  ...NOTIFICATION_FIELDS,
  "root_cause",
  "fix_description",
  "fix_release_identifier",
  "verification_performed",
  "lessons_learned",
  "residual_risk",
] as const;

export const STAGE_FIELDS: Record<Stage, readonly string[]> = {
  early_warning: EARLY_WARNING_FIELDS,
  notification: NOTIFICATION_FIELDS,
  final_report: FINAL_REPORT_FIELDS,
};

export const STAGE_LABEL: Record<Stage, string> = {
  early_warning: "Early warning (24h)",
  notification: "Vulnerability notification (72h)",
  final_report: "Final report (14d)",
};

export type Settings = {
  version: string;
  manufacturer: { name: string; contact: string };
  llm: { url: string; model: string; fallback_model: string; ready: boolean; available_models: string[] };
  feeds: { kev_url: string; epss_csv_url: string; osv_api_url: string };
  sync: { interval_minutes: number; enabled: boolean };
  outbound_allowlist: string[];
  notifications: { webhook_configured: boolean; webhook_host: string | null };
};
