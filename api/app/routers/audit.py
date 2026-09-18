from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog
from app.schemas.incidents import TimelineEvent
from app.services import audit

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=dict, summary="Audit log, newest first")
def list_audit(
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    entity_type: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog)
    cnt = select(func.count()).select_from(AuditLog)
    if entity_type:
        stmt, cnt = stmt.where(AuditLog.entity_type == entity_type), cnt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt, cnt = stmt.where(AuditLog.entity_id == entity_id), cnt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt, cnt = stmt.where(AuditLog.action.like(f"{action}%")), cnt.where(AuditLog.action.like(f"{action}%"))
    rows = db.execute(stmt.order_by(AuditLog.id.desc()).limit(limit).offset(offset)).scalars().all()
    total = db.execute(cnt).scalar() or 0
    items = [TimelineEvent(id=r.id, ts=r.ts, actor=r.actor, action=r.action, entity_type=r.entity_type, entity_id=r.entity_id, payload=r.payload, hash=r.hash, prev_hash=r.prev_hash) for r in rows]
    return {"total": total, "items": [i.model_dump() for i in items]}


@router.get("/verify", summary="Recompute the whole hash chain")
def verify(db: Session = Depends(get_db)) -> dict:
    return audit.verify(db)
