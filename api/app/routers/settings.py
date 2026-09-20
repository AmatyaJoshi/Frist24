from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter

from app.config import OUTBOUND_ALLOWLIST, get_settings
from app.services import llm

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", summary="Running configuration (read-only; values come from environment variables)")
def read_settings() -> dict:
    s = get_settings()
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
        "version": "0.2.0",
        "manufacturer": {"name": s.frist24_manufacturer_name, "contact": s.frist24_manufacturer_contact},
        "llm": {"url": s.ollama_url, "model": s.ollama_model, "fallback_model": s.ollama_fallback_model, "ready": ready, "available_models": models},
        "feeds": {"kev_url": s.kev_url, "epss_csv_url": s.epss_csv_url, "osv_api_url": s.osv_api_url},
        "sync": {"interval_minutes": s.sync_interval_minutes, "enabled": s.sync_enabled},
        "outbound_allowlist": list(OUTBOUND_ALLOWLIST),
        "notifications": {
            "webhook_configured": bool(s.notify_webhook_url),
            "webhook_host": urlparse(s.notify_webhook_url).hostname if s.notify_webhook_url else None,
        },
    }
