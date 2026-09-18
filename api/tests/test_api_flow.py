"""End-to-end API flow on whatever incidents exist (created by test_sync_live or make demo)."""
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(db_url):
    from app.main import app

    with TestClient(app) as c:
        yield c


def _ensure_incidents(client):
    incs = client.get("/incidents").json()
    if incs:
        return incs
    if os.environ.get("FRIST24_OFFLINE") == "1":
        pytest.skip("no incidents and offline")
    from app.cli import seed
    from app.services.demo import ingest_fixtures

    seed()
    ingest_fixtures()
    client.post("/sync", headers={"X-Actor": "pytest"})
    return client.get("/incidents").json()


def test_incident_list_is_deadline_sorted(client):
    incs = _ensure_incidents(client)
    assert incs, "no incidents"
    nd = [i["next_deadline"] for i in incs if i["next_deadline"]]
    assert nd == sorted(nd)
    first = incs[0]
    for k in ("sku", "cve_id", "aware_at", "deadline_early_warning", "deadline_notification", "component_count"):
        assert k in first


def test_detail_template_edit_approve_audit(client):
    incs = _ensure_incidents(client)
    inc = next((i for i in incs if i["cve_id"] == "CVE-2020-11023" and i["sku"] == "HMI-4100"), incs[0])
    d = client.get(f"/incidents/{inc['id']}").json()
    assert d["kev"]["cve_id"] == inc["cve_id"]
    assert d["components"], "incident must list matched components"
    assert d["facts"]["actively_exploited"] is True
    assert d["facts"]["vulnerability_id"] == inc["cve_id"]
    assert any(e["action"] == "incident.opened" for e in d["timeline"])

    # template draft (no LLM) in EN and DE
    ew = client.post(f"/incidents/{inc['id']}/reports/template", params={"stage": "early_warning", "language": "en"}, headers={"X-Actor": "pytest"})
    assert ew.status_code == 201, ew.text
    ew = ew.json()
    assert ew["status"] == "pending_review" and ew["source"] == "template"
    assert ew["content"]["report_type"] == "early_warning"
    assert set(ew["fact_fields"]) <= set(ew["content"])
    de = client.post(f"/incidents/{inc['id']}/reports/template", params={"stage": "early_warning", "language": "de"}).json()
    for k in ew["fact_fields"]:
        assert de["content"][k] == ew["content"][k], f"FACT {k} must be identical across languages"
    assert "wird untersucht" in de["content"]["initial_assessment"] or "untersucht" in de["content"]["initial_assessment"]

    # FACT edit rejected, TEXT edit accepted
    r = client.patch(f"/reports/{ew['id']}", json={"content": {"vulnerability_id": "CVE-1999-0001"}})
    assert r.status_code == 422
    r = client.patch(f"/reports/{ew['id']}", json={"content": {"member_states_affected": "Germany, Austria, Italy"}, "note": "confirmed markets"}, headers={"X-Actor": "pytest"})
    assert r.status_code == 200, r.text
    assert r.json()["content"]["member_states_affected"] == "Germany, Austria, Italy"

    # approve -> incident status advances, audit rows exist, chain verifies
    r = client.post(f"/reports/{ew['id']}/approve", json={"note": "ok"}, headers={"X-Actor": "pytest"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"
    d2 = client.get(f"/incidents/{inc['id']}").json()
    assert d2["status"] in ("early_warning_approved", "notification_approved", "final_approved")
    actions = [e["action"] for e in d2["timeline"]]
    assert "report.drafted" in actions and "report.edited" in actions and "report.approved" in actions
    # second approve is a 409, edit after approval is a 409
    assert client.post(f"/reports/{ew['id']}/approve").status_code == 409
    assert client.patch(f"/reports/{ew['id']}", json={"content": {"initial_assessment": "x"}}).status_code == 409

    # notification template references the approved early warning
    n = client.post(f"/incidents/{inc['id']}/reports/template", params={"stage": "notification", "language": "en"}).json()
    assert n["content"]["reference_to_early_warning"] and ew["id"] in n["content"]["reference_to_early_warning"]
    assert n["content"]["epss_score"]

    v = client.get("/audit/verify").json()
    assert v["ok"] is True and v["rows"] > 0
    a = client.get("/audit", params={"limit": 5}).json()
    assert a["total"] >= v["rows"] - 1 and len(a["items"]) <= 5
    assert client.get("/sync/status").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_package_zip_contains_json_and_pdf(client):
    incs = _ensure_incidents(client)
    inc = next((i for i in incs if i["reports_approved"] > 0), incs[0])
    r = client.get(f"/incidents/{inc['id']}/package")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    import io
    import zipfile

    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert "manifest.json" in names and "facts.json" in names and "audit_trail.json" in names
    pdfs = [n for n in names if n.endswith(".pdf")]
    jsons = [n for n in names if n.startswith("reports/") and n.endswith(".json")]
    assert pdfs and jsons
    assert z.read(pdfs[0])[:4] == b"%PDF"
    import json

    m = json.loads(z.read("manifest.json"))
    assert m["incident"]["cve_id"] == inc["cve_id"]
