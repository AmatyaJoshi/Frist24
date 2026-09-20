"""Webhook alerting: payload shape and delivery bookkeeping, without network."""
import httpx

from app.config import get_settings
from app.services import notify

INC = [
    {"id": "abc", "sku": "HMI-4100", "cve_id": "CVE-2020-11023", "vulnerability_name": "JQuery XSS", "deadline_early_warning": "2026-09-19T02:07:15+00:00"},
]


def test_payload_has_link_and_summary():
    p = notify.build_payload(INC, "http://localhost:3000/")
    assert p["event"] == "incidents.opened" and p["count"] == 1
    assert p["incidents"][0]["url"] == "http://localhost:3000/incidents/abc"
    assert "HMI-4100 × CVE-2020-11023" in p["text"]
    assert "components" not in p["incidents"][0]  # never leaks SBOM content


def test_no_webhook_means_no_send(monkeypatch):
    monkeypatch.setattr(get_settings(), "notify_webhook_url", None)
    assert notify.send_incident_alert(INC) is None


def test_send_records_status(monkeypatch):
    monkeypatch.setattr(get_settings(), "notify_webhook_url", "https://hooks.example.test/abc")
    seen = {}

    def fake_post(url, json, timeout):
        seen["url"], seen["json"] = url, json
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    r = notify.send_incident_alert(INC)
    assert r == {"host": "hooks.example.test", "status_code": 200, "ok": True, "count": 1}
    assert seen["json"]["count"] == 1


def test_send_failure_is_reported_not_raised(monkeypatch):
    monkeypatch.setattr(get_settings(), "notify_webhook_url", "https://hooks.example.test/abc")

    def boom(url, json, timeout):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", boom)
    r = notify.send_incident_alert(INC)
    assert r["ok"] is False and "ConnectError" in r["error"]
