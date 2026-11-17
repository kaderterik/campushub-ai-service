from app.contracts import Classifier
from app.schemas.classification import CategoryPrediction, ClassificationResponse


class InferenceService:
    def __init__(self, classifier: Classifier) -> None:
        self.classifier = classifier

    def classify(self, text: str) -> ClassificationResponse:
        results = self.classifier.classify(text)

        return ClassificationResponse(
            predictions=[
                CategoryPrediction(category=result.category, confidence=result.confidence)
                for result in results
            ],
        )
