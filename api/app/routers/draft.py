from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.incidents import _get, report_out
from app.routers.products import actor_from_header
from app.schemas.reports import ReportOut
from app.services import drafting, llm

router = APIRouter(prefix="/draft", tags=["drafting"])


@router.post("/{stage}", response_model=ReportOut, status_code=201, summary="Draft a report with the local LLM (falls back to template)")
def draft_stage(
    stage: str,
    incident_id: uuid.UUID = Query(...),
    language: str = Query(default="en", pattern="^(en|de)$"),
    db: Session = Depends(get_db),
    actor: str = Depends(actor_from_header),
):
    if stage not in ("early_warning", "notification", "final_report"):
        from fastapi import HTTPException

        raise HTTPException(400, "stage must be early_warning | notification | final_report")
    inc = _get(db, incident_id)
    rep = drafting.draft(db, inc, stage, language, actor)
    db.commit()
    db.refresh(rep)
    return report_out(rep)


@router.get("/status", summary="Is the local model ready?")
def status() -> dict:
    try:
        models = llm.available_models()
        try:
            chosen = llm.pick_model()
        except llm.LlmUnavailable as e:
            return {"ready": False, "models": models, "reason": str(e)}
        return {"ready": True, "models": models, "model": chosen}
    except llm.LlmUnavailable as e:
        return {"ready": False, "models": [], "reason": str(e)}
