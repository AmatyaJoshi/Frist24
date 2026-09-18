import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import AuditLog, Component
from app.services.sbom import SbomParseError, parse_sbom

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "sboms"
EXPECTED = {"hmi-web-ui.cdx.json": 883, "edge-gateway.cdx.json": 903}


@pytest.mark.parametrize("fname,count", EXPECTED.items())
def test_parse_cyclonedx_fixtures(fname, count):
    parsed = parse_sbom((FIX / fname).read_bytes())
    assert parsed.format == "cyclonedx"
    assert parsed.spec_version == "1.2"
    assert len(parsed.components) == count
    assert all(c.purl for c in parsed.components)
    assert {c.ecosystem for c in parsed.components} <= {"npm", "maven"}


def test_parse_spdx_sample():
    parsed = parse_sbom((FIX / "spdx-sample.spdx.json").read_bytes())
    assert parsed.format == "spdx"
    assert parsed.spec_version == "2.3"
    purls = {c.purl for c in parsed.components}
    assert "pkg:npm/jquery@3.4.1" in purls
    assert len(parsed.components) == 3


def test_parse_rejects_garbage():
    with pytest.raises(SbomParseError):
        parse_sbom(b"not json")
    with pytest.raises(SbomParseError):
        parse_sbom(json.dumps({"hello": "world"}).encode())


def test_upload_endpoint_ingests_and_audits(db_url, db):
    from app.main import app

    with TestClient(app) as c:
        r = c.post("/products", json={"sku": "TEST-SKU-1", "name": "Test product"}, headers={"X-Actor": "pytest"})
        if r.status_code == 409:
            pid = next(p["id"] for p in c.get("/products").json() if p["sku"] == "TEST-SKU-1")
        else:
            assert r.status_code == 201, r.text
            pid = r.json()["id"]
        raw = (FIX / "hmi-web-ui.cdx.json").read_bytes()
        r = c.post(f"/products/{pid}/sbom", files={"file": ("hmi-web-ui.cdx.json", io.BytesIO(raw), "application/json")}, headers={"X-Actor": "pytest"})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["sbom"]["component_count"] == 883
        # idempotent re-upload
        r2 = c.post(f"/products/{pid}/sbom", files={"file": ("again.json", io.BytesIO(raw), "application/json")})
        assert r2.status_code == 201 and r2.json()["created"] is False
        comps = c.get(f"/products/{pid}/components", params={"q": "jquery@3.4.1"}).json()
        assert any(x["purl"] == "pkg:npm/jquery@3.4.1" for x in comps)

    n = db.execute(select(func.count()).select_from(Component).where(Component.product_id == pid)).scalar()
    assert n == 883
    ev = db.execute(select(AuditLog).where(AuditLog.action == "sbom.ingested").order_by(AuditLog.id.desc())).scalars().first()
    assert ev is not None and ev.payload["component_count"] == 883
