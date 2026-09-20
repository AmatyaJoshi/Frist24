from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import OUTBOUND_ALLOWLIST, get_settings
from app.db import get_db
from app.routers.products import actor_from_header
from app.services import app_settings, llm

router = APIRouter(prefix="/settings", tags=["settings"])

EU_MEMBER_STATES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia", "CY": "Cyprus", "CZ": "Czechia", "DK": "Denmark",
    "EE": "Estonia", "FI": "Finland", "FR": "France", "DE": "Germany", "GR": "Greece", "HU": "Hungary", "IE": "Ireland",
    "IT": "Italy", "LV": "Latvia", "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta", "NL": "Netherlands", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "SK": "Slovakia", "SI": "Slovenia", "ES": "Spain", "SE": "Sweden",
}


def _payload(db: Session) -> dict:
    s = get_settings()
    editable = app_settings.load(db)
    try:
        models = llm.available_models()
        ready = True
        try:
            llm.pick_model()
        except llm.LlmUnavailable:
            ready = False
    except llm.LlmUnavailable:
        models, ready = [], False
    return {
        "version": "0.3.0",
        "editable": editable.model_dump(),
        "eu_member_states": EU_MEMBER_STATES,
        "manufacturer": {"name": editable.manufacturer_name, "contact": editable.manufacturer_contact},
        "llm": {"url": s.ollama_url, "model": s.ollama_model, "fallback_model": s.ollama_fallback_model, "ready": ready, "available_models": models},
        "feeds": {"kev_url": s.kev_url, "epss_csv_url": s.epss_csv_url, "osv_api_url": s.osv_api_url},
        "sync": {"interval_minutes": s.sync_interval_minutes, "enabled": s.sync_enabled},
        "outbound_allowlist": list(OUTBOUND_ALLOWLIST),
        "notifications": {
            "webhook_configured": bool(editable.notify_webhook_url),
            "webhook_host": urlparse(editable.notify_webhook_url).hostname if editable.notify_webhook_url else None,
        },
    }


@router.get("", summary="Running configuration: editable (database) + environment-only values")
def read_settings(db: Session = Depends(get_db)) -> dict:
    return _payload(db)


@router.put("", summary="Update editable settings (audited)")
def update_settings(body: app_settings.SettingsUpdate, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)) -> dict:
    app_settings.update(db, body, actor)
    db.commit()
    return _payload(db)
