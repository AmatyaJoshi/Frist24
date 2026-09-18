"""CRA Article 14 report schemas (docs/REPORT_SCHEMA.md). Mirrored in web/lib/types.ts.

FACT fields are filled deterministically from the DB and must be copied verbatim by the LLM.
TEXT fields are written by the LLM (or the template fallback) and reviewed by a human.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = {"en": "under investigation", "de": "wird untersucht"}


class EarlyWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_type: Literal["early_warning"] = "early_warning"
    manufacturer_name: str
    manufacturer_contact: str
    product_name: str
    product_identifier: str
    product_versions_affected: str
    vulnerability_id: str
    actively_exploited: bool
    exploitation_evidence: str
    member_states_affected: str
    aware_at: str
    initial_assessment: str
    potentially_malicious: bool
    corrective_measures_status: str
    request_confidentiality: bool


class Notification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_type: Literal["notification"] = "notification"
    reference_to_early_warning: str | None
    # --- EarlyWarning FACT fields ---
    manufacturer_name: str
    manufacturer_contact: str
    product_name: str
    product_identifier: str
    product_versions_affected: str
    vulnerability_id: str
    actively_exploited: bool
    exploitation_evidence: str
    aware_at: str
    potentially_malicious: bool
    request_confidentiality: bool
    # --- Notification ---
    vulnerability_description: str
    affected_component: str
    cvss_score: float | None
    cvss_vector: str | None
    epss_score: str
    severity_assessment: str
    attack_prerequisites: str
    corrective_measures_taken: str
    mitigations_for_users: str
    security_update_availability: str
    user_notification_plan: str
    affected_user_estimate: str
    cross_border_impact: str


class FinalReport(Notification):
    model_config = ConfigDict(extra="forbid")
    report_type: Literal["final_report"] = "final_report"  # type: ignore[assignment]
    root_cause: str
    fix_description: str
    fix_release_identifier: str
    verification_performed: str
    lessons_learned: str
    residual_risk: str


STAGE_MODELS: dict[str, type[BaseModel]] = {
    "early_warning": EarlyWarning,
    "notification": Notification,
    "final_report": FinalReport,
}

# Which keys are FACT (deterministic) per stage. Everything else is TEXT.
FACT_FIELDS: dict[str, list[str]] = {
    "early_warning": [
        "report_type",
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
    ],
    "notification": [
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
        "affected_component",
        "cvss_score",
        "cvss_vector",
        "epss_score",
    ],
}
FACT_FIELDS["final_report"] = FACT_FIELDS["notification"] + ["fix_release_identifier"]


def text_fields(stage: str) -> list[str]:
    model = STAGE_MODELS[stage]
    return [k for k in model.model_fields if k not in FACT_FIELDS[stage]]


# ----------------------------------------------------------------------------- API envelopes
class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    incident_id: str
    stage: str
    language: str
    version: int
    status: str
    content: dict
    fact_fields: list[str]
    source: str
    model: str | None
    prompt_version: str | None
    generated_at: str
    reviewed_by: str | None
    reviewed_at: str | None
    review_note: str | None


class ReportEdit(BaseModel):
    """Reviewer edits TEXT fields. FACT fields are rejected with 422."""

    content: dict = Field(description="full or partial content; only TEXT keys may change")
    note: str | None = None


class ReviewDecision(BaseModel):
    note: str | None = None
