from app.contracts import ClassificationResult


class FakeClassifier:
    def __init__(self) -> None:
        self._ready = False

    def load(self) -> None:
        self._ready = True

    def is_ready(self) -> bool:
        return self._ready

    def classify(self, text: str) -> ClassificationResult:
        return ClassificationResult(
            category="TECHNOLOGY",
            confidence=0.91,
        )
