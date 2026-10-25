
"""Gerçek sınıflandırıcı için model indirmeden çalışan testler."""

import sys
import types

import pytest

from app.exceptions import ModelUnavailableError
from app.models.classifier import (
    CATEGORY_DESCRIPTIONS,
    HYPOTHESIS_TEMPLATE,
    MODEL_ID,
    MODEL_REVISION,
    MDeBERTaClassifier,
)


@pytest.fixture
def fake_hf(monkeypatch):
    state = {
        "loads": [],
        "calls": [],
        "scores": {
            label: 0.1
            for label in CATEGORY_DESCRIPTIONS.values()
        },
    }

    fake_transformers = types.ModuleType("transformers")

    def fake_pipeline(task, **kwargs):
        state["loads"].append((task, kwargs))

        def inference(
            text, *, candidate_labels,
            hypothesis_template, multi_label
        ):
            state["calls"].append(
                (text, candidate_labels, hypothesis_template, multi_label)
            )
            return {
                "labels": list(candidate_labels),
                "scores": [
                    state["scores"][label]
                    for label in candidate_labels
                ],
            }

        return inference

    fake_transformers.pipeline = fake_pipeline
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    return state


def test_load_once_on_cpu_with_pinned_revision(fake_hf):
    classifier = MDeBERTaClassifier()

    assert not classifier.is_ready()

    classifier.load()
    classifier.load()

    assert classifier.is_ready()
    assert fake_hf["loads"] == [
        (
            "zero-shot-classification",
            {
                "model": MODEL_ID,
                "revision": MODEL_REVISION,
                "device": -1,
            },
        )
    ]


def test_multiple_predictions_above_threshold(fake_hf):
    classifier = MDeBERTaClassifier()
    classifier.load()

    fake_hf["scores"].update({
        CATEGORY_DESCRIPTIONS["TECHNOLOGY"]: 0.93,
        CATEGORY_DESCRIPTIONS["CAREER"]: 0.70,
        CATEGORY_DESCRIPTIONS["ART"]: 0.69,
        CATEGORY_DESCRIPTIONS["OTHER"]: 0.99,
    })

    results = classifier.classify("Yazılım kariyer etkinliği")

    assert [
        (item.category, item.confidence)
        for item in results
    ] == [
        ("TECHNOLOGY", 0.93),
        ("CAREER", 0.70),
    ]

    assert fake_hf["calls"] == [
        (
            "Yazılım kariyer etkinliği",
            list(CATEGORY_DESCRIPTIONS.values()),
            HYPOTHESIS_TEMPLATE,
            True,
        )
    ]


def test_other_only_when_no_topical_category_passes(fake_hf):
    classifier = MDeBERTaClassifier()
    classifier.load()

    fake_hf["scores"][
        CATEGORY_DESCRIPTIONS["TECHNOLOGY"]
    ] = 0.69

    fake_hf["scores"][
        CATEGORY_DESCRIPTIONS["OTHER"]
    ] = 0.42

    results = classifier.classify("Öğrenci işleri duyurusu")

    assert len(results) == 1
    assert results[0].category == "OTHER"
    assert results[0].confidence == 0.42


def test_classification_requires_model_loading():
    classifier = MDeBERTaClassifier()

    with pytest.raises(ModelUnavailableError):
        classifier.classify("Yazılım etkinliği")
