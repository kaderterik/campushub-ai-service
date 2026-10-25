"""CampusHub K1: CPU-only mDeBERTa zero-shot multi-label classifier.

This module matches the finalized 337/84 evaluation policy:
- pinned HF model revision
- identical candidate-label descriptions and hypothesis template
- multi_label=True
- retain all five topical labels with score >= 0.70
- return OTHER only when no topical label passes the threshold

The caller must call load() once during app startup; importing the module does
not download or initialize the model.
"""

from __future__ import annotations

from typing import Any

from app.contracts import ClassificationResult
from app.exceptions import ModelUnavailableError

MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
MODEL_REVISION = "8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c"
THRESHOLD = 0.70
HYPOTHESIS_TEMPLATE = "Bu metin {} ile ilgilidir."

# Order and wording are identical to the final model-evaluation scripts.
CATEGORY_DESCRIPTIONS = {
    "TECHNOLOGY": "teknoloji ve yazılım",
    "SPORT": "spor",
    "ART": "sanat, müzik ve kültür",
    "CAREER": "kariyer ve iş hayatı",
    "SOCIAL": "sosyal buluşma ve gönüllülük",
    "OTHER": "üniversite idari işlemleri, genel bilgilendirme ve öğrenci duyuruları",
}
TOPICAL_CATEGORIES = tuple(c for c in CATEGORY_DESCRIPTIONS if c != "OTHER")
LABEL_TO_CATEGORY = {description: category for category, description in CATEGORY_DESCRIPTIONS.items()}


class MDeBERTaClassifier:
    """Real classifier implementing the K2 multi-category contract.

    Call load() in the application startup/lifespan. Classification before
    successful loading raises ModelUnavailableError (handled as HTTP 503).
    """

    def __init__(self) -> None:
        self._pipeline: Any | None = None

    def load(self) -> None:
        """Initialize pinned model on CPU once."""
        if self.is_ready():
            return
        try:
            from transformers import pipeline
            loaded = pipeline(
                "zero-shot-classification",
                model=MODEL_ID,
                revision=MODEL_REVISION,
                device=-1,
            )
        except Exception as exc:
            raise ModelUnavailableError("mDeBERTa model could not be loaded") from exc
        self._pipeline = loaded

    def is_ready(self) -> bool:
        return self._pipeline is not None

    def classify(self, text: str) -> list[ClassificationResult]:
        if not self.is_ready():
            raise ModelUnavailableError("mDeBERTa model is not loaded")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        try:
            result = self._pipeline(
                text,
                candidate_labels=list(CATEGORY_DESCRIPTIONS.values()),
                hypothesis_template=HYPOTHESIS_TEMPLATE,
                multi_label=True,
            )
            scores = {
                LABEL_TO_CATEGORY[label]: float(score)
                for label, score in zip(result["labels"], result["scores"])
            }
            if set(scores) != set(CATEGORY_DESCRIPTIONS):
                raise ValueError("Model did not return all six category scores")
        except ModelUnavailableError:
            raise
        except Exception as exc:
            raise ModelUnavailableError("mDeBERTa inference failed") from exc

        selected = [
            ClassificationResult(category=category, confidence=scores[category])
            for category in TOPICAL_CATEGORIES
            if scores[category] >= THRESHOLD
        ]
        if selected:
            return sorted(selected, key=lambda item: item.confidence, reverse=True)

        # OTHER is a decision-rule fallback, not a calibrated probability.
        # Return the model's actual OTHER score rather than invent a confidence.
        return [ClassificationResult(category="OTHER", confidence=scores["OTHER"])]
