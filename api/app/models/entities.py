"""Data model (derived from CLAUDE.md, REPORT_SCHEMA.md, CONTEXT.md; docs/SPEC.md was not delivered).

Key rules encoded here:
- An Incident is one product x one KEV-listed CVE. `aware_at` starts every CRA clock.
- Reports are versioned drafts; status defaults to `pending_review`.
- audit_log is append-only (DB trigger, see alembic) and hash-chained (app.services.audit).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)  # active | discontinued
    placed_on_market_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sboms: Mapped[list[Sbom]] = relationship(back_populates="product", cascade="all, delete-orphan")
    incidents: Mapped[list[Incident]] = relationship(back_populates="product")


class Sbom(Base):
    __tablename__ = "sboms"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(16), nullable=False)  # cyclonedx | spdx
    spec_version: Mapped[str | None] = mapped_column(String(16))
    filename: Mapped[str | None] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    component_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product: Mapped[Product] = relationship(back_populates="sboms")
    components: Mapped[list[Component]] = relationship(back_populates="sbom", cascade="all, delete-orphan")


class Component(Base):
    __tablename__ = "components"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    sbom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sboms.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100))
    purl: Mapped[str | None] = mapped_column(String(600), index=True)
    ecosystem: Mapped[str | None] = mapped_column(String(32))  # purl type: npm, maven, pypi ...
    cpe: Mapped[str | None] = mapped_column(String(300))
    supplier: Mapped[str | None] = mapped_column(String(300))

    sbom: Mapped[Sbom] = relationship(back_populates="components")
    matches: Mapped[list[Match]] = relationship(back_populates="component", cascade="all, delete-orphan")


class KevEntry(Base):
    """One row per CISA KEV catalog entry. Presence == actively exploited."""

    __tablename__ = "kev_entries"
    cve_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_project: Mapped[str | None] = mapped_column(String(200))
    product: Mapped[str | None] = mapped_column(String(200))
    vulnerability_name: Mapped[str | None] = mapped_column(Text)
    date_added: Mapped[date] = mapped_column(Date, nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    required_action: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    known_ransomware_campaign_use: Mapped[str | None] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)
    cwes: Mapped[list | None] = mapped_column(JSONType)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EpssScore(Base):
    __tablename__ = "epss_scores"
    cve_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    epss: Mapped[float] = mapped_column(Float, nullable=False)
    percentile: Mapped[float | None] = mapped_column(Float)
    score_date: Mapped[date | None] = mapped_column(Date)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Vulnerability(Base):
    """OSV record (GHSA-*, PYSEC-*, CVE-* ...). cve_id is the extracted CVE alias."""

    __tablename__ = "vulnerabilities"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # OSV id
    cve_id: Mapped[str | None] = mapped_column(String(32), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list | None] = mapped_column(JSONType)
    severity: Mapped[list | None] = mapped_column(JSONType)  # OSV severity[] (CVSS vectors)
    cvss_score: Mapped[float | None] = mapped_column(Float)
    cvss_vector: Mapped[str | None] = mapped_column(String(200))
    published: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Match(Base):
    """Component x vulnerability. in_kev is copied from kev_entries at match time and refreshed on sync."""

    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("component_id", "vulnerability_id", name="uq_match_component_vuln"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    component_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), nullable=False, index=True)
    vulnerability_id: Mapped[str] = mapped_column(ForeignKey("vulnerabilities.id"), nullable=False, index=True)
    cve_id: Mapped[str | None] = mapped_column(String(32), index=True)
    match_type: Mapped[str] = mapped_column(String(16), nullable=False, default="purl_exact")  # purl_exact | fuzzy
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    affected_range: Mapped[str | None] = mapped_column(Text)
    in_kev: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    epss: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="auto")  # auto | needs_review | confirmed | rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    component: Mapped[Component] = relationship(back_populates="matches")
    vulnerability: Mapped[Vulnerability] = relationship()


class Incident(Base):
    """One product x one KEV-listed CVE. Opened only by the deterministic KEV rule."""

    __tablename__ = "incidents"
    __table_args__ = (UniqueConstraint("product_id", "cve_id", name="uq_incident_product_cve"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    cve_id: Mapped[str] = mapped_column(ForeignKey("kev_entries.cve_id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    # open | early_warning_approved | notification_approved | final_approved | closed
    aware_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline_early_warning: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # aware_at + 24h
    deadline_notification: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # aware_at + 72h
    deadline_final_report: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # provisional aware_at + 14d
    final_report_anchor: Mapped[str] = mapped_column(String(16), nullable=False, default="provisional")  # provisional | fix_available
    fix_available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship(back_populates="incidents")
    kev: Mapped[KevEntry] = relationship()
    reports: Mapped[list[Report]] = relationship(back_populates="incident", cascade="all, delete-orphan")


class Report(Base):
    """A drafted report. Every LLM output lands here as pending_review."""

    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("incident_id", "stage", "language", "version", name="uq_report_version"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(16), nullable=False)  # early_warning | notification | final_report
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="en")  # en | de
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending_review")  # pending_review | approved | rejected
    content: Mapped[dict] = mapped_column(JSONType, nullable=False)
    fact_fields: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)  # keys the LLM had to copy verbatim
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="llm")  # llm | template | human
    model: Mapped[str | None] = mapped_column(String(64))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(120))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)

    incident: Mapped[Incident] = relationship(back_populates="reports")


class AuditLog(Base):
    """Append-only, hash-chained. hash = sha256(prev_hash || canonical(ts, actor, action, entity_type, entity_id, payload))."""

    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


Index("ix_audit_entity", AuditLog.entity_type, AuditLog.entity_id)


class FeedSync(Base):
    __tablename__ = "feed_syncs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feed: Mapped[str] = mapped_column(String(16), nullable=False)  # kev | epss | osv | match
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")  # running | ok | error
    items: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str | None] = mapped_column(Text)
