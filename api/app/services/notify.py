"""Outbound alerts when incidents open. Optional: set NOTIFY_WEBHOOK_URL.

Sends one JSON POST per sync run (not per incident) so a burst of KEV additions does not page
forty times. Payload contains only what the reviewer needs to act: product, CVE, deadlines and a
link. No SBOM contents, no component lists. The webhook host is the single exception to the
egress allow-list and must be configured explicitly by the operator.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

from app.config import get_settings

log = logging.getLogger("frist24.notify")


def build_payload(incidents: list[dict], base_url: str) -> dict:
    return {
        "source": "frist24",
        "event": "incidents.opened",
        "sent_at": datetime.now(UTC).isoformat(),
        "count": len(incidents),
        "text": _summary_text(incidents),
        "incidents": [{**i, "url": f"{base_url.rstrip('/')}/incidents/{i['id']}"} for i in incidents],
    }


def _summary_text(incidents: list[dict]) -> str:
    lines = [f"Frist24: {len(incidents)} new CRA Art. 14 incident(s) — early warning due in 24h"]
    for i in incidents[:10]:
        lines.append(f"• {i['sku']} × {i['cve_id']} ({i.get('vulnerability_name') or 'KEV'}) — early warning by {i['deadline_early_warning']}")
    if len(incidents) > 10:
        lines.append(f"… and {len(incidents) - 10} more")
    return "\n".join(lines)


def send_incident_alert(incidents: list[dict]) -> dict | None:
    """Returns delivery metadata, or None when no webhook is configured or nothing to send."""
    s = get_settings()
    if not s.notify_webhook_url or not incidents:
        return None
    payload = build_payload(incidents, s.public_web_url)
    host = urlparse(s.notify_webhook_url).hostname
    try:
        r = httpx.post(s.notify_webhook_url, json=payload, timeout=10)
        ok = r.status_code < 300
        log.info("webhook %s -> %s (%d incidents)", host, r.status_code, len(incidents))
        return {"host": host, "status_code": r.status_code, "ok": ok, "count": len(incidents)}
    except httpx.HTTPError as e:
        log.warning("webhook %s failed: %s", host, e)
        return {"host": host, "status_code": None, "ok": False, "error": f"{type(e).__name__}: {e}"[:300], "count": len(incidents)}
