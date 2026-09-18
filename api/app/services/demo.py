"""`make demo` pipeline. Step 4: ingest fixture SBOMs. Step 5 adds feed sync + incident opening."""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select

from app.config import get_settings
from app.db import session_factory
from app.models import Product

log = logging.getLogger("frist24.demo")

FIXTURE_SBOMS = {"HMI-4100": "hmi-web-ui.cdx.json", "EGW-7200": "edge-gateway.cdx.json"}


def fixtures_dir() -> Path:
    configured = Path(get_settings().fixtures_dir)
    if configured.exists():
        return configured
    here = Path(__file__).resolve().parents[3] / "fixtures"  # repo checkout: <repo>/api/app/services -> <repo>/fixtures
    if here.exists():
        return here
    raise FileNotFoundError(f"fixtures dir not found: tried {configured} and {here}")


def ingest_fixtures(actor: str = "system:demo") -> int:
    from app.services.ingest import ingest_sbom

    n = 0
    with session_factory()() as db:
        for sku, fname in FIXTURE_SBOMS.items():
            p = db.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()
            if not p:
                log.warning("product %s not seeded; skipping", sku)
                continue
            path = fixtures_dir() / "sboms" / fname
            sbom, created = ingest_sbom(db, p, path.read_bytes(), fname, actor)
            db.commit()
            log.info("%s <- %s: %d components (%s)", sku, fname, sbom.component_count, "new" if created else "already present")
            n += 1
    return n


def run_demo() -> None:
    ingest_fixtures()
    try:
        from app.services.sync import run_full_sync  # step 5
    except ImportError:
        log.warning("feed sync not implemented yet (build step 5)")
        return
    run_full_sync(actor="system:demo")
