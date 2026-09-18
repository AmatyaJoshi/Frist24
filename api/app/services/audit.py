"""Append-only, hash-chained audit log.

    hash_n = sha256( prev_hash || canonical_json({ts, actor, action, entity_type, entity_id, payload}) )

- prev_hash of the first row is GENESIS (64 zeros).
- Writers serialise on a transaction-level advisory lock so the chain never forks.
- Rows can never be updated or deleted: a DB trigger (alembic 0001) raises on UPDATE/DELETE.
- `verify(db)` recomputes every hash and reports the first break, if any.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import AuditLog

GENESIS = "0" * 64
_LOCK_KEY = 0x24F0_1524  # arbitrary, project-wide


def _canonical(ts: datetime, actor: str, action: str, entity_type: str, entity_id: str | None, payload: dict) -> str:
    body = {
        "ts": ts.astimezone(UTC).isoformat(timespec="microseconds"),
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def compute_hash(prev_hash: str, ts: datetime, actor: str, action: str, entity_type: str, entity_id: str | None, payload: dict) -> str:
    return hashlib.sha256((prev_hash + _canonical(ts, actor, action, entity_type, entity_id, payload)).encode("utf-8")).hexdigest()


def append(db: Session, actor: str, action: str, entity_type: str, entity_id: Any = None, payload: dict | None = None) -> AuditLog:
    """Append one row inside the caller's transaction. Caller commits."""
    payload = payload or {}
    db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _LOCK_KEY})
    last = db.execute(select(AuditLog.hash).order_by(AuditLog.id.desc()).limit(1)).scalar_one_or_none()
    prev = last or GENESIS
    ts = datetime.now(UTC)
    eid = str(entity_id) if entity_id is not None else None
    row = AuditLog(
        ts=ts,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=eid,
        payload=payload,
        prev_hash=prev,
        hash=compute_hash(prev, ts, actor, action, entity_type, eid, payload),
    )
    db.add(row)
    db.flush()
    return row


def verify(db: Session) -> dict:
    """Walk the whole chain. Returns {ok, rows, first_bad_id, reason}."""
    prev = GENESIS
    rows = 0
    for r in db.execute(select(AuditLog).order_by(AuditLog.id.asc())).scalars():
        rows += 1
        if r.prev_hash != prev:
            return {"ok": False, "rows": rows, "first_bad_id": r.id, "reason": "prev_hash does not match previous row"}
        expected = compute_hash(r.prev_hash, r.ts, r.actor, r.action, r.entity_type, r.entity_id, r.payload)
        if expected != r.hash:
            return {"ok": False, "rows": rows, "first_bad_id": r.id, "reason": "hash does not match row content"}
        prev = r.hash
    return {"ok": True, "rows": rows, "first_bad_id": None, "reason": None, "head": prev}
