"""Local dev without Docker: start an embedded Postgres 16 (pgserver) and print DATABASE_URL.

    pip install pgserver          (or: uv pip install -e "api[dev]")
    python scripts/dev_pg.py      # keeps running; Ctrl+C stops the server
"""
import pathlib
import sys
import time

import pgserver

data = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".pgdata").resolve()
data.mkdir(parents=True, exist_ok=True)
srv = pgserver.get_server(data)
uri = srv.get_uri()
try:
    srv.psql("CREATE DATABASE frist24;")
except Exception:  # noqa: BLE001  (already exists)
    pass
print("DATABASE_URL=" + uri.replace("postgresql://", "postgresql+psycopg://").rsplit("/", 1)[0] + "/frist24", flush=True)
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    pass
