"""Unit tests for the demo API. Run with: pytest -q"""
from app.main import app


def _client():
    return app.test_client()


def test_index_returns_ok():
    response = _client().get("/")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["service"] == "utiso-cicd-demo"


def test_healthz_returns_healthy():
    response = _client().get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"
