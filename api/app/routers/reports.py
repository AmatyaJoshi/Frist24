from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Report
from app.routers.incidents import report_out
from app.routers.products import actor_from_header
from app.schemas.reports import ReportEdit, ReportOut, ReviewDecision
from app.services import reports

router = APIRouter(prefix="/reports", tags=["reports"])


def _get(db: Session, report_id: uuid.UUID) -> Report:
    rep = db.execute(select(Report).options(selectinload(Report.incident)).where(Report.id == report_id)).scalar_one_or_none()
    if not rep:
        raise HTTPException(404, "report not found")
    return rep


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    return report_out(_get(db, report_id))


@router.patch("/{report_id}", response_model=ReportOut, summary="Edit TEXT fields of a pending_review report")
def edit(report_id: uuid.UUID, body: ReportEdit, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)):
    rep = reports.edit_report(db, _get(db, report_id), body.content, actor, body.note)
    db.commit()
    db.refresh(rep)
    return report_out(rep)


@router.post("/{report_id}/approve", response_model=ReportOut)
def approve(report_id: uuid.UUID, body: ReviewDecision | None = None, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)):
    rep = reports.approve_report(db, _get(db, report_id), actor, body.note if body else None)
    db.commit()
    db.refresh(rep)
    return report_out(rep)


@router.post("/{report_id}/reject", response_model=ReportOut)
def reject(report_id: uuid.UUID, body: ReviewDecision | None = None, db: Session = Depends(get_db), actor: str = Depends(actor_from_header)):
    rep = reports.reject_report(db, _get(db, report_id), actor, body.note if body else None)
    db.commit()
    db.refresh(rep)
    return report_out(rep)
