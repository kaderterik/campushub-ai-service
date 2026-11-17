from dataclasses import dataclass
from typing import Protocol
from typing import Literal


Category = Literal["TECHNOLOGY", "SPORT", "ART", "CAREER", "SOCIAL", "OTHER"]


@dataclass(frozen=True)
class ClassificationResult:
    category: Category
    confidence: float


class Classifier(Protocol):
    def load(self) -> None:
        ...

    def is_ready(self) -> bool:
        ...

    def classify(self, text: str) -> list[ClassificationResult]:
        ...
