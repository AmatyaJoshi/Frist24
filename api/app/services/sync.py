"""Full feed sync = KEV -> OSV match -> EPSS -> KEV flags -> deterministic incident rule.

Called by POST /sync, by the APScheduler job, and by `make demo`.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import session_factory
from app.models import FeedSync, KevEntry
from app.services import audit, feeds, incidents, matching

log = logging.getLogger("frist24.sync")
_lock = threading.Lock()


def _step(db: Session, feed: str, fn) -> dict:
    fs = FeedSync(feed=feed, status="running", started_at=datetime.now(UTC))
    db.add(fs)
    db.flush()
    t = time.perf_counter()
    try:
        result = fn() or {}
        fs.status = "ok"
        fs.items = int(result.get("total") or result.get("stored") or result.get("matches_created") or result.get("opened") or 0)
        fs.message = ", ".join(f"{k}={v}" for k, v in result.items() if k != "new_cves")[:2000]
    except Exception as e:  # noqa: BLE001
        fs.status = "error"
        fs.message = f"{type(e).__name__}: {e}"[:2000]
        log.exception("sync step %s failed", feed)
        result = {"error": fs.message}
    fs.finished_at = datetime.now(UTC)
    result["seconds"] = round(time.perf_counter() - t, 1)
    db.flush()
    return result


def run_full_sync(actor: str = "system:scheduler") -> dict:
    if not _lock.acquire(blocking=False):
        return {"skipped": "sync already running"}
    try:
        with session_factory()() as db:
            summary: dict = {"started_at": datetime.now(UTC).isoformat()}
            summary["kev"] = _step(db, "kev", lambda: feeds.load_kev(db))
            db.commit()
            summary["osv"] = _step(db, "osv", lambda: matching.match_by_purl(db))
            db.commit()
            keep = set(db.execute(select(KevEntry.cve_id)).scalars()) | matching.matched_cves(db)
            summary["epss"] = _step(db, "epss", lambda: feeds.load_epss(db, keep))
            db.commit()
            # EPSS was loaded after matching: copy scores onto matches and refresh KEV flags.
            kev_matches = matching.refresh_kev_flags(db)
            summary["kev_matches"] = kev_matches
            opened = _step(db, "incidents", lambda: {"opened": len(incidents.open_incidents(db, actor))})
            summary["incidents"] = opened
            audit.append(
                db,
                actor,
                "feed.synced",
                "system",
                None,
                {k: v for k, v in summary.items() if k in ("kev", "osv", "epss", "incidents", "kev_matches")},
            )
            db.commit()
            summary["finished_at"] = datetime.now(UTC).isoformat()
            log.info("full sync done: %s", summary)
            return summary
    finally:
        _lock.release()


def last_runs(db: Session, limit: int = 12) -> list[FeedSync]:
    return db.execute(select(FeedSync).order_by(FeedSync.id.desc()).limit(limit)).scalars().all()
