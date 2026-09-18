"""Live-network test: real KEV, OSV and EPSS. Set FRIST24_OFFLINE=1 to skip."""
import os

import pytest
from sqlalchemy import select

from app.models import EpssScore, Incident, KevEntry, Product
from app.services.demo import ingest_fixtures
from app.services.sync import run_full_sync

pytestmark = pytest.mark.skipif(os.environ.get("FRIST24_OFFLINE") == "1", reason="offline")


def test_full_sync_opens_real_kev_incident(db_url, db):
    from app.cli import seed

    seed()
    ingest_fixtures()
    summary = run_full_sync(actor="pytest")
    assert "error" not in summary["kev"], summary["kev"]
    assert summary["kev"]["total"] > 1000
    assert "error" not in summary["osv"], summary["osv"]

    hmi = db.execute(select(Product).where(Product.sku == "HMI-4100")).scalar_one()
    egw = db.execute(select(Product).where(Product.sku == "EGW-7200")).scalar_one()
    incs = db.execute(select(Incident)).scalars().all()
    pairs = {(i.product_id, i.cve_id) for i in incs}
    assert (hmi.id, "CVE-2020-11023") in pairs, [(i.cve_id) for i in incs]
    assert (egw.id, "CVE-2022-22965") in pairs

    inc = next(i for i in incs if i.cve_id == "CVE-2020-11023" and i.product_id == hmi.id)
    assert (inc.deadline_early_warning - inc.aware_at).total_seconds() == 24 * 3600
    assert (inc.deadline_notification - inc.aware_at).total_seconds() == 72 * 3600
    assert db.get(KevEntry, "CVE-2020-11023") is not None
    assert db.get(EpssScore, "CVE-2020-11023") is not None  # EPSS stored for KEV CVEs

    # idempotent: a second sync opens nothing new
    again = run_full_sync(actor="pytest")
    assert again["incidents"]["opened"] == 0
