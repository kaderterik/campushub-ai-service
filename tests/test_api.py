import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_classify_success():
    response = client.post(
        "/ai/classify",
        json={"text": "Python atölyesi"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "predictions": [
            {"category": "TECHNOLOGY", "confidence": 0.91},
            {"category": "CAREER", "confidence": 0.84},
        ],
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"text": ""},
        {"text": "   "},
        {},
        {"text": 123},
        {"text": None},
    ],
)
def test_classify_invalid_input(payload):
    response = client.post("/ai/classify", json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert isinstance(body["message"], str)
    assert body["message"]


def test_classify_invalid_json():
    response = client.post(
        "/ai/classify",
        content='{"text":',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "VALIDATION_ERROR"

def test_model_unavailable(monkeypatch):
    from app.exceptions import ModelUnavailableError

    def unavailable(text):
        raise ModelUnavailableError("Model could not be loaded")

    monkeypatch.setattr(
        "app.main.classifier.classify",
        unavailable,
    )

    response = client.post(
        "/ai/classify",
        json={"text": "Python atölyesi"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": "MODEL_UNAVAILABLE",
        "message": "AI model is not ready",
    }


def test_unexpected_error(monkeypatch):
    def unexpected(text):
        raise RuntimeError("Private technical error details")

    monkeypatch.setattr(
        "app.main.classifier.classify",
        unexpected,
    )

    with TestClient(app, raise_server_exceptions=False) as error_client:
        response = error_client.post(
            "/ai/classify",
            json={"text": "Python atölyesi"},
        )

    assert response.status_code == 500
    assert response.json() == {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
    }

def test_openapi_error_responses():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    responses = response.json()["paths"]["/ai/classify"]["post"]["responses"]

    assert "422" not in responses

    for status in ("400", "503", "500"):
        assert responses[status]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponse"
        }


@pytest.mark.parametrize("category", ["TECHNOLOGY", "SPORT", "ART", "CAREER", "SOCIAL", "OTHER"])
def test_single_prediction_uses_same_list_contract(monkeypatch, category):
    from app.contracts import ClassificationResult

    monkeypatch.setattr(
        "app.main.classifier.classify",
        lambda text: [ClassificationResult(category=category, confidence=0.72)],
    )
    response = client.post("/ai/classify", json={"text": "Örnek etkinlik"})
    assert response.status_code == 200
    assert response.json() == {
        "predictions": [{"category": category, "confidence": 0.72}]
    }


@pytest.mark.parametrize(
    "values",
    [
        [],
        [("TECHNOLOGY", 0.9), ("TECHNOLOGY", 0.8)],
        [("OTHER", 0.9), ("CAREER", 0.8)],
        [("ANNOUNCEMENT", 0.9)],
        [("SPORT", -0.1)],
        [("ART", 1.1)],
        [("ART", float("nan"))],
        [("ART", float("inf"))],
    ],
)
def test_invalid_classifier_output_is_server_error(monkeypatch, values):
    from app.contracts import ClassificationResult

    monkeypatch.setattr(
        "app.main.classifier.classify",
        lambda text: [ClassificationResult(category=label, confidence=score) for label, score in values],
    )
    with TestClient(app, raise_server_exceptions=False) as error_client:
        response = error_client.post("/ai/classify", json={"text": "Örnek etkinlik"})
    assert response.status_code == 500
    assert response.json() == {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
    }


def test_scores_are_preserved_and_input_is_trimmed(monkeypatch):
    from app.contracts import ClassificationResult

    received = []

    def classify(text):
        received.append(text)
        return [
            ClassificationResult(category="ART", confidence=0.91),
            ClassificationResult(category="TECHNOLOGY", confidence=0.84),
        ]

    monkeypatch.setattr("app.main.classifier.classify", classify)
    response = client.post("/ai/classify", json={"text": "  Dijital müzik üretimi  "})
    assert received == ["Dijital müzik üretimi"]
    assert response.json()["predictions"] == [
        {"category": "ART", "confidence": 0.91},
        {"category": "TECHNOLOGY", "confidence": 0.84},
    ]


def test_openapi_documents_multi_category_response():
    schema = client.get("/openapi.json").json()
    response = schema["components"]["schemas"]["ClassificationResponse"]
    assert "category" not in response["properties"]
    predictions = response["properties"]["predictions"]
    assert predictions["type"] == "array"
    assert predictions["minItems"] == 1
    assert predictions["items"]["$ref"] == "#/components/schemas/CategoryPrediction"
