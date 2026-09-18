"""APScheduler job: full feed sync every SYNC_INTERVAL_MINUTES (default 15). Disabled when SYNC_ENABLED=false."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings

log = logging.getLogger("frist24.scheduler")
_scheduler: BackgroundScheduler | None = None


def start() -> BackgroundScheduler | None:
    global _scheduler
    s = get_settings()
    if not s.sync_enabled:
        log.info("scheduler disabled (SYNC_ENABLED=false)")
        return None
    from app.services.sync import run_full_sync

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(run_full_sync, "interval", minutes=s.sync_interval_minutes, id="full_sync", coalesce=True, max_instances=1)
    _scheduler.start()
    log.info("scheduler started: full sync every %d min", s.sync_interval_minutes)
    return _scheduler


def stop() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
