from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.classify_routes import create_classify_router
from app.models.classifier import (
    CATEGORY_DESCRIPTIONS,
    MDeBERTaClassifier,
)
from app.services.inference_service import InferenceService


def test_real_classifier_service_api_flow(monkeypatch):
    classifier = MDeBERTaClassifier()
    received = []

    def fake_pipeline(text, **kwargs):
        received.append((text, kwargs))

        scores = {
            "TECHNOLOGY": 0.95,
            "SPORT": 0.10,
            "ART": 0.15,
            "CAREER": 0.88,
            "SOCIAL": 0.20,
            "OTHER": 0.30,
        }

        return {
            "labels": list(CATEGORY_DESCRIPTIONS.values()),
            "scores": [
                scores[category]
                for category in CATEGORY_DESCRIPTIONS
            ],
        }

    # Yalnızca ağır model pipeline'ını taklit ediyoruz.
    monkeypatch.setattr(classifier, "_pipeline", fake_pipeline)

    service = InferenceService(classifier)
    test_app = FastAPI()
    test_app.include_router(create_classify_router(service))

    with TestClient(test_app) as client:
        response = client.post(
            "/ai/classify",
            json={"text": "  Yazılım stajı başvuruları başladı.  "},
        )

    assert response.status_code == 200
    assert response.json() == {
        "predictions": [
            {"category": "TECHNOLOGY", "confidence": 0.95},
            {"category": "CAREER", "confidence": 0.88},
        ]
    }

    assert len(received) == 1
    assert received[0][0] == "Yazılım stajı başvuruları başladı."
    assert received[0][1]["multi_label"] is True

def test_real_backend_loads_once_at_startup(monkeypatch):
    import importlib

    main_module = importlib.import_module("app.main")

    class StubClassifier:
        def __init__(self):
            self.load_count = 0

        def load(self):
            self.load_count += 1

    classifier = StubClassifier()

    monkeypatch.setattr(main_module, "MDeBERTaClassifier", StubClassifier)
    monkeypatch.setattr(main_module, "classifier", classifier)

    assert classifier.load_count == 0

    with TestClient(main_module.app):
        assert classifier.load_count == 1

    assert classifier.load_count == 1