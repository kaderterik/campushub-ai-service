import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.health_routes import create_health_router
from app.main import app
from app.services.fake_classifier import FakeClassifier


@pytest.fixture
def client():
    # Context manager lifespan'i tetikler, böylece model startup'ta yüklenir.
    with TestClient(app) as test_client:
        yield test_client


def test_health_returns_200(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_health_response_schema(client):
    response = client.get("/health")
    body = response.json()

    assert set(body.keys()) == {"service", "status", "version"}
    assert all(isinstance(value, str) for value in body.values())


def test_health_response_values(client):
    response = client.get("/health")

    assert response.json() == {
        "service": "ai-service",
        "status": "UP",
        "version": "1.0.0",
    }


def test_health_returns_503_when_model_not_ready(client, monkeypatch):
    monkeypatch.setattr("app.main.classifier.is_ready", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "service": "ai-service",
        "status": "DOWN",
        "error": "MODEL_STARTING",
        "version": "1.0.0",
    }


def test_health_returns_503_before_startup():
    # Lifespan çalışmadan (startup tamamlanmadan) model hazır değildir.
    fresh_app = FastAPI()
    fresh_app.include_router(create_health_router(FakeClassifier()))

    response = TestClient(fresh_app).get("/health")

    assert response.status_code == 503
    assert response.json()["error"] == "MODEL_STARTING"
