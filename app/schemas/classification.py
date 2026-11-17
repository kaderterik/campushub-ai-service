from pydantic import BaseModel, Field, StrictStr, field_validator, model_validator

from app.contracts import Category


class ClassificationRequest(BaseModel):
    text: StrictStr

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("text must be a non-empty string")

        return value


class CategoryPrediction(BaseModel):
    category: Category
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)


class ClassificationResponse(BaseModel):
    predictions: list[CategoryPrediction] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_predictions(self) -> "ClassificationResponse":
        categories = [prediction.category for prediction in self.predictions]
        if len(categories) != len(set(categories)):
            raise ValueError("Each category must appear only once")
        if "OTHER" in categories and len(categories) != 1:
            raise ValueError("OTHER must be returned on its own")
        return self

class ErrorResponse(BaseModel):
    error: str
    message: str
