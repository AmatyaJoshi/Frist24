from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.products import actor_from_header
from app.services import sync

router = APIRouter(prefix="/sync", tags=["sync"])


class FeedSyncOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    feed: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    items: int | None
    message: str | None


@router.post("", summary="Run a full feed sync now (KEV -> OSV -> EPSS -> incident rule)")
def run_sync(actor: str = Depends(actor_from_header)) -> dict:
    return sync.run_full_sync(actor=f"{actor} (manual sync)")


@router.get("/status", response_model=list[FeedSyncOut])
def sync_status(db: Session = Depends(get_db)):
    return sync.last_runs(db)
