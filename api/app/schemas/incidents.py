from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.reports import ReportOut


class IncidentListItem(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    product_name: str
    cve_id: str
    vulnerability_name: str | None
    kev_date_added: date
    known_ransomware_campaign_use: str | None
    epss: float | None
    cvss_score: float | None
    status: str
    aware_at: datetime
    deadline_early_warning: datetime
    deadline_notification: datetime
    deadline_final_report: datetime
    final_report_anchor: str
    next_deadline: datetime | None
    next_stage: str | None
    component_count: int
    reports_pending: int
    reports_approved: int


class KevOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cve_id: str
    vendor_project: str | None
    product: str | None
    vulnerability_name: str | None
    date_added: date
    short_description: str | None
    required_action: str | None
    due_date: date | None
    known_ransomware_campaign_use: str | None
    notes: str | None
    cwes: list | None


class MatchedComponent(BaseModel):
    match_id: uuid.UUID
    component_id: uuid.UUID
    name: str
    version: str | None
    purl: str | None
    ecosystem: str | None
    match_type: str
    confidence: float
    affected_range: str | None
    status: str
    osv_id: str


class VulnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    cve_id: str | None
    summary: str | None
    details: str | None
    cvss_score: float | None
    cvss_vector: str | None
    aliases: list | None
    published: datetime | None
    modified: datetime | None


class TimelineEvent(BaseModel):
    id: int
    ts: datetime
    actor: str
    action: str
    entity_type: str
    entity_id: str | None
    payload: dict
    hash: str
    prev_hash: str


class IncidentDetail(IncidentListItem):
    product_description: str | None
    lifecycle_status: str
    kev: KevOut
    vulnerabilities: list[VulnOut]
    components: list[MatchedComponent]
    reports: list[ReportOut]
    timeline: list[TimelineEvent]
    facts: dict


class FixAvailable(BaseModel):
    fix_available_at: datetime | None = None
