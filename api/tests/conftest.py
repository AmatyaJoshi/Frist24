"""Test DB: uses DATABASE_URL (compose: db:5432). Locally, set DATABASE_URL to any Postgres 16,
e.g. the pgserver instance started by scripts/dev_pg.py. Schema is created via alembic upgrade head."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("DATABASE_URL")


@pytest.fixture(scope="session")
def db_url() -> str:
    if not DB_URL:
        pytest.skip("DATABASE_URL not set; DB tests skipped")
    eng = create_engine(DB_URL, connect_args={"connect_timeout": 3})
    try:
        with eng.connect() as c:
            c.execute(text("select 1"))
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"database not reachable: {e}")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, cwd=os.path.dirname(os.path.dirname(__file__)))
    return DB_URL


@pytest.fixture()
def db(db_url):
    from app.db import session_factory

    s = session_factory()()
    try:
        yield s
    finally:
        s.rollback()
        s.close()
