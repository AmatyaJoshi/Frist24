"""Operator-editable settings, stored in app_settings and layered over environment defaults.

Editable here (take effect immediately): manufacturer identity, member states, default language,
default reviewer name, webhook URL, public web URL.
Environment-only (need a restart): database, model, feed URLs, sync interval.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import session_factory
from app.models import AppSetting
from app.services import audit

EDITABLE_KEYS = ("manufacturer_name", "manufacturer_contact", "member_states", "default_language", "default_reviewer", "notify_webhook_url", "public_web_url")


class EditableSettings(BaseModel):
    manufacturer_name: str = Field(min_length=1, max_length=200)
    manufacturer_contact: str = Field(min_length=3, max_length=200)
    member_states: list[str] = Field(default_factory=list, description="ISO 3166-1 alpha-2 codes of EU Member States where products are placed on the market")
    default_language: str = Field(default="en", pattern="^(en|de)$")
    default_reviewer: str = Field(default="reviewer", max_length=120)
    notify_webhook_url: str | None = None
    public_web_url: str = "http://localhost:3000"


class SettingsUpdate(BaseModel):
    manufacturer_name: str | None = Field(default=None, min_length=1, max_length=200)
    manufacturer_contact: str | None = Field(default=None, min_length=3, max_length=200)
    member_states: list[str] | None = None
    default_language: str | None = Field(default=None, pattern="^(en|de)$")
    default_reviewer: str | None = Field(default=None, max_length=120)
    notify_webhook_url: str | None = None
    public_web_url: str | None = None


def _env_defaults() -> dict[str, Any]:
    s = get_settings()
    return {
        "manufacturer_name": s.frist24_manufacturer_name,
        "manufacturer_contact": s.frist24_manufacturer_contact,
        "member_states": [],
        "default_language": "en",
        "default_reviewer": "reviewer",
        "notify_webhook_url": s.notify_webhook_url,
        "public_web_url": s.public_web_url,
    }


def load(db: Session) -> EditableSettings:
    merged = _env_defaults()
    for row in db.execute(select(AppSetting)).scalars():
        if row.key in merged:
            merged[row.key] = row.value
    return EditableSettings.model_validate(merged)


def load_standalone() -> EditableSettings:
    with session_factory()() as db:
        return load(db)


def update(db: Session, changes: SettingsUpdate, actor: str) -> EditableSettings:
    before = load(db).model_dump()
    now = datetime.now(UTC)
    diff: dict[str, dict] = {}
    for key, val in changes.model_dump(exclude_unset=True).items():
        if key not in EDITABLE_KEYS or before.get(key) == val:
            continue
        if key == "member_states" and val is not None:
            val = sorted({c.strip().upper() for c in val if c and c.strip()})
        row = db.get(AppSetting, key)
        if row is None:
            db.add(AppSetting(key=key, value=val, updated_at=now, updated_by=actor))
        else:
            row.value, row.updated_at, row.updated_by = val, now, actor
        diff[key] = {"before": before.get(key), "after": val}
    db.flush()
    after = load(db)
    if diff:
        audit.append(db, actor, "settings.updated", "settings", None, {"changed": diff})
    return after
