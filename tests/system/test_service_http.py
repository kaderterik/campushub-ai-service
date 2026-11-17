"""T18: Çalışan servise gerçek HTTP istekleriyle sistem testleri.

Servis ayrı bir uvicorn süreci olarak FakeClassifier ile başlatılır; testler
Grup 3'ün Event Service'i gibi dışarıdan istek atar.
"""

from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

VALID_CATEGORIES = {"TECHNOLOGY", "SPORT", "ART", "CAREER", "SOCIAL", "OTHER"}


def assert_contract(body: dict) -> None:
    """docs/ai-classify-contract.md kurallarını doğrular."""
    predictions = body["predictions"]
    assert isinstance(predictions, list)
    assert 1 <= len(predictions) <= 5
    categories = [item["category"] for item in predictions]
    assert set(categories) <= VALID_CATEGORIES
    assert len(categories) == len(set(categories))
    if "OTHER" in categories:
        assert categories == ["OTHER"]
    for item in predictions:
        assert set(item) == {"category", "confidence"}
        assert 0.0 <= item["confidence"] <= 1.0


def test_health_over_http(running_service):
    response = httpx.get(f"{running_service}/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"service": "ai-service", "status": "UP", "version": "1.0.0"}


def test_classify_over_http_follows_contract(running_service):
    response = httpx.post(
        f"{running_service}/ai/classify",
        json={"text": "Yazılım stajı başvuruları başladı"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert_contract(response.json())


def test_classify_accepts_turkish_unicode_and_long_text(running_service):
    text = "Çağdaş şiir, müzik ve görsel sanatlar şenliği. " * 200

    response = httpx.post(f"{running_service}/ai/classify", json={"text": text})

    assert response.status_code == 200
    assert_contract(response.json())


@pytest.mark.parametrize(
    "payload",
    [{"text": ""}, {"text": "   "}, {}, {"text": 123}, {"text": None}, {"metin": "yanlış alan"}],
)
def test_invalid_requests_return_400_over_http(running_service, payload):
    response = httpx.post(f"{running_service}/ai/classify", json=payload)

    assert response.status_code == 400
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_malformed_json_returns_400_over_http(running_service):
    response = httpx.post(
        f"{running_service}/ai/classify",
        content='{"text":',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_wrong_method_and_unknown_path(running_service):
    assert httpx.get(f"{running_service}/ai/classify").status_code == 405
    assert httpx.get(f"{running_service}/bilinmeyen").status_code == 404


def test_concurrent_requests(running_service):
    def call(index: int) -> httpx.Response:
        return httpx.post(
            f"{running_service}/ai/classify",
            json={"text": f"Etkinlik {index}: kampüste hackathon"},
            timeout=10,
        )

    with ThreadPoolExecutor(max_workers=10) as pool:
        responses = list(pool.map(call, range(30)))

    assert all(response.status_code == 200 for response in responses)
    for response in responses:
        assert_contract(response.json())


def test_openapi_and_docs_are_served(running_service):
    schema = httpx.get(f"{running_service}/openapi.json").json()

    assert "/ai/classify" in schema["paths"]
    assert "/health" in schema["paths"]
    assert httpx.get(f"{running_service}/docs").status_code == 200
