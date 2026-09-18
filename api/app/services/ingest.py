"""Persist a parsed SBOM as sboms + components and emit an audit event."""
from __future__ import annotations

import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, Product, Sbom
from app.services import audit
from app.services.sbom import parse_sbom

log = logging.getLogger("frist24.ingest")


def ingest_sbom(db: Session, product: Product, raw: bytes, filename: str | None, actor: str) -> tuple[Sbom, bool]:
    """Returns (sbom, created). Re-uploading a byte-identical SBOM for the same product is a no-op."""
    sha = hashlib.sha256(raw).hexdigest()
    existing = db.execute(select(Sbom).where(Sbom.product_id == product.id, Sbom.sha256 == sha)).scalar_one_or_none()
    if existing:
        return existing, False

    parsed = parse_sbom(raw)
    sbom = Sbom(
        product_id=product.id,
        format=parsed.format,
        spec_version=parsed.spec_version,
        filename=filename,
        sha256=sha,
        component_count=len(parsed.components),
    )
    db.add(sbom)
    db.flush()
    db.add_all(
        Component(
            sbom_id=sbom.id,
            product_id=product.id,
            name=c.name[:300],
            version=(c.version or None) and c.version[:100],
            purl=(c.purl or None) and c.purl[:600],
            ecosystem=c.ecosystem,
            cpe=(c.cpe or None) and c.cpe[:300],
            supplier=(c.supplier or None) and c.supplier[:300],
        )
        for c in parsed.components
    )
    with_purl = sum(1 for c in parsed.components if c.purl)
    audit.append(
        db,
        actor,
        "sbom.ingested",
        "sbom",
        sbom.id,
        {
            "product_id": str(product.id),
            "sku": product.sku,
            "format": parsed.format,
            "spec_version": parsed.spec_version,
            "filename": filename,
            "sha256": sha,
            "component_count": len(parsed.components),
            "components_with_purl": with_purl,
        },
    )
    log.info("ingested %s for %s: %d components (%d with purl)", filename, product.sku, len(parsed.components), with_purl)
    return sbom, True
