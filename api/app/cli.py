"""Frist24 CLI:  python -m app.cli <command>

  migrate   run alembic upgrade head
  seed      insert the two demo products (idempotent) + audit event
  demo      seed + upload fixture SBOMs + sync feeds + open incidents  (steps 4-5 fill this in)
  reset     drop demo data (products cascade; keeps feeds and the audit log)
"""
from __future__ import annotations

import logging
import subprocess
import sys
from datetime import date

from sqlalchemy import select

from app.db import session_factory
from app.models import Product
from app.services import audit

log = logging.getLogger("frist24.cli")

DEMO_PRODUCTS = [
    {
        "sku": "HMI-4100",
        "name": "HMI-4100 Operator Panel",
        "description": "10-inch operator panel for machine control; embedded web UI served to service laptops. Shipped 2021, discontinued 2023, still in the field.",
        "lifecycle_status": "discontinued",
        "placed_on_market_at": date(2021, 3, 15),
    },
    {
        "sku": "EGW-7200",
        "name": "EGW-7200 Edge Gateway",
        "description": "Industrial edge gateway (Java runtime) bridging fieldbus data to the plant network; includes an embedded identity service.",
        "lifecycle_status": "active",
        "placed_on_market_at": date(2022, 9, 1),
    },
]


def migrate() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)


def seed(actor: str = "system:seed") -> list[Product]:
    with session_factory()() as db:
        out = []
        for spec in DEMO_PRODUCTS:
            p = db.execute(select(Product).where(Product.sku == spec["sku"])).scalar_one_or_none()
            if p is None:
                p = Product(**spec)
                db.add(p)
                db.flush()
                audit.append(db, actor, "product.created", "product", p.id, {"sku": p.sku, "name": p.name})
                log.info("seeded product %s", p.sku)
            out.append(p)
        db.commit()
        return out


def reset(actor: str = "system:reset") -> None:
    with session_factory()() as db:
        n = 0
        for p in db.execute(select(Product)).scalars().all():
            db.delete(p)
            n += 1
        audit.append(db, actor, "demo.reset", "system", None, {"products_deleted": n})
        db.commit()
        log.info("deleted %d products (cascade)", n)


def demo() -> None:
    seed()
    # steps 4-5 add: ingest fixture SBOMs, sync feeds, open incidents
    try:
        from app.services.demo import run_demo  # type: ignore

        run_demo()
    except ImportError:
        log.warning("demo pipeline not implemented yet (build step 5)")


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "migrate":
        migrate()
    elif cmd == "seed":
        seed()
    elif cmd == "reset":
        reset()
    elif cmd == "demo":
        migrate()
        demo()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
