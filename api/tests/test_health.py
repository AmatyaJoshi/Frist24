from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    with TestClient(app) as c:
        r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "frist24-api"
    assert "db" in body and "ollama" in body
