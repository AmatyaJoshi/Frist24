import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models import AuditLog
from app.services import audit


def test_append_chains_hashes_and_verifies(db):
    a = audit.append(db, "tester", "test.one", "test", "1", {"x": 1})
    b = audit.append(db, "tester", "test.two", "test", "2", {"y": [1, 2]})
    db.commit()
    assert b.prev_hash == a.hash
    assert len(a.hash) == 64
    res = audit.verify(db)
    assert res["ok"] is True and res["rows"] >= 2


def test_update_on_audit_log_is_rejected(db):
    row = audit.append(db, "tester", "test.immutable", "test", "3", {})
    db.commit()
    with pytest.raises(DBAPIError) as ei:
        db.execute(text("UPDATE audit_log SET actor = 'evil' WHERE id = :id"), {"id": row.id})
        db.commit()
    assert "append-only" in str(ei.value)
    db.rollback()


def test_delete_on_audit_log_is_rejected(db):
    row = audit.append(db, "tester", "test.immutable", "test", "4", {})
    db.commit()
    with pytest.raises(DBAPIError):
        db.execute(text("DELETE FROM audit_log WHERE id = :id"), {"id": row.id})
        db.commit()
    db.rollback()
    assert db.get(AuditLog, row.id) is not None
