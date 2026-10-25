from app.contracts import ClassificationResult


class FakeClassifier:
    def classify(self, text: str) -> list[ClassificationResult]:
        return [
            ClassificationResult(category="TECHNOLOGY", confidence=0.91),
            ClassificationResult(category="CAREER", confidence=0.84),
        ]
