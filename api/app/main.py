import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import OUTBOUND_ALLOWLIST, get_settings
from app import scheduler
from app.routers import audit, draft, incidents, products, reports, settings, sync

log = logging.getLogger("frist24")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    log.info("outbound allow-list: %s + ollama (%s)", ", ".join(OUTBOUND_ALLOWLIST), s.ollama_url)
    log.info("manufacturer: %s <%s>", s.frist24_manufacturer_name, s.frist24_manufacturer_contact)
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(
    title="Frist24 API",
    version="0.2.0",
    description="CRA Article 14 reporting assistant. Deterministic KEV rule opens incidents; a local LLM only drafts.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(sync.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(audit.router)
app.include_router(draft.router)
app.include_router(settings.router)


def _db_status() -> str:
    """Uses the shared engine/pool (no per-call engine creation)."""
    try:
        from app.db import get_engine

        with get_engine().connect() as c:
            c.execute(text("select 1"))
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"error: {type(e).__name__}"


_ollama_cache: dict = {"at": 0.0, "value": None}


async def _ollama_status() -> dict:
    """Cached for 10 s: Ollama answers /api/tags slowly while a draft is generating, and the
    overview page calls /health on every load."""
    import time

    now = time.monotonic()
    if _ollama_cache["value"] is not None and now - _ollama_cache["at"] < 10:
        return _ollama_cache["value"]
    s = get_settings()
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            r = await client.get(f"{s.ollama_url}/api/tags")
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            value = {"status": "ok", "models": models, "target": s.ollama_model}
    except Exception as e:  # noqa: BLE001
        value = {"status": f"error: {type(e).__name__}", "models": [], "target": s.ollama_model}
    _ollama_cache.update(at=now, value=value)
    return value


@app.get("/health", tags=["meta"])
async def health():
    """Liveness for compose. Always 200 when the API process is up; dependencies are reported, not enforced."""
    return {
        "status": "ok",
        "service": "frist24-api",
        "version": app.version,
        "db": _db_status(),
        "ollama": await _ollama_status(),
    }
