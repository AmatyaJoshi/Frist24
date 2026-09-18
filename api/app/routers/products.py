from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Component, Incident, Product
from app.schemas.products import ComponentOut, ProductCreate, ProductOut, SbomUploadResult
from app.services import audit
from app.services.ingest import ingest_sbom
from app.services.sbom import SbomParseError

router = APIRouter(prefix="/products", tags=["products"])

MAX_SBOM_BYTES = 25 * 1024 * 1024


def actor_from_header(x_actor: str | None = Header(default=None, alias="X-Actor")) -> str:
    """Single 'reviewer' role for the prototype; the header just names who clicked."""
    return (x_actor or "reviewer").strip()[:120]


def _counts(db: Session, product_ids: list[uuid.UUID]) -> tuple[dict, dict]:
    if not product_ids:
        return {}, {}
    comp = dict(
        db.execute(select(Component.product_id, func.count()).where(Component.product_id.in_(product_ids)).group_by(Component.product_id)).all()
    )
    inc = dict(
        db.execute(
            select(Incident.product_id, func.count())
            .where(Incident.product_id.in_(product_ids), Incident.status != "closed")
            .group_by(Incident.product_id)
        ).all()
    )
    return comp, inc


def _to_out(p: Product, comp: dict, inc: dict) -> ProductOut:
    out = ProductOut.model_validate(p)
    out.component_count = comp.get(p.id, 0)
    out.open_incidents = inc.get(p.id, 0)
    return out


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    products = db.execute(select(Product).options(selectinload(Product.sboms)).order_by(Product.sku)).scalars().all()
    comp, inc = _counts(db, [p.id for p in products])
    return [_to_out(p, comp, inc) for p in products]


@router.post("", response_model=ProductOut, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)):
    if db.execute(select(Product).where(Product.sku == body.sku)).scalar_one_or_none():
        raise HTTPException(409, f"SKU {body.sku} already exists")
    p = Product(**body.model_dump())
    db.add(p)
    db.flush()
    audit.append(db, actor, "product.created", "product", p.id, {"sku": p.sku, "name": p.name})
    db.commit()
    db.refresh(p)
    return _to_out(p, {}, {})


def _get_product(db: Session, product_id: uuid.UUID) -> Product:
    p = db.execute(select(Product).options(selectinload(Product.sboms)).where(Product.id == product_id)).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "product not found")
    return p


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    p = _get_product(db, product_id)
    comp, inc = _counts(db, [p.id])
    return _to_out(p, comp, inc)


@router.post("/{product_id}/sbom", response_model=SbomUploadResult, status_code=201)
async def upload_sbom(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: str = Depends(actor_from_header),
):
    p = _get_product(db, product_id)
    raw = await file.read()
    if len(raw) > MAX_SBOM_BYTES:
        raise HTTPException(413, "SBOM larger than 25 MB")
    try:
        sbom, created = ingest_sbom(db, p, raw, file.filename, actor)
    except SbomParseError as e:
        raise HTTPException(422, str(e)) from e
    db.commit()
    db.refresh(sbom)
    msg = f"{sbom.component_count} components ingested" if created else "identical SBOM already on file; nothing changed"
    return SbomUploadResult(sbom=sbom, created=created, message=msg)


@router.get("/{product_id}/components", response_model=list[ComponentOut])
def list_components(
    product_id: uuid.UUID,
    q: str | None = Query(default=None, description="substring filter on name or purl"),
    limit: int = Query(default=200, le=2000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    _get_product(db, product_id)
    stmt = select(Component).where(Component.product_id == product_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Component.name.ilike(like) | Component.purl.ilike(like))
    stmt = stmt.order_by(Component.name, Component.version).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()
