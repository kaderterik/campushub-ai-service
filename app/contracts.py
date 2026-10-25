from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    confidence: float


class Classifier(Protocol):
    def load(self) -> None:
        ...

    def is_ready(self) -> bool:
        ...

    def classify(self, text: str) -> ClassificationResult:
        ...
